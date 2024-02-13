import MeCab
from collections import Counter
import os

# ストップワードを定義します
stopwords = {
    "名詞": ["こと", "ん", "の", "みたい", "まま", "これ", "もの", "それ", "そう", "しない", "しよう", "さ", "なん", "よう"],
    "動詞": ["し", "なっ", "てる", "い", "れ", "くれ", "でき", "られ", "られる", "ちゃう", "て", "せ", "いる", "ちゃっ", "さ"],
    "形容詞": ["いい", "ない", "なく", "無く", "よ"],
    "副詞": [],
    "接続詞": [],
    "連体詞": [],
    "感動詞": [],
}

# アルバムのリスト
album_list = os.listdir("lyric")
album_len = len(album_list)

# アルバムごとの歌詞解析
for i in range(5, 9):
    album_name = album_list[i]
    file_list = os.listdir("lyric//" + album_name)
    file_len = len(file_list)
    
    # titleという配列を作ります
    title = []

    # titlesという辞書を作ります
    titles = {}

    # keywordsという配列を作ります
    keywords = []

    # ageという配列を作ります
    age = []

    # kindという配列を作ります
    kind = []

    # １曲ごとの歌詞解析
    for l in range(file_len):
        file_name = "lyric\\" + album_name + "\\" + str(l) + ".txt"
        
        # ファイルを読み込みます
        with open(file_name, "r", encoding="utf-8") as f:
            # 1行目はtitleに追加します
            title.append(f.readline().strip())
            # 2行目はageに追加します
            age.append(f.readline().strip())
            # 3行目はkindに追加します
            kind.append(f.readline().strip())
            # 4行目は飛ばします
            next(f)
            text = f.read()

        # MeCabのオブジェクトを作ります
        # 辞書はNEologd
        mecab = MeCab.Tagger(r'-d "C:\mecab-ipadic-neologd"')

        # 形態素解析を実行します
        result = mecab.parse(text)

        # 名詞，動詞，副詞，形容詞のみ抽出します
        # 重複を避けるためにsetを使います
        words = set()
        for line in result.split("\n"):
            if line == "EOS":
                break
            surface, feature = line.split("\t")[:2]
            pos = feature.split(",")[0]
            
            # 動詞，形容詞の場合は終止形にする
            if pos in ["動詞", "形容詞"]:
                #print(surface)
                surface = feature.split(",")[6]
            
            if pos in ["名詞", "動詞", "副詞", "形容詞", "接続詞", "連体詞", "感動詞"]:
                # ストップワードに含まれない場合にだけ追加します
                if surface not in stopwords[pos]:
                    words.add((surface, pos))

        # keywordsに追加します
        keywords.extend(words)

    # titlesに登場したタイトルを追加します
    for word in words:
        if word not in titles:
            titles[word] = []
        titles[word].append(title[i])

    # 頻度分析を行います
    counter = Counter(keywords)

    # 結果を出力します
    print(album_name + ":")
    for pos in ["名詞", "動詞", "副詞", "形容詞", "接続詞", "連体詞", "感動詞"]:
        print(pos + "の頻度分析:")
        # 数が2以上の単語を降順にソートします
        words = sorted(counter.items(), key=lambda x: x[1], reverse=True)
        # ランキングを表示します
        rank = 1
        for word, count in words:
            if word[1] == pos and count >= 3:
                print(str(rank) + ". " + word[0] + ": " + str(count))
                # 登場したタイトルを表示します
                #print(",\n".join(titles[word]))
                #print("\n")
                rank += 1
        print()
