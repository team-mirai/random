# education_pr_report_final.md に関するPull Request

生成日時: 2025-05-29 07:24:37

## このファイルに影響するPull Request (1件)

| # | タイトル | 作成者 | 作成日 | 状態 | 変更 |
|---|---------|--------|--------|------|------|
| #1605 | [Add PR section analyzer script to identify which PRs modify the same sections](https://github.com/team-mirai/policy/pull/1605) | devin-ai-integration[bot] | 2025-05-24 | added | +88/-0 |

## 各Pull Requestの詳細

### #1605: Add PR section analyzer script to identify which PRs modify the same sections

- **URL**: https://github.com/team-mirai/policy/pull/1605
- **作成者**: devin-ai-integration[bot]
- **作成日時**: 2025-05-24 18:45:15
- **ブランチ**: devin/1748111368-pr-section-analyzer → main

#### Issue内容

# PR Section Analyzer and Education PR Analyzer

This PR adds scripts to analyze pull requests in the policy repository and extract the specific sections of the manifest that are being modified. The scripts can identify which PRs modify the same sections of the manifest, making it easier to track related changes.

## Features

- Extracts markdown section hierarchies from policy documents
- Identifies which sections are modified by each PR
- Groups PRs by the sections they modify
- Handles Japanese section formatting (ステップ１, ステップ２, etc.)
- Works without relying on LLM technology
- Supports both single PR analysis and batch processing
- Outputs results in text or JSON format

## Implementation Details

The scripts use regex patterns to identify markdown headings and Japanese section numbering patterns. They build a section hierarchy tree and map line numbers from PR diffs to the corresponding sections.

Two main scripts are included:
- `pr_section_analyzer_final.py`: Analyzes any PR to identify modified sections
- `education_pr_analyzer.py`: Specifically analyzes PRs with the education label ("教育")

## Usage

### PR Section Analyzer

```bash
# Analyze a specific PR
python pr_section_analyzer_final.py --pr 1533

# Analyze all PRs (limited to 100 by default)
python pr_section_analyzer_final.py --all

# Analyze all PRs with a custom limit
python pr_section_analyzer_final.py --all --limit 50

# Output results in JSON format
python pr_section_analyzer_final.py --pr 1533 --format json

# Save results to a file
python pr_section_analyzer_final.py --all --output report.txt
```

### Education PR Analyzer

```bash
# Analyze education-labeled PRs (limited to 20 by default)
python education_pr_analyzer.py

# Analyze with a custom limit
python education_pr_analyzer.py --limit 10

# Save results to a file
python education_pr_analyzer.py --output education_report.md
```

## Example Output

The education PR analyzer generates a comprehensive report showing:

1. Which PRs modify the same sections:

```markdown
### 11_ステップ１教育.md
#### ４）貧困世帯の子どもたち・保護者の皆様を支援するため、データとAIを駆使し、プッシュ型の支援を実現します > 現状認識・課題分析
このセクションを変更するPR:
- PR #1462: [SAISにおける科学技術コンテスト参加支援の明記](https://github.com/team-mirai/policy/pull/1462)
- PR #1460: [教育政策における個別最適化とプライバシー保護の強化（匿名ユーザー提案）](https://github.com/team-mirai/policy/pull/1460)
```

2. Which sections are modified by each PR:

```markdown
### PR #1335: 教育政策の改善案：AI家庭教師の対象拡大とプッシュ型支援の強化（すださんご提案）
- 11_ステップ１教育.md: １．教育 > ビジョン
- 11_ステップ１教育.md: ４）貧困世帯の子どもたち・保護者の皆様を支援するため、データとAIを駆使し、プッシュ型の支援を実現します > 現状認識・課題分析
- 11_ステップ１教育.md: １）すべての子どもに「専属のAI家庭教師」を届けます > 現状認識・課題分析
```

A sample report is included in the PR: `education_pr_report_final.md`

## Link to Devin run
https://app.devin.ai/sessions/4d02a46b92954a4d8978a5f005ddc511

Requested by: NISHIO Hirokazu (nishio.hirokazu@gmail.com)


#### 変更差分

##### education_pr_report_final.md (added, +88/-0)

```diff
@@ -0,0 +1,88 @@
+# 教育関連PRの分析
+
+分析日時: 2025-05-24 19:13:06
+
+## セクション別PR一覧
+
+### 32_ステップ３教育.md
+#### ３）子どもたちの好奇心と「はじめる力」を育むための教育に投資します > 現状認識・課題分析
+このセクションを変更するPR:
+- PR #1475: [政策案「２．教育」への子どもの権利尊重に関する新規提案 (IR)](https://github.com/team-mirai/policy/pull/1475)
+- PR #1307: [公設民営型施設の事例記述を最新情報に基づき更新](https://github.com/team-mirai/policy/pull/1307)
+
+### 11_ステップ１教育.md
+#### ４）貧困世帯の子どもたち・保護者の皆様を支援するため、データとAIを駆使し、プッシュ型の支援を実現します > 現状認識・課題分析
+このセクションを変更するPR:
+- PR #1462: [SAISにおける科学技術コンテスト参加支援の明記](https://github.com/team-mirai/policy/pull/1462)
+- PR #1460: [教育政策における個別最適化とプライバシー保護の強化（匿名ユーザー提案）](https://github.com/team-mirai/policy/pull/1460)
+- PR #1431: [教育方針改善：専科制導入と教員の役割分担によるAI活用促進と働き方改革](https://github.com/team-mirai/policy/pull/1431)
+- PR #1385: [mayabreaさん提案：小学校における生成AI利用の安全技術要件を強化](https://github.com/team-mirai/policy/pull/1385)
+- PR #1383: [教育政策案の改善：既存教育アプリの迅速な導入による学習機会の拡充（Himawaruwaruさん提案）](https://github.com/team-mirai/policy/pull/1383)
+- PR #1338: [教員の働き方改革に関する記述を更新（千葉さん提案）](https://github.com/team-mirai/policy/pull/1338)
+- PR #1335: [教育政策の改善案：AI家庭教師の対象拡大とプッシュ型支援の強化（すださんご提案）](https://github.com/team-mirai/policy/pull/1335)
+- PR #1316: [ムライ氏提案：実践的スキル育成と社会ニーズを反映した教育へのAI活用強化](https://github.com/team-mirai/policy/pull/1316)
+
+### 11_ステップ１教育.md
+#### １．教育 > ビジョン
+このセクションを変更するPR:
+- PR #1460: [教育政策における個別最適化とプライバシー保護の強化（匿名ユーザー提案）](https://github.com/team-mirai/policy/pull/1460)
+- PR #1335: [教育政策の改善案：AI家庭教師の対象拡大とプッシュ型支援の強化（すださんご提案）](https://github.com/team-mirai/policy/pull/1335)
+- PR #1316: [ムライ氏提案：実践的スキル育成と社会ニーズを反映した教育へのAI活用強化](https://github.com/team-mirai/policy/pull/1316)
+
+### 11_ステップ１教育.md
+#### １）すべての子どもに「専属のAI家庭教師」を届けます > 現状認識・課題分析
+このセクションを変更するPR:
+- PR #1431: [教育方針改善：専科制導入と教員の役割分担によるAI活用促進と働き方改革](https://github.com/team-mirai/policy/pull/1431)
+- PR #1383: [教育政策案の改善：既存教育アプリの迅速な導入による学習機会の拡充（Himawaruwaruさん提案）](https://github.com/team-mirai/policy/pull/1383)
+- PR #1335: [教育政策の改善案：AI家庭教師の対象拡大とプッシュ型支援の強化（すださんご提案）](https://github.com/team-mirai/policy/pull/1335)
+
+### 11_ステップ１教育.md
+#### ３）：AI＆ITによる教員の働き方改革を進める > 現状認識・課題分析
+このセクションを変更するPR:
+- PR #1431: [教育方針改善：専科制導入と教員の役割分担によるAI活用促進と働き方改革](https://github.com/team-mirai/policy/pull/1431)
+- PR #1338: [教員の働き方改革に関する記述を更新（千葉さん提案）](https://github.com/team-mirai/policy/pull/1338)
+
+## PR別変更セクション一覧
+
+### PR #1307: 公設民営型施設の事例記述を最新情報に基づき更新
+- 32_ステップ３教育.md: ３）子どもたちの好奇心と「はじめる力」を育むための教育に投資します > 現状認識・課題分析
+
+### PR #1316: ムライ氏提案：実践的スキル育成と社会ニーズを反映した教育へのAI活用強化
+- 11_ステップ１教育.md: １．教育 > ビジョン
+- 11_ステップ１教育.md: ４）貧困世帯の子どもたち・保護者の皆様を支援するため、データとAIを駆使し、プッシュ型の支援を実現します > 現状認識・課題分析
+
+### PR #1335: 教育政策の改善案：AI家庭教師の対象拡大とプッシュ型支援の強化（すださんご提案）
+- 11_ステップ１教育.md: １．教育 > ビジョン
+- 11_ステップ１教育.md: ４）貧困世帯の子どもたち・保護者の皆様を支援するため、データとAIを駆使し、プッシュ型の支援を実現します > 現状認識・課題分析
+- 11_ステップ１教育.md: １）すべての子どもに「専属のAI家庭教師」を届けます > 現状認識・課題分析
+- 11_ステップ１教育.md: １．教育 > １）すべての子どもに「専属のAI家庭教師」を届けます
+
+### PR #1338: 教員の働き方改革に関する記述を更新（千葉さん提案）
+- 11_ステップ１教育.md: ４）貧困世帯の子どもたち・保護者の皆様を支援するため、データとAIを駆使し、プッシュ型の支援を実現します > 現状認識・課題分析
+- 11_ステップ１教育.md: ３）：AI＆ITによる教員の働き方改革を進める > 現状認識・課題分析
+
+### PR #1383: 教育政策案の改善：既存教育アプリの迅速な導入による学習機会の拡充（Himawaruwaruさん提案）
+- 11_ステップ１教育.md: １）すべての子どもに「専属のAI家庭教師」を届けます > 現状認識・課題分析
+- 11_ステップ１教育.md: ４）貧困世帯の子どもたち・保護者の皆様を支援するため、データとAIを駆使し、プッシュ型の支援を実現します > 現状認識・課題分析
+
+### PR #1385: mayabreaさん提案：小学校における生成AI利用の安全技術要件を強化
+- 11_ステップ１教育.md: ２）子どものAIリテラシーを育み、AIと共生する未来を切り拓きます > 現状認識・課題分析
+- 11_ステップ１教育.md: ４）貧困世帯の子どもたち・保護者の皆様を支援するため、データとAIを駆使し、プッシュ型の支援を実現します > 現状認識・課題分析
+
+### PR #1431: 教育方針改善：専科制導入と教員の役割分担によるAI活用促進と働き方改革
+- 11_ステップ１教育.md: １）すべての子どもに「専属のAI家庭教師」を届けます > 現状認識・課題分析
+- 11_ステップ１教育.md: ３）：AI＆ITによる教員の働き方改革を進める > 現状認識・課題分析
+- 11_ステップ１教育.md: ４）貧困世帯の子どもたち・保護者の皆様を支援するため、データとAIを駆使し、プッシュ型の支援を実現します > 現状認識・課題分析
+
+### PR #1460: 教育政策における個別最適化とプライバシー保護の強化（匿名ユーザー提案）
+- 11_ステップ１教育.md: １．教育 > ビジョン
+- 11_ステップ１教育.md: ４）貧困世帯の子どもたち・保護者の皆様を支援するため、データとAIを駆使し、プッシュ型の支援を実現します > 現状認識・課題分析
+
+### PR #1462: SAISにおける科学技術コンテスト参加支援の明記
+- 11_ステップ１教育.md: ４）貧困世帯の子どもたち・保護者の皆様を支援するため、データとAIを駆使し、プッシュ型の支援を実現します > 現状認識・課題分析
+- 11_ステップ１教育.md: １．教育 > ３）：AI＆ITによる教員の働き方改革を進める
+
+### PR #1475: 政策案「２．教育」への子どもの権利尊重に関する新規提案 (IR)
+- 32_ステップ３教育.md: ３）子どもたちの好奇心と「はじめる力」を育むための教育に投資します > 現状認識・課題分析
+- 32_ステップ３教育.md: １）政府全体で、教育への投資予算を確保します > 現状認識・課題分析
+
```

---

