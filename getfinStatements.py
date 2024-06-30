import requests
import json
import os

# 環境変数からREFRESH_TOKENを取得
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")

# REFRESH_TOKENが取得できなかった場合のエラーハンドリング
if not REFRESH_TOKEN:
    raise ValueError("環境変数 'REFRESH_TOKEN' が設定されていません。")

r_post = requests.post(f"https://api.jquants.com/v1/token/auth_refresh?refreshtoken={REFRESH_TOKEN}")

# レスポンスからJSONデータを取得
response_data = r_post.json()

# idTokenを取得
idToken = response_data.get("idToken")

# idTokenが取得できなかった場合のエラーハンドリング
if not idToken:
    raise ValueError("レスポンスに 'idToken' が含まれていません。")

print(idToken)

# 財務情報を取得
headers = {'Authorization': 'Bearer {}'.format(idToken)}
r = requests.get("https://api.jquants.com/v1/fins/statements?code=7832", headers=headers)

# レスポンスを整形して表示
response_json = r.json()
print(json.dumps(response_json, indent=4, ensure_ascii=False))