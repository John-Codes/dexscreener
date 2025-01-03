import os
from dotenv import load_dotenv
from google import genai
import requests
import json
import csv
from solana_token_risk_checker import get_token_risk

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

def get_latest_boosted_tokens(count = 1):
    response = requests.get(
        "https://api.dexscreener.com/token-boosts/latest/v1",
        headers={},
    )
    data = response.json()
    # Filter the data to get the required number of tokens
    filtered_data = data[:count]
    return filtered_data

def fetch_dexscreener_token_pair_data(pairId, chainId):
    url = f"https://api.dexscreener.com/latest/dex/pairs/{chainId}/{pairId}"
    response = requests.get(url, headers={})
    data = response.json()
    return data

def fetch_dexscreener_token_data(token_address):
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
    response = requests.get(url, headers={})
    data = response.json()
    if data.get("pairs"):
        pair_info = data["pairs"][0]
        json_data = json.dumps(pair_info)
        prompt = f"From the following JSON data, extract the key names in to columns and the definitions as rows and return them as a single line of raw CSV: {json_data}"
        llm_response = client.models.generate_content(model='gemini-pro', contents=prompt)
        return llm_response.text.strip()
    else:
        return None

def get_token_pairs_csv(boosted_tokens_data):
    csv_output = ""
    for token in boosted_tokens_data:
        chain_id = token['chainId']
        token_address = token['tokenAddress']
        token_pair_data = fetch_dexscreener_token_pair_data(token_address, chain_id)
        if token_pair_data == {'schemaVersion': '1.0.0', 'pairs': None, 'pair': None}:
            print("no pairs found")
            token_data_csv = fetch_dexscreener_token_data(token_address)
            if token_data_csv:
                security_info = get_token_risk(token_address)
                prompt = f"Convert the following security token information into a CSV format: {security_info}"
                security_info = client.models.generate_content(model='gemini-pro', contents=prompt)
                csv_output += f"{token_data_csv},{security_info.text.strip()}\n"
            else:

                continue

            


    return csv_output

def save_token_pairs_to_csv(csv_data):
    # Create tokens directory if it doesn't exist
    if not os.path.exists("tokens"):
        os.makedirs("tokens")

    # Save the CSV data to a file
    with open("tokens/token_pairs.csv", "w") as f:
        f.write(csv_data)
    print(f"Token pairs data saved to tokens/token_pairs.csv")

def save_boosted_tokens_to_csv(boosted_tokens_data):
    # Create tokens directory if it doesn't exist
    if not os.path.exists("tokens"):
        os.makedirs("tokens")

    # Save the JSON data to a file
    with open("tokens/boosted_tokens.json", "w") as f:
        json.dump(boosted_tokens_data, f, indent=4)
    print(f"Boosted tokens data saved to tokens/boosted_tokens.json")

boosted_tokens_data = get_latest_boosted_tokens(count=1)
save_boosted_tokens_to_csv(boosted_tokens_data)

token_pairs_csv = get_token_pairs_csv(boosted_tokens_data)
save_token_pairs_to_csv(token_pairs_csv)
