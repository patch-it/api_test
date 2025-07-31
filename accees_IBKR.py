from typing import Literal
import requests
import urllib3
import os
import stat
import random
import pandas as pd
from requests.packages.urllib3.exceptions import InsecureRequestWarning  # type: ignore
import subprocess
#  temp login to paper: ohrikq855

# TODO move to config
BASE_URL = "https://localhost:5000/v1"
headers = {"User-Agent": "MyApp/1.0", "Accept": "*/*", "Connection": "keep-alive"}


# Get account ID assuming only one account in profile
def get_account_id():
    data = session.get(f"{BASE_URL}/api/portfolio/accounts")
    response = data.json()
    account_id = response[0]["id"]  # Could be modified to handle multiple accounts
    return account_id


# TODO fetch cookie automatically and add to config
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
session = requests.Session()
session.verify = False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
session = requests.Session()
session.verify = False
session.cookies.set(
    "JSESSIONID", "your_cookie_here"
)

# TODO could move all urls to a config file


# Fetch response from the API
def get_response(url: str, headers: dict = headers, params: dict = None):
    url = f"{BASE_URL}{url}"
    response = session.get(url, headers=headers, params=params)
    return response


def post_response(url: str, headers: dict = headers, data: dict = None):
    url = f"{BASE_URL}{url}"
    response = session.post(url, headers=headers, json=data)
    return response


# TODO create permanent file for df and safe new orders to df
# Check current orders
def check_current_orders():
    """
    Fetches current orders from the IBKR API and returns a DataFrame with stock names,
    statuses, and order sizes.
    Returns:
        pd.DataFrame: DataFrame containing stock names, statuses, and order sizes.
    """
    response = get_response("/api/iserver/account/orders")
    if response.status_code == 200:
        data = response.json()
        orders = data.get("orders", [])
        if orders:
            stock_name = [item.get("ticker") for item in orders]
            order_status = [item.get("status") for item in orders]
            order_size = [item.get("totalSize") for item in orders]

            orders_data = {
                "Stock": stock_name,
                "Status": order_status,
                "Size": order_size,
            }
            return pd.DataFrame(orders_data)


def check_session():
    response = get_response("/portal/sso/validate")
    if response.status_code == 200:
        print("Session is active.")
    else:
        print(f"Session check failed: {response.text}")
        raise ConnectionError(
            "Session is not active. Please check your connection or session cookie."
        )


# Fetch id of a stock
def get_conid(symbol: str):
    """
    Fetches the contract ID (conid) for a given stock symbol from the IBKR API.
    Args:
        symbol (str): The stock symbol to search for.
    Returns:
        str: The contract ID (conid) of the stock if found, otherwise None.
    """
    params = {"symbol": symbol}
    response = get_response("/api/iserver/secdef/search", params=params)
    data = response.json()
    if data and isinstance(data, list):
        return data[0].get("conid")
    else:
        print(f"No conid found for {symbol}. Response: {data}")
    return None


# Fetch market data for a stock
# Fields: 31=last, 55=bid, 70=ask - works only when markets are open
def get_market_data(conid: str):
    """
    Fetches market data for a given contract ID (conid) from the IBKR API.
    Args:
        conid (int): The contract ID of the stock.
    Returns:
        dict: A dictionary containing market data of a given stock.
    """
    params = {"conids": conid, "fields": "31,55,70"}
    response = get_response("/api/iserver/marketdata/snapshot", params=params)
    if response.status_code != 200:
        print(f"Failed to fetch market data: {response.status_code} - {response.text}")
        return None
    return response.json()


# TODO add market status to df
# Check market data for a list of tickers
def check_market(tickers: list):
    """Fetches and prints market data for a list of stock tickers.
    Args:
        tickers (list): List of stock ticker symbols to check.
    """
    keys_to_check = ["31", "55", "70"]  # Last, Bid, Ask -> config
    for symbol in tickers:
        print(f"\nChecking {symbol}...")
        conid = get_conid(symbol)
        if not conid:
            print(f"Could not fetch contract ID for {symbol}.")
            continue

        data = loop_market_data(conid, keys_to_check)


        # TODO expand data points and check for data before calling get
        if isinstance(data, list):
            print(
                f"{symbol}: Last={data[0].get('31')}, Bid={data[0].get('55')}, Ask={data[0].get('70')}"
            )
        else:
            missing_keys = [key for key in keys_to_check if key not in data]
            print(
                f"Market data for {symbol} is incomplete. Expected keys: {keys_to_check}. Missing keys: {missing_keys}"
            )

        # time.sleep(1.5)  # Rate limiting lol


# Get single account information of a given stock
def get_position_quantity(account_id: str, conid: str):
    """
    Fetches the quantity of a specific stock position in a given account.
    Args:
        account_id (str): The account ID to check.
        conid (str): The contract ID of the stock.
    Returns:
        int: The quantity of the stock position if found, otherwise 0.
    """
    response = get_response(f"/api/portfolio/{account_id}/positions/{conid}")
    if response.status_code == 200:
        data = response.json()
        if data:
            return data[0]
        else:
            print(f"No data in response: {response.status_code} - {response.text}")
    else:
        print(
            f"Failed to fetch position for conid {conid} and account {account_id}: {response.status_code} - {response.text}"
        )
    return 0


# Place an order for a stock
def place_order(symbol: str, quantity: int, side: Literal["BUY", "SELL"]):
    """
    Places an order for a stock with the specified quantity and side (buy/sell).
    Args:
        symbol (str): The stock symbol to trade.
        quantity (int): The number of shares to buy or sell.
        side (Literal["BUY", "SELL"]): The action to perform (buy or sell).
    Returns:
        bool: True if the order was placed successfully, False otherwise.
    """
    conid = int(get_conid(symbol))
    if not conid:
        print(f"Could not fetch conid for {symbol}")
        return

    if not account_id:
        print("No active accounts, check your connection.")
        return

    # Check if the account has enough balance for the order
    if side == "SELL":
        held = get_position_quantity(account_id, conid)
        if held < quantity:
            print(
                f"Not enough holdings to sell. Held: {held}, Tried to sell: {quantity}"
            )
            return

    order_payload = {
        "orders": [
            {
                "conid": conid,  # Contract ID for the stock
                "secType": "STK",  # Security type
                "orderType": "MKT",  # Market order
                "price": 1,  # Price for limit orders, ignored for market orders
                "side": side,  # Buy/sell action
                "quantity": quantity,  # Number of shares to buy
                "tif": "DAY",  # Time in force
                "outsideRTH": True,  # Outside Regular Trading Hours
                "useAdaptive": False,  # Use adaptive orders
            }
        ]
    }

    response = post_response(
        f"/api/iserver/account/{account_id}/orders", headers=headers, data=order_payload
    )

    if response.status_code == 200:
        print(f"Order placed for {quantity} shares of {symbol}")
        return True
    else:
        print(f"Failed to place order: {response.status_code} - {response.text}")
        return False


# Get account balances for a specific currency EUR or USD
def get_account_balances(currency: Literal["EUR", "USD"]):
    """
    Fetches the account balances for a specific currency (EUR or USD).
    Args:
        currency (Literal["EUR", "USD"]): The currency to check balances for.
    Returns:
        float: The cash balance in the specified currency if successful, otherwise None.
    """
    response = get_response(f"/api/portfolio//{account_id}/ledger")

    if response.status_code == 200:
        data = response.json()
        #print(f"Money to spend: {currency} - ", data[currency]["cashbalance"])
        return data[currency]["cashbalance"]
    else:
        print(f"Failed to get account summary: {response.status_code} {response.text}")
        return None


# Convert currency from one to another - not working yet
def currency_exchange(from_currency: str, to_currency: str, amount: float = 0.0):
    """Converts currency from one type to another using the IBKR API.
    Args:
        from_currency (str): The currency to convert from (e.g., "EUR").
        to_currency (str): The currency to convert to (e.g., "USD").
        amount (float): The amount to convert. If 0, uses the available balance in the from_currency.
    Returns:
        bool: True if the conversion was successful, False otherwise.
    """
    if amount > 0:
        convert_amount = amount
    else:
        convert_amount = get_account_balances("EUR")

    payload = {
        "orders": [
            {
                "conid": int(get_conid(f"{from_currency}.{to_currency}")),
                "secType": "CASH",
                "orderType": "MKT",
                "side": "SELL",
                "quantity": convert_amount,
                "tif": "DAY",
                "outsideRTH": True,
                "useAdaptive": False,
            }
        ]
    }
    response = post_response(
        f"/api/iserver/account/{account_id}/orders", headers=headers, data=payload
    )
    if response.status_code == 200:
        print(f"Converted {amount} {from_currency} to {to_currency}")
        return True
    else:
        print(f"Failed to convert currency: {response.status_code} - {response.text}")
        return False

def loop_market_data(conid: str, keys_to_check: list):
    '''Loops through market data requests for a given contract ID (conid) until the required keys are found or maximum attempts are reached.
    Args:
        conid (str): The contract ID of the stock.
        keys_to_check (list): List of keys to check in the market data.
    Returns:
        list: A list of dictionaries containing market data if the required keys are found, otherwise returns the first dict in data.
      '''  
    for attempt in range(10):
        data = get_market_data(conid)

        if data is None:
            return data[0]

        if not isinstance(data, list) or not all(isinstance(d, dict) for d in data):
            print(f"Unexpected data format expected a list of dictionaries but got {type(data)}")
            return data[0]

        if any(all(key in d for key in keys_to_check) for d in data):
            return data

        # Check if any dict contains both '31' and '70'
        found = any('31' in d and '70' in d for d in data)
        if found:
            return data

    print("Reached maximum attempts without finding all keys.")
    return data[0]


if __name__ == "__main__":
    # Verify connection
    try:
        check_session()
    except ConnectionError as e:
        print(f"Connection to IBKR Client Portal failed: {e}\nAttempting to start IB Gateway...")

        try:
            # Set execute permissions for the script
            st = os.stat('./start_gateway_and_open.sh')
            os.chmod('./start_gateway_and_open.sh', st.st_mode | stat.S_IEXEC)

            result = subprocess.run(
                ["./start_gateway_and_open.sh"],
                capture_output=True,
                text=True,
                check=True
        )
            print(result.stdout)
            if result.stderr:
                print(f"Error: {result.stderr}")
        except (PermissionError) as e:
            print(f"Permission error: {e}\nMake sure the script has execute permissions. " \
            "\nSetting execute permissions for start_gateway_and_open.sh...")

            
            


    # Check status for account
    print("Auth status:", get_response("/api/iserver/auth/status").json())
    account_id = get_account_id()

    # Stock examples
    TICKERS = random.sample(
        [
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "TSLA",
            "NVDA",
            "META",
            "NFLX",
            "AMD",
            "BABA",
            "INTC",
            "V",
            "JPM",
            "DIS",
            "BA",
        ],
        10,
    )

    # Check market data for the selected tickers
    check_market(TICKERS)

    # Check current balance
    mooooooney = get_account_balances("USD")

    # Convert currency from EUR to USD
    currency_exchange("EUR", "USD", 1000)

    # Place orders for the selected tickers
    for ticker in TICKERS:
        place_order(ticker, 1, "BUY")

    # Check current orders
    current_orders = check_current_orders()
