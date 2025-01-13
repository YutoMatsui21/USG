import os
import sys
import yaml
import logging
from pathlib import Path
import argparse
import re
from tqdm import tqdm

class Config:
    """設定を管理するクラス"""

    def __init__(self, config_path: str):
        self.config = self.load_config(config_path)
        # キー名を 'album_dir' に統一
        self.album_dir: str = self.config.get('album_dir', 'album')
        self.log_file: str = self.config.get('log_file', 'rename_log.log')

    @staticmethod
    def load_config(config_path: str) -> dict:
        """YAML形式の設定ファイルを読み込む"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"設定ファイルが見つかりません: {config_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"設定ファイルの解析中にエラーが発生しました: {e}")
            sys.exit(1)

class Logger:
    """ログ設定を管理するクラス"""

    @staticmethod
    def setup_logging(log_file: str) -> None:
        """ログ設定を初期化"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )

def sanitize_filename(filename: str) -> str:
    """
    ファイル名に使用できない文字を削除または置換します。
    Windowsのファイル名に無効な文字: \ / : * ? " < > |
    """
    invalid_chars = r'[\\/:*?"<>|]'
    sanitized = re.sub(invalid_chars, '_', filename)
    return sanitized

def process_album(album_name: str, album_path: Path) -> None:
    """
    1つのアルバムフォルダ内の全テキストファイルをリネームします。
    ファイル名は「番号_タイトル.txt」の形式になります。
    """
    txt_files = list(album_path.glob("*.txt"))
    if not txt_files:
        logging.warning(f"アルバム '{album_name}' にテキストファイルが存在しません。")
        return

    logging.info(f"アルバム '{album_name}' を処理中...")

    for file_path in tqdm(txt_files, desc=f"Processing {album_name}", unit="file"):
        try:
            with file_path.open('r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if not first_line:
                    logging.warning(f"ファイルの1行目が空です: {file_path.name}")
                    continue

            # 元のファイル名から番号を抽出（例: "0_txt.txt" -> "0"）
            match = re.match(r"(\d+)", file_path.stem)
            if not match:
                logging.warning(f"ファイル名に番号が含まれていません: {file_path.name}")
                continue
            number = match.group(1)

            # タイトルをサニタイズ
            title = sanitize_filename(first_line)

            new_filename = f"{number}_{title}.txt"
            new_file_path = album_path / new_filename

            if new_file_path.exists():
                logging.error(f"新しいファイル名が既に存在します: {new_file_path}")
                continue

            file_path.rename(new_file_path)
            logging.info(f"ファイルをリネームしました: {file_path.name} -> {new_filename}")

        except Exception as e:
            logging.error(f"ファイルの処理中にエラーが発生しました {file_path.name}: {e}")

def rename_files(album_dir: str) -> None:
    """
    指定された album_dir 内の各アルバムフォルダを巡回し、
    各アルバム内のテキストファイルをリネームします。
    """
    p = Path(album_dir)
    if not p.is_dir():
        logging.error(f"指定されたディレクトリが存在しません: {album_dir}")
        sys.exit(1)

    album_list = [d for d in p.iterdir() if d.is_dir()]
    if not album_list:
        logging.error(f"指定されたディレクトリにアルバムフォルダが存在しません: {album_dir}")
        sys.exit(1)

    for album_path in album_list:
        album_name = album_path.name
        process_album(album_name, album_path)

def main():
    # コマンドライン引数の設定
    parser = argparse.ArgumentParser(description="テキストファイルの名前を変更するプログラム")
    parser.add_argument('--config', type=str, default='config.yaml', help='設定ファイルのパス（YAML形式）')
    args = parser.parse_args()

    # 設定の読み込み
    config = Config(args.config)

    # ログの設定
    Logger.setup_logging(config.log_file)

    # ファイルのリネーム処理
    rename_files(config.album_dir)

if __name__ == "__main__":
    main()
