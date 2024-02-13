# 必要なライブラリやパッケージをインポート
import requests
import urllib.parse
import os
from bs4 import BeautifulSoup


# 検索キーワードとダウンロードする画像の数を設定
print("キーワード：")
keyword = input()
print("画像の枚数：")
num_images = int(input())

# 画像を保存するフォルダを作成（存在しない場合）
folder = keyword.replace(" ", "_")
if not os.path.exists(folder):
    os.mkdir(folder)

# Bing画像検索のURLを生成
base_url = "https://www.bing.com/images/search"
query = urllib.parse.quote(keyword)
params = f"?q={query}&form=HDRSC2&first=1&scenario=ImageBasicHover"
url = base_url + params

# リクエストを送信してレスポンスを取得
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

# 画像のURLを抽出してリストに格納
image_urls = []
for img in soup.find_all("img", class_="mimg"):
    #print(img.attrs) # キーと値の辞書として表示される
    for attr in img.attrs:
        if attr == "src":
        	image_url = img["src"]
        elif attr == "data-src":
          	image_url = img["data-src"]
        
    image_urls.append(image_url)

# リストから画像のURLを取り出してダウンロード
count = 0
for image_url in image_urls:
    # ダウンロードする画像の数に達したら終了
    if count >= num_images:
        break
    # 画像のファイル名と保存先のパスを設定
    filename = f"{keyword}_{count}.jpg"
    filepath = os.path.join(folder, filename)
    # 画像をダウンロードして保存
    try:
        image_data = requests.get(image_url).content
        with open(filepath, "wb") as f:
            f.write(image_data)
        print(f"Downloaded {filename} from {image_url}")
        count += 1
    except Exception as e:
        print(f"Failed to download {filename} from {image_url}: {e}")
