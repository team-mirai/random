# pr_section_analyzer_final.py に関するPull Request

生成日時: 2025-05-29 07:24:37

## このファイルに影響するPull Request (1件)

| # | タイトル | 作成者 | 作成日 | 状態 | 変更 |
|---|---------|--------|--------|------|------|
| #1605 | [Add PR section analyzer script to identify which PRs modify the same sections](https://github.com/team-mirai/policy/pull/1605) | devin-ai-integration[bot] | 2025-05-24 | added | +390/-0 |

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

##### pr_section_analyzer_final.py (added, +390/-0)

```diff
@@ -0,0 +1,390 @@
+#!/usr/bin/env python3
+"""
+Script to analyze PRs in the policy repository and extract the specific sections 
+of the manifest that are being modified. This script can identify which PRs modify
+the same sections of the manifest.
+"""
+
+import json
+import os
+import re
+import subprocess
+import sys
+import argparse
+from collections import defaultdict
+
+def run_command(command):
+    """Run a shell command and return the output."""
+    result = subprocess.run(command, shell=True, capture_output=True, text=True)
+    if result.returncode != 0:
+        print(f"Error running command: {command}")
+        print(f"Error: {result.stderr}")
+        return ""
+    return result.stdout.strip()
+
+def get_pr_list(limit=100):
+    """Get a list of PRs from the repository."""
+    command = f"gh pr list --limit {limit} --json number,title,headRefName,state,url"
+    output = run_command(command)
+    try:
+        return json.loads(output)
+    except json.JSONDecodeError:
+        print(f"Error parsing JSON from PR list: {output}")
+        return []
+
+def get_pr_details(pr_number):
+    """Get detailed information about a PR."""
+    command = f"gh pr view {pr_number} --json number,title,headRefName,state,url,body"
+    output = run_command(command)
+    try:
+        return json.loads(output)
+    except json.JSONDecodeError:
+        print(f"Error parsing JSON from PR details: {output}")
+        return {}
+
+def get_pr_files(pr_number):
+    """Get the list of files changed in a PR using GitHub API."""
+    command = f"gh pr view {pr_number} --json files"
+    output = run_command(command)
+    try:
+        data = json.loads(output)
+        files = [file.get('path') for file in data.get('files', [])]
+        print(f"Changed files from GitHub API: {files}")
+        return files
+    except json.JSONDecodeError:
+        print(f"Error parsing JSON from PR files: {output}")
+        return []
+
+def get_file_diff(pr_number, file_path):
+    """Get the diff for a specific file in a PR."""
+    command = f"gh pr view {pr_number} --json headRefName"
+    output = run_command(command)
+    try:
+        data = json.loads(output)
+        branch_name = data.get('headRefName')
+        if not branch_name:
+            print(f"Could not get branch name for PR #{pr_number}")
+            return ""
+        
+        fetch_cmd = f"git fetch origin {branch_name}"
+        run_command(fetch_cmd)
+        
+        diff_cmd = f"git diff main..origin/{branch_name} -- '{file_path}'"
+        return run_command(diff_cmd)
+    except json.JSONDecodeError:
+        print(f"Error parsing JSON for PR branch: {output}")
+        return ""
+
+def extract_markdown_sections(file_path):
+    """Extract the markdown sections from a file with improved Japanese section handling."""
+    if not os.path.exists(file_path):
+        print(f"File not found: {file_path}")
+        return {}
+    
+    with open(file_path, 'r', encoding='utf-8') as f:
+        content = f.read()
+    
+    print(f"Extracting sections from file with {len(content.split('\n'))} lines")
+    
+    headings = []
+    section_content = {}
+    current_section_start = None
+    
+    for i, line in enumerate(content.split('\n')):
+        heading_match = re.match(r'^(#+)\s+(.+)$', line)
+        
+        jp_section_match = None
+        if not heading_match:
+            jp_section_match = re.match(r'^([０-９]+）|\d+）)\s*(.+)$', line)
+        
+        jp_policy_match = None
+        if not heading_match and not jp_section_match:
+            jp_policy_match = re.match(r'^###\s+(現状認識・課題分析|政策概要)$', line)
+        
+        if heading_match:
+            level = len(heading_match.group(1))
+            title = heading_match.group(2).strip()
+            headings.append((i+1, level, title))
+            print(f"Found heading at line {i+1}: {title} (level {level})")
+            
+            if current_section_start is not None:
+                section_content[current_section_start] = (current_section_start, i)
+            current_section_start = i+1
+            
+        elif jp_section_match:
+            level = 2
+            title = jp_section_match.group(0).strip()
+            headings.append((i+1, level, title))
+            print(f"Found JP section at line {i+1}: {title} (level {level})")
+            
+            if current_section_start is not None:
+                section_content[current_section_start] = (current_section_start, i)
+            current_section_start = i+1
+            
+        elif jp_policy_match:
+            level = 3
+            title = jp_policy_match.group(1).strip()
+            headings.append((i+1, level, title))
+            print(f"Found JP policy section at line {i+1}: {title} (level {level})")
+            
+            if current_section_start is not None:
+                section_content[current_section_start] = (current_section_start, i)
+            current_section_start = i+1
+    
+    if current_section_start is not None and len(content.split('\n')) > 0:
+        section_content[current_section_start] = (current_section_start, len(content.split('\n')))
+    
+    sections = {}
+    
+    sorted_headings = sorted(headings, key=lambda x: x[0])
+    
+    for i, (line_num, level, title) in enumerate(sorted_headings):
+        parent_sections = []
+        current_parent_level = 0
+        
+        for j in range(i-1, -1, -1):
+            prev_line, prev_level, prev_title = sorted_headings[j]
+            
+            if prev_level < level and prev_level > current_parent_level:
+                parent_sections.insert(0, prev_title)
+                current_parent_level = prev_level
+                
+                if prev_level == 1:
+                    break
+        
+        section_path = " > ".join(parent_sections + [title])
+        
+        content_range = section_content.get(line_num, (line_num, line_num))
+        
+        sections[line_num] = {
+            "level": level,
+            "title": title,
+            "path": section_path,
+            "parent_sections": parent_sections,
+            "start_line": content_range[0],
+            "end_line": content_range[1]
+        }
+    
+    return sections
+
+def find_section_for_line(sections, line_number):
+    """Find the section that contains a specific line."""
+    for section_line, section_info in sections.items():
+        if section_info["start_line"] <= line_number <= section_info["end_line"]:
+            return section_info
+    
+    section_lines = sorted(sections.keys())
+    for i, section_line in enumerate(section_lines):
+        if section_line > line_number:
+            if i > 0:
+                return sections[section_lines[i-1]]
+            break
+    
+    if section_lines:
+        return sections[section_lines[-1]]
+    
+    return None
+
+def extract_line_numbers_from_diff(diff_text):
+    """Extract line numbers from a diff."""
+    line_numbers = []
+    current_line = None
+    
+    for line in diff_text.split('\n'):
+        if line.startswith('@@'):
+            match = re.search(r'@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@', line)
+            if match:
+                current_line = int(match.group(1))
+                line_count = int(match.group(2)) if match.group(2) else 1
+        elif current_line is not None:
+            if line.startswith('+') and not line.startswith('+++'):
+                line_numbers.append(current_line)
+                current_line += 1
+            elif line.startswith('-'):
+                pass
+            else:
+                current_line += 1
+    
+    return line_numbers
+
+def analyze_pr(pr_number):
+    """Analyze a PR and extract the sections being modified."""
+    pr_details = get_pr_details(pr_number)
+    changed_files = get_pr_files(pr_number)
+    
+    print(f"Analyzing PR #{pr_number}")
+    
+    if not changed_files:
+        print("No changed files found")
+        return None
+    
+    results = []
+    
+    for file_path in changed_files:
+        if not file_path.endswith('.md'):
+            print(f"Skipping non-markdown file: {file_path}")
+            continue
+        
+        print(f"Processing file: {file_path}")
+        full_path = os.path.join(os.getcwd(), file_path)
+        
+        if not os.path.exists(full_path):
+            print(f"Warning: File {full_path} does not exist, skipping")
+            continue
+        
+        file_diff = get_file_diff(pr_number, file_path)
+        
+        if not file_diff:
+            print(f"No diff found for file {file_path}")
+            continue
+        
+        print(f"Found diff for file {file_path}, length: {len(file_diff)}")
+        
+        line_numbers = extract_line_numbers_from_diff(file_diff)
+        
+        if not line_numbers:
+            print(f"No line numbers found in diff for file {file_path}")
+            continue
+        
+        print(f"Affected line numbers: {line_numbers[:10]}...")
+        
+        sections = extract_markdown_sections(full_path)
+        print(f"Found {len(sections)} sections in {file_path}")
+        
+        if len(sections) > 0:
+            print(f"Section titles: {[s['title'] for s in sections.values()][:5]}")
+        
+        affected_sections = set()
+        for line_number in line_numbers:
+            section = find_section_for_line(sections, line_number)
+            if section:
+                print(f"Line {line_number} is in section: {section['title']}")
+                affected_sections.add((section['title'], section['path']))
+        
+        for section_title, section_path in affected_sections:
+            results.append({
+                'pr_number': pr_number,
+                'pr_title': pr_details.get('title', ''),
+                'pr_url': pr_details.get('url', ''),
+                'file': file_path,
+                'section': section_title,
+                'section_path': section_path,
+                'changes': [line for line in file_diff.split('\n') if line.startswith('+') and not line.startswith('+++')]
+            })
+    
+    print(f"Found {len(results)} affected sections")
+    return results
+
+def analyze_all_prs(limit=100):
+    """Analyze all PRs and group them by the sections they modify."""
+    prs = get_pr_list(limit)
+    
+    all_results = []
+    section_to_prs = defaultdict(list)
+    
+    for pr in prs:
+        pr_number = pr['number']
+        print(f"Analyzing PR #{pr_number}: {pr['title']}")
+        
+        results = analyze_pr(pr_number)
+        if results:
+            all_results.extend(results)
+            
+            for result in results:
+                section_key = f"{result['file']}:{result['section_path']}"
+                section_to_prs[section_key].append({
+                    'pr_number': pr_number,
+                    'pr_title': pr['title'],
+                    'pr_url': pr['url']
+                })
+    
+    return all_results, section_to_prs
+
+def generate_report(all_results, section_to_prs):
+    """Generate a report of the analysis results."""
+    report = []
+    
+    report.append("# PRs Grouped by Section\n")
+    
+    for section_key, prs in sorted(section_to_prs.items()):
+        if len(prs) > 1:  # Only show sections with multiple PRs
+            file_path, section_path = section_key.split(':', 1)
+            report.append(f"## {file_path}\n")
+            report.append(f"### {section_path}\n")
+            report.append("PRs modifying this section:\n")
+            
+            for pr in prs:
+                report.append(f"- PR #{pr['pr_number']}: {pr['pr_title']} ({pr['pr_url']})\n")
+            
+            report.append("\n")
+    
+    report.append("# Sections Modified by Each PR\n")
+    
+    pr_to_sections = defaultdict(list)
+    for result in all_results:
+        pr_key = f"{result['pr_number']}:{result['pr_title']}"
+        section_info = {
+            'file': result['file'],
+            'section_path': result['section_path']
+        }
+        pr_to_sections[pr_key].append(section_info)
+    
+    for pr_key, sections in sorted(pr_to_sections.items()):
+        pr_number, pr_title = pr_key.split(':', 1)
+        report.append(f"## PR #{pr_number}: {pr_title}\n")
+        
+        for section in sections:
+            report.append(f"- {section['file']}: {section['section_path']}\n")
+        
+        report.append("\n")
+    
+    return "".join(report)
+
+def main():
+    """Main function with improved command-line interface."""
+    parser = argparse.ArgumentParser(description='Analyze PRs in the policy repository and extract modified sections.')
+    group = parser.add_mutually_exclusive_group(required=True)
+    group.add_argument('--pr', type=str, help='PR number to analyze')
+    group.add_argument('--all', action='store_true', help='Analyze all PRs')
+    parser.add_argument('--limit', type=int, default=100, help='Limit the number of PRs to analyze (default: 100)')
+    parser.add_argument('--output', type=str, help='Output file for the report (default: stdout)')
+    parser.add_argument('--format', choices=['text', 'json'], default='text', help='Output format (default: text)')
+    
+    args = parser.parse_args()
+    
+    if args.pr:
+        results = analyze_pr(args.pr)
+        
+        if results:
+            if args.format == 'json':
+                output = json.dumps(results, indent=2, ensure_ascii=False)
+            else:
+                output = f"\nAnalysis of PR #{args.pr}:\n"
+                for result in results:
+                    output += f"\nFile: {result['file']}\n"
+                    output += f"Section: {result['section_path']}\n"
+                    output += "Changes:\n"
+                    for change in result['changes']:
+                        output += f"  {change}\n"
+        else:
+            output = f"No markdown sections found in PR #{args.pr}"
+    else:  # --all
+        all_results, section_to_prs = analyze_all_prs(args.limit)
+        
+        if args.format == 'json':
+            output = json.dumps({
+                'results': all_results,
+                'section_to_prs': {k: v for k, v in section_to_prs.items()}
+            }, indent=2, ensure_ascii=False)
+        else:
+            output = generate_report(all_results, section_to_prs)
+    
+    if args.output:
+        with open(args.output, 'w', encoding='utf-8') as f:
+            f.write(output)
+        print(f"Report written to {args.output}")
+    else:
+        print(output)
+
+if __name__ == "__main__":
+    main()
```

---

