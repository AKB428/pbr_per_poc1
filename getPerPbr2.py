import requests
import os
import json
import pandas as pd
import sys
from tokyo_stock_exchange import tse

def format_number(value):
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return value

def get_closing_price(idToken, code, date):
    headers = {'Authorization': f'Bearer {idToken}'}
    params = {"code": code, "date": date}
    r_get = requests.get("https://api.jquants.com/v1/prices/daily_quotes", headers=headers, params=params)
    response_json = r_get.json()
    daily_quotes = response_json.get('daily_quotes', [])
    if daily_quotes:
        return daily_quotes[0].get('Close')
    return None

def get_price_range(idToken, code, start_date, end_date):
    headers = {'Authorization': f'Bearer {idToken}'}
    params = {"code": code, "from": start_date, "to": end_date}
    r_get = requests.get("https://api.jquants.com/v1/prices/daily_quotes", headers=headers, params=params)
    response_json = r_get.json()
    daily_quotes = response_json.get('daily_quotes', [])
    if daily_quotes:
        high_prices = [quote.get('High') for quote in daily_quotes]
        low_prices = [quote.get('Low') for quote in daily_quotes]
        return max(high_prices), min(low_prices)
    return None, None

# 銘柄名またはコードを第一引数から取得
stock_name_or_code = sys.argv[1]

# 銘柄コードを取得
stock_info = tse.get_stock_info(stock_name_or_code)
if not stock_info:
    raise ValueError(f"銘柄 '{stock_name_or_code}' の情報が見つかりません。")
print("Stock Info:", stock_info)  # 取得したstock_infoを出力
code = stock_info[0]

# 環境変数からREFRESH_TOKENを取得
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")

# REFRESH_TOKENが取得できなかった場合のエラーハンドリング
if not REFRESH_TOKEN:
    raise ValueError("環境変数 'REFRESH_TOKEN' が設定されていません。")

# POSTリクエストを送信
r_post = requests.post(f"https://api.jquants.com/v1/token/auth_refresh?refreshtoken={REFRESH_TOKEN}")

# レスポンスからJSONデータを取得
response_data = r_post.json()

# idTokenを取得
idToken = response_data.get("idToken")

# idTokenが取得できなかった場合のエラーハンドリング
if not idToken:
    raise ValueError("レスポンスに 'idToken' が含まれていません。")

# APIエンドポイントへのGETリクエスト
headers = {'Authorization': f'Bearer {idToken}'}
params = {"code": code}
r_get = requests.get("https://api.jquants.com/v1/fins/statements", headers=headers, params=params)

# レスポンスを取得
response_json = r_get.json()

# 指定された項目を抽出して整形
statements = response_json.get('statements', [])
data = []
high_per = None
low_per = None

for statement in statements:
    closing_price = get_closing_price(idToken, code, statement.get("DisclosedDate"))
    earnings_per_share = statement.get("EarningsPerShare")
    book_value_per_share = statement.get("BookValuePerShare")

    if closing_price and earnings_per_share:
        per = closing_price / float(earnings_per_share)
    else:
        per = None

    if closing_price and book_value_per_share:
        pbr = closing_price / float(book_value_per_share)
    else:
        pbr = None

    data.append({
        "DisclosedDate": statement.get("DisclosedDate"),
        "NetSales": format_number(statement.get("NetSales")),
        "OperatingProfit": format_number(statement.get("OperatingProfit")),
        "OrdinaryProfit": format_number(statement.get("OrdinaryProfit")),
        "Profit": format_number(statement.get("Profit")),
        "EarningsPerShare": earnings_per_share,
        "BookValuePerShare": book_value_per_share,
        "ClosingPrice": format_number(closing_price),
        "PER": f"{per:.1f}" if per is not None else None,
        "PBR": f"{pbr:.2f}" if pbr is not None else None
    })

# 最後のstatementから期間を取得
last_statement = statements[-1]
start_date = last_statement.get("CurrentPeriodStartDate")
end_date = last_statement.get("CurrentPeriodEndDate")
high_price, low_price = get_price_range(idToken, code, start_date, end_date)

if high_price and last_statement.get("EarningsPerShare"):
    high_per = high_price / float(last_statement.get("EarningsPerShare"))

if low_price and last_statement.get("EarningsPerShare"):
    low_per = low_price / float(last_statement.get("EarningsPerShare"))

# DataFrameを作成して表示
df = pd.DataFrame(data)
print(df.to_string(index=False, justify='left'))

print(f"\n対象期間: {start_date} ～ {end_date}")
print(f"High Price: {format_number(high_price)}")
print(f"Low Price: {format_number(low_price)}")
print(f"High PER: {high_per:.1f}" if high_per is not None else "High PER: N/A")
print(f"Low PER: {low_per:.1f}" if low_per is not None else "Low PER: N/A")
