import os
import sys
from mecab import main, load_stopwords, initialize_mecab, process_album, analyze_frequencies, print_analysis

def test_main_exits_if_album_directory_does_not_exist(mocker):
    mocker.patch('os.path.isdir', return_value=False)
    mocker.patch('sys.exit')
    mock_print = mocker.patch('builtins.print')

    main()

    mock_print.assert_called_once_with('ディレクトリが存在しません: album')
    sys.exit.assert_called_once_with(1)

def test_main_prints_analysis_results(mocker):
    mocker.patch('os.path.isdir', side_effect=lambda path: path == "album" or path.startswith("album/"))
    mocker.patch('os.listdir', side_effect=lambda path: ["album1", "album2"] if path == "album" else ["song1.txt", "song2.txt"])
    mocker.patch('builtins.open', mocker.mock_open(read_data="Title\nAge\nKind\n\nLyrics"))
    mocker.patch('mecab.initialize_mecab', return_value=mocker.Mock(parse=lambda text: "surface\tfeature,動詞,*,*,*,*,base_form,*\nEOS"))
    mock_print = mocker.patch('builtins.print')

    main()

    expected_calls = [
        mocker.call("album1:"),
        mocker.call("動詞の頻度分析:"),
        mocker.call("1. base_form: 2"),
        mocker.call(),
        mocker.call("album2:"),
        mocker.call("動詞の頻度分析:"),
        mocker.call("1. base_form: 2"),
        mocker.call(),
        mocker.call("全フォルダの合計頻度分析:"),
        mocker.call("動詞の頻度分析:"),
        mocker.call("1. base_form: 4"),
        mocker.call()
    ]
    mock_print.assert_has_calls(expected_calls, any_order=False)

if __name__ == '__main__':
    pass
