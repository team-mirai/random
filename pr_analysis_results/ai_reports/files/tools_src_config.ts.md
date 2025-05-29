# tools/src/config.ts に関するPull Request

生成日時: 2025-05-29 07:24:37

## このファイルに影響するPull Request (1件)

| # | タイトル | 作成者 | 作成日 | 状態 | 変更 |
|---|---------|--------|--------|------|------|
| #1211 | [PR自動ラベル付けバッチの追加](https://github.com/team-mirai/policy/pull/1211) | devin-ai-integration[bot] | 2025-05-19 | added | +32/-0 |

## 各Pull Requestの詳細

### #1211: PR自動ラベル付けバッチの追加

- **URL**: https://github.com/team-mirai/policy/pull/1211
- **作成者**: devin-ai-integration[bot]
- **作成日時**: 2025-05-19 13:16:09
- **ブランチ**: devin/1747660390-add-pr-auto-labeler → main

#### Issue内容

# PR自動ラベル付けバッチの追加

PRに対して適切なラベルを自動的に付けるバッチスクリプトを追加しました。

ファイルとラベルのマッピング設定に基づいて、PRの変更ファイルからラベルを決定します。

## 使用方法

1. `tools/.env`ファイルにGitHubトークンを設定
2. `cd tools && npm install`で依存関係をインストール
3. `npm run build && npm run start`でスクリプトを実行

実行するとラベルのないPRを自動的に取得し、ラベルを適用します。

## 実装詳細

- TypeScriptのOctokitライブラリを使用してGitHub APIと連携
- 設定ファイル(config.ts)にファイルパターンとラベルのマッピングを定義
- ラベルがついていないPRを対象に、変更されたファイルを取得して適切なラベルを付与
- ページング処理によりバッチ単位（デフォルト10件）でPRを処理
- GitHub APIの `labels: "none"` パラメータを使用して効率的にラベルなしPRを取得

## 環境変数

- `GITHUB_TOKEN`: GitHub API認証用トークン（必須）
- `REPO_OWNER`: リポジトリのオーナー名（デフォルト: team-mirai）
- `REPO_NAME`: リポジトリ名（デフォルト: policy）
- `BATCH_SIZE`: 一度に処理するPR数（デフォルト: 10）

Link to Devin run: https://app.devin.ai/sessions/0dcfb2a9e35648d3ac5b800c788c250a
Requested by: jujunjun110@gmail.com


#### 変更差分

##### tools/src/config.ts (added, +32/-0)

```diff
@@ -0,0 +1,32 @@
+interface FileLabelMapping {
+  pattern: string;
+  label: string;
+}
+
+export const fileLabelMappings: FileLabelMapping[] = [
+  { pattern: "README.md", label: "README" },
+  { pattern: "11_ステップ１教育.md", label: "教育" },
+  { pattern: "12_ステップ１子育て.md", label: "子育て" },
+  { pattern: "13_ステップ１行政改革.md", label: "行政改革" },
+  { pattern: "14_ステップ１産業.md", label: "産業政策" },
+  { pattern: "15_ステップ１科学技術.md", label: "科学技術" },
+  { pattern: "16_ステップ１デジタル民主主義.md", label: "デジタル民主主義" },
+
+  // { pattern: "20_ステップ２「変化に対応できるしなやかな仕組みづくり」.md", label: "変化対応" },
+  { pattern: "21_ステップ２教育.md", label: "教育" },
+  { pattern: "22_ステップ２行政改革.md", label: "行政改革" },
+  { pattern: "23_ステップ２経済財政.md", label: "経済財政" },
+
+  // { pattern: "30_ステップ３「長期の成長に大胆に投資する」.md", label: "長期成長" },
+  { pattern: "31_ステップ３子育て.md", label: "子育て" },
+  { pattern: "32_ステップ３教育.md", label: "教育" },
+  { pattern: "33_ステップ３科学技術.md", label: "科学技術" },
+  { pattern: "34_ステップ３産業.md", label: "産業政策" },
+  { pattern: "35_ステップ３エネルギー.md", label: "エネルギー" },
+  { pattern: "36_ステップ３経済財政.md", label: "経済財政" },
+
+  { pattern: "01_チームみらいのビジョン.md", label: "ビジョン" },
+  // { pattern: "02_政策インデックス.md", label: "インデックス" },
+  // { pattern: "40_国政政党成立後100日プラン.md", label: "100日プラン" },
+  { pattern: "50_国政のその他重要分野.md", label: "その他政策" }
+];
```

---

