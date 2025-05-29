# tools/tsconfig.json に関するPull Request

生成日時: 2025-05-29 07:24:37

## このファイルに影響するPull Request (1件)

| # | タイトル | 作成者 | 作成日 | 状態 | 変更 |
|---|---------|--------|--------|------|------|
| #1211 | [PR自動ラベル付けバッチの追加](https://github.com/team-mirai/policy/pull/1211) | devin-ai-integration[bot] | 2025-05-19 | added | +15/-0 |

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

##### tools/tsconfig.json (added, +15/-0)

```diff
@@ -0,0 +1,15 @@
+{
+  "compilerOptions": {
+    "target": "es2022",
+    "module": "commonjs",
+    "outDir": "./dist",
+    "rootDir": "./src",
+    "strict": true,
+    "esModuleInterop": true,
+    "skipLibCheck": true,
+    "forceConsistentCasingInFileNames": true,
+    "resolveJsonModule": true
+  },
+  "include": ["src/**/*"],
+  "exclude": ["node_modules", "dist"]
+}
```

---

