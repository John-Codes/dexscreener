import os
from dotenv import load_dotenv
from google import genai
import requests
import json
from dotmap import DotMap

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

def get_latest_boosted_tokens(count = 1):
    response = requests.get(
        "https://api.dexscreener.com/token-boosts/latest/v1",
        headers={},
    )
    data = response.json()
    
    if isinstance(data, list) and data:
        # Assuming the array contains objects with the required information
        tokens_info = []
        for item in data:
            token_data = DotMap(item)
            tokens_info.append({
                'address': token_data.get('tokenAddress'),
                'chainId': token_data.get('chainId'),
                'url': token_data.get('url'),
                'description': token_data.get('description'),
                'links': token_data.get('links')
            })

        return tokens_info
    else:
        return []

def fetch_dexscreener_token_pair_data(pairId, chainId):
    url = f"https://api.dexscreener.com/latest/dex/pairs/{chainId}/{pairId}"
    response = requests.get(url, headers={})
    data = response.json()
    return data

def llm(prompt,data):
        prompt+=data
        llm_response = client.models.generate_content(model='gemini-pro', contents=prompt)
        return llm_response.text.strip()


def add_trading_data(tokens):
    for token in tokens:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{token['address']}"
        response = requests.get(url)
        data = response.json()
        if data and data['pairs']:
            pair = DotMap(data['pairs'][0])
            token['baseToken'] = pair.baseToken
            token['quoteToken'] = pair.quoteToken
            token['priceNative'] = pair.priceNative
            token['priceUsd'] = pair.priceUsd
            token['txns'] = pair.txns
            token['volume'] = pair.volume
            token['priceChange'] = pair.priceChange
            token['fdv'] = pair.fdv
            token['marketCap'] = pair.marketCap
            token['pairCreatedAt'] = pair.pairCreatedAt
            token['info'] = pair.info
            token['boosts'] = pair.boosts
        else:
            token['baseToken'] = None
            token['quoteToken'] = None
            token['priceNative'] = None
            token['priceUsd'] = None
            token['txns'] = None
            token['volume'] = None
            token['priceChange'] = None
            token['fdv'] = None
            token['marketCap'] = None
            token['pairCreatedAt'] = None
            token['info'] = None
            token['boosts'] = None
    return tokens

def filter_by_volume_and_txns(tokens):
    def get_volume_h24(token):
        return token.get('volume', {}).get('h24', 0)

    def get_txns_h24_total(token):
        return token.get('txns', {}).get('h24', {}).get('total', 0)

    if not tokens:
        return []

    # Sort tokens by volume and transaction count in descending order
    sorted_tokens = sorted(tokens, key=lambda x: (get_volume_h24(x), get_txns_h24_total(x)), reverse=True)

    return sorted_tokens[:3]



            

    return csv_output

def save_token_pairs_to_csv(csv_data):
    # Create tokens directory if it doesn't exist
    if not os.path.exists("tokens"):
        os.makedirs("tokens")

    # Save the CSV data to a file
    with open("tokens/top_3_boosted_tokens.csv", "w") as f:
        f.write(csv_data)
    print(f"Token pairs data saved to tokens/token_pairs.csv")



boosted_tokens_data = get_latest_boosted_tokens(count=1)
boosted_tokens_with_data = add_trading_data(boosted_tokens_data)
top_active_tokens = filter_by_volume_and_txns(boosted_tokens_with_data)




#convert top active tokens to json format
top_active_tokens_json = json.dumps(top_active_tokens, indent=4)



top_tokens_csv_Format=llm("From the following JSON data structures, extract the key names in to columns and the definitions as rows and return them as a single line of raw very precise CSV ",top_active_tokens_json)


csv_data = save_token_pairs_to_csv(top_tokens_csv_Format)







print("Boosted tokens with trading data:")
print(json.dumps(boosted_tokens_with_data, indent=4))

print("\nTop 3 tokens with the highest 24h volume and transaction count:")
print(json.dumps(top_active_tokens, indent=4))
