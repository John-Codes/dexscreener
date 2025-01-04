import requests
import json
import os
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


# Solana RPC endpoint

# Token mint address (base58-encoded string)
#Get rpc url from .env file
RPC_URL = os.getenv("RPC_URL")


TOKEN_MINT_ADDRESS = "2gnGkpQfM7mQjkY7VjQqD6bEa84tA5EqqYHr5ccNpump"

def fetch_token_mint_info(token_mint_address):
    """Fetch token mint information."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getAccountInfo",
        "params": [token_mint_address, {"encoding": "jsonParsed"}]
    }
    response = requests.post(RPC_URL, json=payload)
    if response.status_code == 200:
        result = response.json()
        print("Raw API Response (Mint Info):")
        print(json.dumps(result, indent=2))
        if result is None:
            return {}
        result_data = result.get("result")
        if result_data is None:
            return {}
        value_data = result_data.get("value")
        if value_data is None:
            return {}
        mint_info = value_data.get("data", {}).get("parsed", {}).get("info", {})
        return mint_info
    else:
        print(f"Error fetching token mint info: {response.status_code}, {response.text}")
        return None

def fetch_token_accounts(token_mint_address):
    """Fetch all token accounts for a token mint."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getProgramAccounts",
        "params": [
            "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",  # SPL Token program ID
            {
                "encoding": "jsonParsed",
                "filters": [
                    {"dataSize": 165},  # Token account size
                    {"memcmp": {"offset": 0, "bytes": token_mint_address}}  # Filter by mint address
                ]
            }
        ]
    }
    response = requests.post(RPC_URL, json=payload)
    if response.status_code == 200:
        result = response.json()
        print("Raw API Response (Token Accounts):")
        # print(json.dumps(result, indent=2))
        token_accounts = result.get("result", [])
        return token_accounts
    else:
        print(f"Error fetching token accounts: {response.status_code}, {response.text}")
        return None

def fetch_transaction_history(token_mint_address):
    """Fetch transaction history for a token mint."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [
            token_mint_address,
            {
                "limit": 10  # Fetch the last 10 transactions
            }
        ]
    }
    response = requests.post(RPC_URL, json=payload)
    if response.status_code == 200:
        result = response.json()
        transactions = result.get("result", [])
        return transactions
    else:
        print(f"Error fetching transaction history: {response.status_code}, {response.text}")
        return None

def analyze_holder_distribution(token_accounts):
    """Analyze the distribution of token holders."""
    # Extract balances
    holders = []
    for account in token_accounts:
        info = account.get("account", {}).get("data", {}).get("parsed", {}).get("info", {})
        token_amount = info.get("tokenAmount", {})
        amount = int(token_amount.get("amount", 0))  # Extract amount from tokenAmount
        if amount > 0:  # Only include accounts with a balance
            holders.append({
                "address": account.get("pubkey"),
                "owner": info.get("owner"),
                "amount": amount
            })

    # Calculate total supply from holders
    total_supply = sum(holder["amount"] for holder in holders)

    # Sort holders by balance (descending)
    top_holders = sorted(holders, key=lambda x: x["amount"], reverse=True)[:10]

    # Calculate percentage held by top holders
    if total_supply > 0:
        top_holder_percentage = sum(holder["amount"] for holder in top_holders) / total_supply * 100
    else:
        top_holder_percentage = 0

    return total_supply, top_holders, top_holder_percentage

def main():
    # Fetch token mint info
    mint_info = fetch_token_mint_info(TOKEN_MINT_ADDRESS)
    if not mint_info:
        return

    print("Token Mint Info:")
    print(json.dumps(mint_info, indent=2))

    # Check if mint and freeze authorities are disabled
    mint_authority = mint_info.get("mintAuthority")
    freeze_authority = mint_info.get("freezeAuthority")
    print(f"Mint Authority Disabled: {mint_authority is None}")
    print(f"Freeze Authority Disabled: {freeze_authority is None}")

    # Fetch token accounts
    token_accounts = fetch_token_accounts(TOKEN_MINT_ADDRESS)
    if not token_accounts:
        return

    # Analyze holder distribution
    total_supply, top_holders, top_holder_percentage = analyze_holder_distribution(token_accounts)
    print(f"Total Supply: {total_supply}")
    print(f"Top 10 Holders: {top_holder_percentage:.2f}%")
    print("Top Holders:")
    for holder in top_holders:
        print(f"  Address: {holder['address']}, Owner: {holder['owner']}, Amount: {holder['amount']}")

    # Fetch transaction history
    # transactions = fetch_transaction_history(TOKEN_MINT_ADDRESS)
    # if transactions:
    #     print("Transaction History:")
    #     for tx in transactions:
    #         print(f"  Signature: {tx['signature']}, Block Time: {tx['blockTime']}")
    # else:
    #     print("No transaction history found.")

if __name__ == "__main__":
    main()