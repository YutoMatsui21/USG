import os
import sys
import MeCab
import pandas as pd
import yaml
import logging
from collections import Counter, defaultdict
from typing import List, Tuple, Set, Dict, Any
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Border, Side
from openpyxl.utils import get_column_letter
from tqdm import tqdm
import argparse


class Config:
    """設定を管理するクラス"""

    def __init__(self, config_path: str):
        self.config = self.load_config(config_path)
        self.mecab_dict_path: str = self.config.get('mecab_dict_path', 'C:\\mecab-ipadic-neologd')
        self.album_dir: str = self.config.get('album_dir', 'album')
        self.output_excel: str = self.config.get('output_excel', 'frequency_analysis.xlsx')
        self.output_csv: str = self.config.get('output_csv', 'frequency_analysis.csv')
        self.stopwords: Dict[str, Set[str]] = {k: set(v) for k, v in self.config.get('stopwords', {}).items()}
        self.pos_list: List[str] = self.config.get('pos_list', [
            "名詞",
            "動詞",
            "副詞",
            "形容詞",
            "接続詞",
            "連体詞",
            "感動詞",
        ])
        self.output_formats: List[str] = self.config.get('output_formats', ['excel', 'csv'])

    @staticmethod
    def load_config(config_path: str) -> Dict[str, Any]:
        """YAML形式の設定ファイルを読み込む"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logging.error(f"設定ファイルが見つかりません: {config_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            logging.error(f"設定ファイルの解析中にエラーが発生しました: {e}")
            sys.exit(1)


class Logger:
    """ログ設定を管理するクラス"""

    @staticmethod
    def setup_logging(log_file: str = 'word_analyzer.log') -> None:
        """ログ設定を初期化"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )


class MeCabAnalyzer:
    """MeCabを使用してテキストを解析するクラス"""

    def __init__(self, mecab_dict_path: str, stopwords: Dict[str, Set[str]]):
        self.mecab = self.initialize_mecab(mecab_dict_path)
        self.stopwords = stopwords

    @staticmethod
    def initialize_mecab(dict_path: str) -> MeCab.Tagger:
        """MeCabのTaggerオブジェクトを初期化"""
        try:
            mecab = MeCab.Tagger(f'-d "{dict_path}"')
            mecab.parse('')  # バグ回避のための初期パース
            return mecab
        except Exception as e:
            logging.error(f"MeCabの初期化に失敗しました: {e}")
            sys.exit(1)

    def parse_text(self, text: str) -> List[Tuple[str, str]]:
        """テキストを形態素解析し、単語と品詞のリストを返す"""
        words = []
        result = self.mecab.parse(text)
        if not result:
            return words
        for line in result.splitlines():
            if line == "EOS" or not line:
                continue
            try:
                surface, feature = line.split("\t")[:2]
                features = feature.split(",")
                pos = features[0]
                if pos in {"動詞", "形容詞"}:
                    base_form = features[6]
                    surface = base_form if base_form != "*" else surface
                # ストップワードのフィルタリング
                if pos in self.stopwords:
                    if surface in self.stopwords[pos]:
                        continue  # ストップワードならスキップ
                words.append((surface, pos))
            except ValueError:
                continue
        return words


class WordAnalyzer:
    """歌詞ファイルから単語を解析し、出現頻度とファイル出現数をカウントするクラス"""

    def __init__(self, config: Config, mecab_analyzer: MeCabAnalyzer):
        self.config = config
        self.mecab_analyzer = mecab_analyzer
        self.frequency_analysis: Dict[str, Dict[str, Counter]] = defaultdict(lambda: defaultdict(Counter))
        self.file_appearance_analysis: Dict[str, Dict[str, Counter]] = defaultdict(lambda: defaultdict(Counter))

    def process_album(self, album_name: str, album_path: str, encoding: str = 'utf-8') -> None:
        """1つのアルバムフォルダ内の全ファイルを処理し、分析データを更新する"""
        file_list = [f for f in os.listdir(album_path) if f.endswith('.txt')]
        for file_name in tqdm(file_list, desc=f"Processing {album_name}", unit="file"):
            file_path = os.path.join(album_path, file_name)
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    lines = f.readlines()
                    if len(lines) < 4:
                        logging.warning(f"ファイル形式が正しくありません（4行未満）: {file_path}")
                        continue
                    # タイトル、年齢、種類を読み飛ばし
                    text = ''.join(lines[4:]).strip()
            except FileNotFoundError:
                logging.error(f"ファイルが見つかりません: {file_path}")
                continue
            except UnicodeDecodeError:
                logging.error(f"エンコーディングエラー: {file_path} を '{encoding}' で読み込めません")
                continue
            except Exception as e:
                logging.error(f"ファイルの読み込み中にエラーが発生しました {file_path}: {e}")
                continue

            # 単語のリストを取得（ストップワードはここで除外済み）
            words = self.mecab_analyzer.parse_text(text)

            # 頻度分析
            for word, pos in words:
                if pos in self.config.pos_list:
                    self.frequency_analysis[album_name][pos][word] += 1
                    self.frequency_analysis["総合"][pos][word] += 1

            # ファイル出現数分析（ユニーク単語のみ）
            unique_words = set(words)
            for word, pos in unique_words:
                if pos in self.config.pos_list:
                    self.file_appearance_analysis[album_name][pos][word] += 1
                    self.file_appearance_analysis["総合"][pos][word] += 1

    def analyze(self, encoding: str = 'utf-8') -> None:
        """全アルバムの分析を実行する"""
        if not os.path.isdir(self.config.album_dir):
            logging.error(f"ディレクトリが存在しません: {self.config.album_dir}")
            sys.exit(1)

        album_list = [d for d in os.listdir(self.config.album_dir) if os.path.isdir(os.path.join(self.config.album_dir, d))]
        if not album_list:
            logging.error("アルバムフォルダが空です。")
            sys.exit(1)

        for album_name in album_list:
            album_path = os.path.join(self.config.album_dir, album_name)
            self.process_album(album_name, album_path, encoding=encoding)

    def get_top_words(self, counter: Counter, top_n: int = 10) -> List[Tuple[str, int]]:
        """指定されたカウンターから上位top_n単語を取得する"""
        return counter.most_common(top_n)

    def create_excel(self, output_excel: str = "frequency_analysis.xlsx") -> None:
        """分析結果をExcelファイルに出力する"""
        wb = Workbook()
        ws_freq = wb.active
        ws_freq.title = "Frequency_Analysis"
        ws_file = wb.create_sheet(title="File_Appearance")

        # シートごとにデータを書き込み
        self.write_sheet(ws_freq, self.frequency_analysis, is_file_appearance=False)
        self.write_sheet(ws_file, self.file_appearance_analysis, is_file_appearance=True)

        # Excelファイルの保存
        wb.save(output_excel)
        logging.info(f"分析結果がExcelファイルに保存されました: {output_excel}")

    def write_sheet(self, ws: Workbook, analysis_data: Dict[str, Dict[str, Counter]], is_file_appearance: bool = False) -> None:
        """指定されたシートに分析データを書き込む"""
        header_font = Font(bold=True, size=14)
        table_header_font = Font(bold=True)
        pos_colors = {
            "名詞": "FFCCCC",    # ライトレッド
            "動詞": "CCFFCC",    # ライトグリーン
            "副詞": "CCCCFF",    # ライトブルー
            "形容詞": "FFFFCC",  # ライトイエロー
            "接続詞": "FFCCFF",  # ライトピンク
            "連体詞": "CCFFFF",  # ライトシアン
            "感動詞": "FFEECC",  # ライトオレンジ
        }

        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        thick_top_border = Border(
            top=Side(style='thick'),
        )

        for idx, pos in enumerate(self.config.pos_list):
            current_column = idx * 4 + 1  # 品詞ごとに4列（3列 + 1列の空白）ずつ使用

            # 品詞名をヘッダーとして挿入
            cell = ws.cell(row=1, column=current_column, value=pos)
            cell.font = header_font
            cell.fill = PatternFill(start_color=pos_colors.get(pos, "FFFFFF"), end_color=pos_colors.get(pos, "FFFFFF"), fill_type="solid")
            cell.border = thin_border

            # テーブルヘッダー
            ws.cell(row=2, column=current_column, value="アルバム名").font = table_header_font
            ws.cell(row=2, column=current_column + 1, value="単語").font = table_header_font
            ws.cell(row=2, column=current_column + 2, value="出現頻度" if not is_file_appearance else "出現ファイル数").font = table_header_font
            for col in range(current_column, current_column + 3):
                cell = ws.cell(row=2, column=col)
                cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
                cell.border = thin_border

            # 各アルバムのトップ10単語
            current_row = 3
            for album_name, pos_counters in analysis_data.items():
                if album_name == "総合":
                    continue  # "総合"を後で追加
                ws.cell(row=current_row, column=current_column, value=album_name).border = thin_border
                if pos in pos_counters and pos_counters[pos]:
                    top_words = self.get_top_words(pos_counters[pos], top_n=10)
                    for word, count in top_words:
                        ws.cell(row=current_row, column=current_column + 1, value=word)
                        ws.cell(row=current_row, column=current_column + 2, value=count)
                        for col in range(current_column, current_column + 3):
                            ws.cell(row=current_row, column=col).border = thin_border
                        current_row += 1
                else:
                    ws.cell(row=current_row, column=current_column + 1, value="データがありません")
                    ws.cell(row=current_row, column=current_column + 2, value="")
                    for col in range(current_column, current_column + 3):
                        ws.cell(row=current_row, column=col).border = thin_border
                    current_row += 1

            # 総合分析のトップ10単語
            ws.cell(row=current_row, column=current_column, value="総合").border = thin_border
            if pos in analysis_data["総合"] and analysis_data["総合"][pos]:
                top_total = self.get_top_words(analysis_data["総合"][pos], top_n=10)
                for word, count in top_total:
                    ws.cell(row=current_row, column=current_column + 1, value=word)
                    ws.cell(row=current_row, column=current_column + 2, value=count)
                    for col in range(current_column, current_column + 3):
                        ws.cell(row=current_row, column=col).border = thin_border
                    current_row += 1
            else:
                ws.cell(row=current_row, column=current_column + 1, value="データがありません")
                ws.cell(row=current_row, column=current_column + 2, value="")
                for col in range(current_column, current_column + 3):
                    ws.cell(row=current_row, column=col).border = thin_border
                current_row += 1

            # アルバム間に区切り線を引く（最後の品詞では引かない）
            if idx < len(self.config.pos_list) - 1:
                ws.cell(row=current_row, column=current_column, value="")
                ws.cell(row=current_row, column=current_column).border = thick_top_border
                current_row += 1

        # 列幅の自動調整
        for idx, pos in enumerate(self.config.pos_list):
            current_column = idx * 4 + 1
            for col in range(current_column, current_column + 3):
                column_letter = get_column_letter(col)
                max_length = 0
                for cell in ws[column_letter]:
                    if cell.value:
                        cell_length = len(str(cell.value))
                        if cell_length > max_length:
                            max_length = cell_length
                adjusted_width = max(max_length + 2, 10)  # 余裕を持たせるために+2、最低幅10
                ws.column_dimensions[column_letter].width = adjusted_width

    def export_to_csv(self, analysis_data: Dict[str, Dict[str, Counter]], analysis_type: str = "Frequency") -> None:
        """分析結果をCSVファイルに出力する"""
        records = []
        for album_name, pos_counters in analysis_data.items():
            for pos, counter in pos_counters.items():
                for word, count in counter.items():
                    records.append({
                        'アルバム名': album_name,
                        '品詞': pos,
                        '単語': word,
                        'カウント': count
                    })
        df = pd.DataFrame(records)
        csv_filename = f"{analysis_type}_Analysis.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        logging.info(f"{analysis_type} 分析結果がCSVファイルに保存されました: {csv_filename}")


def main():
    # コマンドライン引数の設定
    parser = argparse.ArgumentParser(description="歌詞ファイルの単語分析ツール")
    parser.add_argument('--config', type=str, default='config.yaml', help='設定ファイルのパス（YAML形式）')
    parser.add_argument('--encoding', type=str, default='utf-8', help='テキストファイルのエンコーディング')
    args = parser.parse_args()

    # ログの設定
    Logger.setup_logging()

    # 設定の読み込み
    config = Config(args.config)

    # MeCabの初期化
    mecab_analyzer = MeCabAnalyzer(config.mecab_dict_path, config.stopwords)

    # WordAnalyzerの初期化
    analyzer = WordAnalyzer(config, mecab_analyzer)

    # 分析の実行
    analyzer.analyze(encoding=args.encoding)

    # 出力形式に応じた出力
    if 'excel' in config.output_formats:
        analyzer.create_excel(output_excel=config.output_excel)
    if 'csv' in config.output_formats:
        analyzer.export_to_csv(analyzer.frequency_analysis, analysis_type="Frequency")
        analyzer.export_to_csv(analyzer.file_appearance_analysis, analysis_type="File_Appearance")


if __name__ == "__main__":
    main()
