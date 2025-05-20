# チームみらいの政策リポジトリ分析

このツールは、team-mirai/policyリポジトリのオープンなPull Requestを収集し、分析するためのものです。

## 背景

チームみらいのマニフェスト0.1公開と、それに対するプルリクエスト(修正提案, 以下PR)の作成プロセスのAIによる支援によって、5/18 10:00時点で730件ちかいPRが集まった。

このデータを分析するのは面白いし、デジタル民主主義を推進する上で有用でもある。

デジタル民主主義2030でやるかどうか少し迷ったが、直近でこれが必要になる党はチームみらいだけなので早まった抽象化をしないでチームみらいに密結合で作り、他の政党がこれを必要になったときにforkしたらよい、という進め方をすることにした

## 機能

- GitHub APIを使用してオープンなPRを収集
- PRの詳細情報（基本情報、コメント、レビューコメント、コミット、変更ファイル）を取得
- 収集したデータをJSON形式で保存
- 詳細なMarkdownレポートを生成
- 概要的なサマリーMarkdownを生成
- 並列処理による高速な情報収集
- GitHub APIのレート制限に対応

## 使い方

```bash
python3 pr_analyzer.py [オプション]
```

### オプション

- `--limit N`: 取得するPRの最大数（デフォルト: 100、0=全て取得）
- `--workers N`: 並列処理のワーカー数（デフォルト: 10）
- `--no-comments`: コメントを取得しない
- `--no-review-comments`: レビューコメントを取得しない
- `--no-commits`: コミット情報を取得しない
- `--no-files`: 変更ファイル情報を取得しない
- `--output-dir DIR`: 出力ディレクトリ（デフォルト: pr_analysis）
- `--mode fetch`: データ収集モードで実行する
- `--fetch-mode updated|sequential|priority`: 取得モード（更新日時順・ID順・未取得優先）を指定
- `--ignore-last-run`: 前回の実行情報を無視する（ID順モード用）
- `--start-id N`: 開始ID（ID順モード用）
- `--max-id N`: 最大ID（ID順モード用）

### PRデータ収集モード

PRデータの収集には以下の3つのモードがあります：

1. **更新日時順モード (デフォルト)**
   ```
   python pr_analyzer.py --mode fetch --fetch-mode updated
   ```
   更新日時の新しい順にPRを取得します。前回の実行情報を参照し、前回取得したPRと同じ時刻のPRが見つかったら処理を終了します。

2. **ID順モード (「今あるものを全部取る」モード)**
   ```
   python pr_analyzer.py --mode fetch --fetch-mode sequential --ignore-last-run
   ```
   ID1から順に全PRを取得します。`--start-id`で開始IDを、`--max-id`で最大IDを指定できます。

3. **未取得優先モード**
   ```
   python pr_analyzer.py --mode fetch --fetch-mode priority
   ```
   まだ取得できていないPRを優先的に取得します。その後、残りの取得数があれば更新日時順でPRを取得します。

### 継続的なデータ収集

初回実行後、再度実行することで未取得データや更新データを効率的に収集できます：

```
python pr_analyzer.py --mode fetch --fetch-mode priority
```

これにより、まだ取得できていないPRを優先的に取得し、残りの制限数で更新されたPRを取得します。

### 例

最新の50件のPRを取得し、コミット情報を除外する:
```bash
python3 pr_analyzer_improved.py --limit 50 --no-commits
```

すべてのPRを取得し、20個のワーカーで並列処理する:
```bash
python3 pr_analyzer_improved.py --limit 0 --workers 20
```

## 出力ファイル

スクリプトは以下の種類のファイルを生成します:

1. **JSONデータ**: `prs_data.json`
   - すべての収集データを含む生のJSONファイル
   - プログラムによる分析に適しています

2. **詳細Markdownレポート**: `prs_report.md`
   - 各PRの詳細情報を含む完全なレポート
   - PRの本文、コメント、変更ファイル、コミットなどの詳細情報を含みます

3. **サマリーMarkdown**: `prs_summary.md`
   - PRの概要情報を含む簡潔なレポート
   - 作成者別の統計、最近のPR、よく変更されるファイルなどの概要情報を含みます

4. **Issues内容と変更差分Markdown**: `prs_issues_diffs.md`
   - 各PRのIssue内容と変更差分を含むレポート
   - 全PRの変更差分を一度に確認したい場合に便利です

5. **ファイルごとのMarkdown**: `files/` ディレクトリ
   - 編集対象ファイルごとにPRをグループ化したレポート
   - 特定のファイルに影響するすべてのPRを確認したい場合に便利です
   - `files_index.md` にファイル一覧とPR数が表示されます

## 注意事項

- GitHub APIにはレート制限があります。大量のPRを取得する場合は注意してください。
- 認証されていない場合、APIのレート制限はより厳しくなります。
- スクリプトは自動的にGitHubトークンを取得しようとしますが、環境変数`GITHUB_TOKEN`を設定することもできます。
