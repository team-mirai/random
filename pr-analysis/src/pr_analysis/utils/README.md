# Utils モジュール

共通ユーティリティ関数を提供するモジュールです。

## 主な機能

- ファイル操作
- 日付処理
- データ変換
- ヘルパー関数

## 主要コンポーネント

### file_utils.py

ファイル操作に関する関数を提供します。

```python
from pr_analysis.utils.file_utils import load_json_file, save_json_file

# JSONファイルの読み込み
data = load_json_file("input.json")

# JSONファイルの保存
save_json_file(data, "output.json")
```

### date_utils.py

日付処理に関する関数を提供します。

```python
from pr_analysis.utils.date_utils import format_date, calculate_duration

# 日付のフォーマット
formatted_date = format_date("2023-01-01T00:00:00Z")

# 期間の計算
duration = calculate_duration("2023-01-01T00:00:00Z", "2023-01-02T00:00:00Z")
```

## 依存関係

- datetime: 日付処理
- json: JSONデータ処理
- pathlib: パス操作
