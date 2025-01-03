from solana.rpc.api import Client
from solana.publickey import PublicKey

# Connect to Solana mainnet
client = Client("https://api.mainnet-beta.solana.com")

def get_token_metadata(token_address):
    """Fetch metadata for a Solana token."""
    token_pubkey = PublicKey(token_address)
    account_info = client.get_account_info(token_pubkey)
    return account_info

def get_token_holders(token_address):
    """Fetch holders of a Solana token."""
    token_pubkey = PublicKey(token_address)
    token_accounts = client.get_token_accounts_by_owner(token_pubkey, program_id=PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"))
    return token_accounts

def analyze_holder_distribution(holders):
    """Analyze the distribution of token holders."""
    total_supply = sum(int(holder['account']['data']['parsed']['info']['tokenAmount']['amount']) for holder in holders['result']['value'])
    top_holders = sorted(holders['result']['value'], key=lambda x: int(x['account']['data']['parsed']['info']['tokenAmount']['amount']), reverse=True)[:10]
    top_holder_percentage = sum(int(holder['account']['data']['parsed']['info']['tokenAmount']['amount']) for holder in top_holders) / total_supply * 100
    return top_holder_percentage

def check_mint_and_freeze_authority(token_address):
    """Check if the token has a mint authority and freeze authority."""
    token_pubkey = PublicKey(token_address)
    token_info = client.get_account_info(token_pubkey)
    mint_authority = token_info['result']['value']['data']['parsed']['info'].get('mintAuthority')
    freeze_authority = token_info['result']['value']['data']['parsed']['info'].get('freezeAuthority')
    return mint_authority, freeze_authority

def find_lp_address(token_address):
    """Find the LP address for a token."""
    # Raydium LP accounts are associated with the token address
    # This is a simplified example; you may need to query Raydium's API or use a DEX SDK for accuracy
    token_pubkey = PublicKey(token_address)
    lp_accounts = client.get_token_largest_accounts(token_pubkey)
    for account in lp_accounts['result']['value']:
        if account['owner'] == PublicKey("Raydium LP Program Address"):  # Replace with actual Raydium LP program ID
            return account['address']
    return None

def get_lp_info(lp_address):
    """Fetch liquidity pool (LP) information."""
    lp_pubkey = PublicKey(lp_address)
    lp_info = client.get_account_info(lp_pubkey)
    return lp_info

def check_lp_burned(lp_address):
    """Check if LP tokens are burned."""
    if lp_address is None:
        return "No LP address found. Token might not have a liquidity pool or might be traded on a different DEX."
    lp_info = get_lp_info(lp_address)
    lp_supply = int(lp_info['result']['value']['data']['parsed']['info']['supply'])
    return lp_supply == 0

def get_pooled_tokens(lp_address):
    """Fetch the amount of tokens and SOL pooled in the liquidity pool."""
    if lp_address is None:
        return "No LP address found. Token might not have a liquidity pool or might be traded on a different DEX.", ""
    lp_info = get_lp_info(lp_address)
    pooled_tokens = int(lp_info['result']['value']['data']['parsed']['info']['tokenAmount']['amount'])
    pooled_sol = int(lp_info['result']['value']['data']['parsed']['info']['solAmount']['amount'])
    return pooled_tokens, pooled_sol

def is_open_trading(lp_address):
    """Check if the token is open for trading."""
    if lp_address is None:
        return "No LP address found. Token might not have a liquidity pool or might be traded on a different DEX."
    lp_info = get_lp_info(lp_address)
    return lp_info['result']['value']['data']['parsed']['info']['state'] == "initialized"

def get_token_risk(token_address):
    """
    Analyze the risk of a Solana token.
    
    Args:
        token_address (str): The token's contract address.
    
    Returns:
        dict: A dictionary containing the token's risk analysis.
    """
    risk_report = {}

    # Check mint and freeze authority
    mint_authority, freeze_authority = check_mint_and_freeze_authority(token_address)
    risk_report["mint_authority_disabled"] = mint_authority is None
    risk_report["freeze_authority_disabled"] = freeze_authority is None

    # Analyze holder distribution
    holders = get_token_holders(token_address)
    risk_report["top_10_holders_percentage"] = analyze_holder_distribution(holders)

    # Find and analyze LP
    lp_address = find_lp_address(token_address)
    risk_report["lp_address"] = lp_address if lp_address else "No LP address found. Token might not have a liquidity pool or might be traded on a different DEX."
    risk_report["lp_burned"] = check_lp_burned(lp_address)
    risk_report["pooled_tokens"], risk_report["pooled_sol"] = get_pooled_tokens(lp_address)
    risk_report["open_trading"] = is_open_trading(lp_address)

    return risk_report

if __name__ == "__main__":
    # Replace with your token address
    token_address = "YOUR_TOKEN_ADDRESS_HERE"

    # Get token risk analysis
    risk_report = get_token_risk(token_address)

    # Print results
    print("Token Risk Analysis:")
    print(f"Mint Authority Disabled: {risk_report['mint_authority_disabled']}")
    print(f"Freeze Authority Disabled: {risk_report['freeze_authority_disabled']}")
    print(f"Top 10 Holders: {risk_report['top_10_holders_percentage']:.2f}%")
    print(f"LP Address: {risk_report['lp_address']}")
    print(f"LP Burned: {risk_report['lp_burned']}")
    print(f"Pooled Tokens: {risk_report['pooled_tokens']}")
    print(f"Pooled SOL: {risk_report['pooled_sol']}")
    print(f"Open Trading: {risk_report['open_trading']}")