import openpyxl

# Excelファイルの読み込み
workbook = openpyxl.load_workbook('230406依頼_新規リスト作成&問い合わせ（230409〆切）.xlsx')
sheet = workbook.active

# 会社名とURLの対応を格納する辞書を作成
company_url_dict = {}
for row in sheet.iter_rows(min_row=2, values_only=True):
    if row[1] is not None and row[2] is not None:
        company_name = row[1]
        url = row[2]
        company_url_dict[company_name] = url

# ユーザーからの入力に応じて対応するURLを表示
while True:
    company_name = input('会社名を入力してください（終了する場合はqを入力）：')
    if company_name == 'q':
        break
    url = company_url_dict.get(company_name)
    if url is not None:
        print(url)
    else:
        print('該当する会社が見つかりませんでした。')