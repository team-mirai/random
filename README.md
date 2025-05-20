# random

独立したリポジトリにするほどでもないものを気軽にシェアするためのリポジトリです

## 含まれるファイル

- `CONTRIBUTING.md`: コントリビューションガイドライン
- `CLA.md`: コントリビューターライセンス契約
- `.github/`: GitHubの設定ファイル（Issue・PRテンプレート、ワークフロー）
- 各種構成ファイル: Biome, VSCode設定など
- `pr_analysis/`: PR分析ツール（詳細は[pr_analysis/README.md](pr_analysis/README.md)を参照）

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

### 新機能: README対象PRの分類

READMEを対象とするPRを内容に基づいて分類することができます：

```
python pr_analysis/pr_analyzer.py --mode report --classify-readme --input-json pr_analysis/[timestamp]/prs_data.json
```

このコマンドを実行すると、READMEを対象とするPRが内容に基づいて既存のマークダウンファイルに分類され、結果が`classified`ディレクトリに保存されます。

> **注**: この機能を使用するには、環境変数`OPENROUTER_API_KEY`にOpenRouter APIキーを設定する必要があります。
