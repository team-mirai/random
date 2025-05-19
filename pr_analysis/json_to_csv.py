#!/usr/bin/env python3

import csv
import json
import sys
from pathlib import Path

def convert_json_to_csv(json_file_path, output_csv_path=None):
    """
    JSONファイルからPRのIDとコメント（PR本文）を抽出し、CSVファイルに変換する
    
    Parameters:
    -----------
    json_file_path : str
        入力JSONファイルのパス
    output_csv_path : str, optional
        出力CSVファイルのパス。指定がない場合は入力ファイルと同じディレクトリに
        "{入力ファイル名}_id_comment.csv"という名前で保存される
    """
    print(f"Converting JSON file: {json_file_path}")
    
    # 出力ファイルパスが指定されていない場合、デフォルトのパスを生成
    if output_csv_path is None:
        input_path = Path(json_file_path)
        output_csv_path = input_path.parent / f"{input_path.stem}_id_comment.csv"
    
    try:
        # JSONファイルを読み込む
        with open(json_file_path, encoding='utf-8') as f:
            data = json.load(f)
        
        # データが配列であることを確認
        if not isinstance(data, list):
            print("Error: JSON data is not a list")
            return False
        
        print(f"Found {len(data)} PRs in the JSON file")
        
        # CSVファイルに書き込む
        with open(output_csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # ヘッダー行を書き込む
            writer.writerow(["id", "comment"])
            
            # 各PRのデータを処理
            count = 0
            for pr in data:
                if pr and 'basic_info' in pr:
                    basic_info = pr['basic_info']
                    
                    # IDとコメント（PR本文）を抽出
                    pr_id = basic_info.get('number')  # PR番号をIDとして使用
                    comment = basic_info.get('body', '')  # PR本文をコメントとして使用
                    
                    # 空でない場合のみCSVに書き込む
                    if pr_id is not None and comment:
                        writer.writerow([pr_id, comment])
                        count += 1
            
            print(f"Wrote {count} rows to CSV file: {output_csv_path}")
        
        return True
    
    except Exception as e:
        print(f"Error converting JSON to CSV: {e}")
        return False

def main():
    # コマンドライン引数を解析
    if len(sys.argv) < 2:
        print("Usage: python json_to_csv.py <json_file_path> [output_csv_path]")
        return
    
    json_file_path = sys.argv[1]
    output_csv_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    # JSONをCSVに変換
    success = convert_json_to_csv(json_file_path, output_csv_path)
    
    if success:
        print("Conversion completed successfully")
    else:
        print("Conversion failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
