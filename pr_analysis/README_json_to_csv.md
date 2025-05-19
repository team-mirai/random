# JSON to CSV Converter for PR Analysis

このスクリプトは、PR分析のJSONデータをCSVファイルに変換するためのツールです。

## 使い方

```bash
python json_to_csv.py <json_file_path> [output_csv_path]
```

### 引数
- `json_file_path`: 入力JSONファイルのパス（必須）
- `output_csv_path`: 出力CSVファイルのパス（オプション）
  - 指定しない場合、入力ファイルと同じディレクトリに「{入力ファイル名}_id_comment.csv」という名前で保存されます

### 例

すべてのPRデータを変換する：
```bash
python json_to_csv.py 20250518_220220/prs_data.json
```

出力先を指定して変換する：
```bash
python json_to_csv.py 20250518_220220/prs_data.json ./output/pr_data.csv
```

## 出力形式

スクリプトは以下の形式のCSVファイルを生成します：

```
id,comment
123,"PRの本文..."
456,"別のPRの本文..."
...
```

- `id`: PR番号
- `comment`: PR本文
