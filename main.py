import datetime
import requests

# Set global variables
MINUTES = 5
LIMIT = 10
DEBUG = True
WOW_SYMBOLS = ["ETH", "WETH"]
WOW_PRICE = 0.2

# Determine when to query from
occured_after = int((datetime.datetime.now() - datetime.timedelta(minutes=MINUTES)).timestamp())
page = 1
offset = 0
return_size = 10

# Keep trying until the return size from the API is less than the limit
while return_size == LIMIT:
    print("Fetching page %i" % page)

    # Build the url
    url = "https://api.opensea.io/api/v1/events?collection_slug=senties&event_type=successful&only_opensea=false&offset=%i&limit=%i&occurred_after=%i" % (
        offset,
        LIMIT,
        occured_after
    )
    if DEBUG:
        print(url)

    # Get the JSON
    try:
        r = requests.get(url)
        data = r.json()
    except Exception as e:
        print("Failed to run! %s" % str(e))
    
    # Extract events and filter for creator sales
    try:
        events = [e for e in data["asset_events"] if DEBUG or e["seller"]["user"]["username"] != "Senties"]
    except Exception as e:
        print ("Error parsing events! %s" % str(e))

    # Set the return size so we know when to break the loop
    return_size = len(events)
    offset += return_size
    print("%i sale(s) found" % return_size)

    # Loop through each event 
    for event in events:
        try:
            # Build name determining if it is a bundle or not
            if event["asset_bundle"] is None:
                name = event["asset"]["name"]
            else:
                name = "Senties %s" % ", ".join([asset["name"].split(" ")[-1] for asset in event["asset_bundle"]["assets"]])

            # Determine how much to divide the price by
            denominator = 1
            for i in range(event["payment_token"]["decimals"]):
                denominator *= 10

            # Convert the total price to an integer
            total_price = int(event["total_price"])

            # Convert the spot price to a float
            spot_price = float(event["payment_token"]["usd_price"])

            # Find the prices in the token and usd
            price_token = total_price / denominator
            price_usd = price_token * spot_price

            # Build the title
            title = "New sale!"
            symbol = event["payment_token"]["symbol"]
            if symbol in WOW_SYMBOLS and price_token >= WOW_PRICE:
                title = "WOW! " + title

            seller = event["seller"]["user"]["username"] if event["seller"]["user"]["username"] is not None else "n/a"
            buyer = event["winner_account"]["user"]["username"] if event["winner_account"]["user"]["username"] is not None else "n/a"

            # Build the description and extract etherscan and thumbnail urls
            description = "%s -- SOLD BY %s for %.4f %s (~$%.2f) to %s" % (
                name,
                seller,
                price_token,
                symbol,
                price_usd,
                buyer,
            )
            etherscan_url = "https://etherscan.io/tx/%s" % event["transaction"]["transaction_hash"]
            try:
                thumbnail_url = event["asset"]["image_preview_url"]
            except:
                thumbnail_url = None

        except Exception as e:
            print("Error parsing single event... %s" % str(e))
            continue
        
        if DEBUG:
            print(description)
            print(etherscan_url)
            print(thumbnail_url)
            print("-----")

    if DEBUG:
        print ('\n')