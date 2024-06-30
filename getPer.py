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

# 銘柄名またはコードを第一引数から取得
stock_name_or_code = sys.argv[1]

# 銘柄コードを取得
stock_info = tse.get_stock_info(stock_name_or_code)
if not stock_info:
    raise ValueError(f"銘柄 '{stock_name_or_code}' の情報が見つかりません。")
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

for statement in statements:
    closing_price = get_closing_price(idToken, code, statement.get("DisclosedDate"))
    if closing_price and statement.get("EarningsPerShare"):
        per = closing_price / float(statement.get("EarningsPerShare"))
    else:
        per = None

    data.append({
        "DisclosedDate": statement.get("DisclosedDate"),
        "NetSales": format_number(statement.get("NetSales")),
        "OperatingProfit": format_number(statement.get("OperatingProfit")),
        "OrdinaryProfit": format_number(statement.get("OrdinaryProfit")),
        "Profit": format_number(statement.get("Profit")),
        "EarningsPerShare": statement.get("EarningsPerShare"),
        "BookValuePerShare": statement.get("BookValuePerShare"),
        "ClosingPrice": format_number(closing_price),
        "PER": format_number(per) if per is not None else None
    })

# DataFrameを作成して表示
df = pd.DataFrame(data)
print(df.to_string(index=False, justify='left'))
