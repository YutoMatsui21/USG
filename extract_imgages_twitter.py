import tweepy
import requests
import os

# 認証に必要なキーとトークン
API_KEY = '5z25ShoLfMXSvRPDAMEP6RB8S'
API_SECRET = 'Op8g8fJu0mxaXswVznkBAVrg61xRUC9meddiHuttv7tRbHYlD2'
ACCESS_TOKEN = '1673697123899166720-AEBbCj0nExyWyTJJlAwdsO9Ov5CRI7'
ACCESS_TOKEN_SECRET = 'yjud6qcMYhQ7bd3Y7nBOhRJKCNA4jh4jUoPijHDtlXSfb'

# APIの認証
auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

# APIオブジェクトの作成
api = tweepy.API(auth)

# USGinfoというアカウントのID
user_id = 'USGinfo'

# USGというフォルダがなければ作成
if not os.path.exists('USG'):
    os.mkdir('USG')

# ストリーミングリスナーの定義
class MyStreamListener(tweepy.Stream):
    # ツイートを受信したときの処理
    def on_status(self, status):
        # ツイートが対象のアカウントからのものであれば
        if status.user.id_str == user_id:
            # ツイートの内容とURLを表示
            print(status.text)
            print(f'https://twitter.com/{user_id}/status/{status.id}')
            # 携帯に通知を送る処理（ここでは省略）
            # ...
            # ツイートに画像があれば
            if 'media' in status.entities:
                # 画像のURLを取得
                media_url = status.entities['media'][0]['media_url']
                # 画像のファイル名を取得
                filename = media_url.split('/')[-1]
                # 画像をダウンロードしてUSGフォルダに保存
                response = requests.get(media_url)
                with open(os.path.join('USG', filename), 'wb') as f:
                    f.write(response.content)

    # エラーが発生したときの処理
    def on_error(self, status_code):
        # ステータスコードを表示
        print(f'Error: {status_code}')
        # 420エラーは制限に達したときなのでストリームを切断
        if status_code == 420:
            return False

# ストリーミングリスナーのインスタンス化
myStreamListener = MyStreamListener(auth)
# ストリームオブジェクトの作成
#myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener)
# 対象のアカウントのツイートを受信するようにフィルタリング
myStreamListener.filter(follow=[user_id])
