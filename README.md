# random

独立したリポジトリにするほどでもないものを気軽にシェアするためのリポジトリです

## 含まれるファイル

- `CONTRIBUTING.md`: コントリビューションガイドライン
- `CLA.md`: コントリビューターライセンス契約
- `.github/`: GitHubの設定ファイル（Issue・PRテンプレート、ワークフロー）
- 各種構成ファイル: Biome, VSCode設定など
- `pr_analysis/`: PR分析ツール（詳細は[pr_analysis/README.md](pr_analysis/README.md)を参照）
  - `pr_analysis/merge_pr_data.py`: 複数のPRデータファイルを統合するスクリプト

## PR分析ツールの使用方法

### 新機能: PRデータ収集モード

PRデータの収集には以下の3つのモードがあります：

1. **更新日時順モード (デフォルト)**
   ```
   python pr_analysis/pr_analyzer.py --mode fetch --fetch-mode updated
   ```
   更新日時の新しい順にPRを取得します。前回の実行情報を参照し、前回取得したPRと同じ時刻のPRが見つかったら処理を終了します。

2. **ID順モード (「今あるものを全部取る」モード)**
   ```
   python pr_analysis/pr_analyzer.py --mode fetch --fetch-mode sequential --ignore-last-run
   ```
   ID1から順に全PRを取得します。`--start-id`で開始IDを、`--max-id`で最大IDを指定できます。

3. **未取得優先モード**
   ```
   python pr_analysis/pr_analyzer.py --mode fetch --fetch-mode priority
   ```
   まだ取得できていないPRを優先的に取得します。その後、残りの取得数があれば更新日時順でPRを取得します。

### 継続的なデータ収集

初回実行後、再度実行することで未取得データや更新データを効率的に収集できます：

```
python pr_analysis/pr_analyzer.py --mode fetch --fetch-mode priority
```

これにより、まだ取得できていないPRを優先的に取得し、残りの制限数で更新されたPRを取得します。

### PRデータの統合

複数のディレクトリに分散したPRデータを統合するには、以下のコマンドを使用します：

```
python pr_analysis/merge_pr_data.py
```

このコマンドは、デフォルトで4つのディレクトリ（20250521_021502、20250521_034352、20250521_034935、20250521_094649）から
`prs_data.json`ファイルを読み込み、重複を除去して一つの統合ファイル（`pr_analysis_results/merged/merged_prs_data.json`）に保存します。
現在の統合ファイルには、PR番号1～1368の範囲から1361個のPRが含まれています（7つのPRは元のデータに含まれていません）。

特定のディレクトリのみを統合する場合：

```
python pr_analysis/merge_pr_data.py --specific-dirs 20250521_034352 20250521_034935 20250521_094649
```

既存の統合ファイルを更新せず、新しいファイルを作成する場合：

```
python pr_analysis/merge_pr_data.py --no-update --output-file path/to/output.json
```

統合されたPRデータを検証するには、以下のコマンドを使用します：

```
python pr_analysis/verify_pr_data.py
```

### 新機能: README対象PRの分類

READMEを対象とするPRを内容に基づいて分類することができます：

```
python pr_analysis/pr_analyzer.py --mode report --classify-readme --input-json pr_analysis/[timestamp]/prs_data.json
```

このコマンドを実行すると、READMEを対象とするPRが内容に基づいて既存のマークダウンファイルに分類され、結果が`classified`ディレクトリに保存されます。

> **注**: この機能を使用するには、環境変数`OPENROUTER_API_KEY`にOpenRouter APIキーを設定する必要があります。
