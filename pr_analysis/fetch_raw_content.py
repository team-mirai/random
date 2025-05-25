#!/usr/bin/env python3
"""
Script to fetch raw content from GitHub URLs and analyze PR sections.
"""

import argparse
import json
import os
import re
import requests
from collections import defaultdict
from datetime import datetime

def get_label_file_patterns():
    """Get mapping of labels to file patterns based on config.ts"""
    return {
        "教育": ["11_ステップ１教育", "21_ステップ２教育", "32_ステップ３教育"],
        "子育て": ["12_ステップ１子育て", "31_ステップ３子育て"],
        "行政改革": ["13_ステップ１行政改革", "22_ステップ２行政改革"],
        "産業政策": ["14_ステップ１産業", "34_ステップ３産業"],
        "科学技術": ["15_ステップ１科学技術", "33_ステップ３科学技術"],
        "デジタル民主主義": ["16_ステップ１デジタル民主主義"],
        "医療": ["17_ステップ１医療", "24_ステップ２医療"],
        "経済財政": ["23_ステップ２経済財政", "36_ステップ３経済財政"],
        "エネルギー": ["35_ステップ３エネルギー"],
        "ビジョン": ["01_チームみらいのビジョン"],
        "その他政策": ["50_国政のその他重要分野"]
    }

def load_pr_data(file_path='all_pr_data.json'):
    """Load PR data from JSON file."""
    print(f"Loading PR data from {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            all_prs = json.load(f)
        print(f"Loaded {len(all_prs)} PRs")
        return all_prs
    except Exception as e:
        print(f"Error loading PR data: {e}")
        return []

def get_labeled_prs(all_prs, label):
    """Get all PRs with the specified label."""
    labeled_prs = []
    for pr in all_prs:
        pr_labels = [l.get('name') for l in pr.get('labels', [])]
        if label in pr_labels:
            labeled_prs.append(pr)
    
    print(f"Found {len(labeled_prs)} PRs with label '{label}'")
    return labeled_prs

def fetch_raw_content(url):
    """Fetch raw content from GitHub URL."""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to fetch content from {url}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching content from {url}: {e}")
        return None

def extract_markdown_sections(content):
    """Extract markdown sections from content."""
    if not content:
        return {}
    
    headings = []
    section_content = {}
    current_section_start = None
    
    for i, line in enumerate(content.split('\n')):
        heading_match = re.match(r'^(#+)\s+(.+)$', line)
        
        jp_section_match = None
        if not heading_match:
            jp_section_match = re.match(r'^([０-９]+）|\d+）)\s*(.+)$', line)
        
        jp_policy_match = None
        if not heading_match and not jp_section_match:
            jp_policy_match = re.match(r'^###\s+(現状認識・課題分析|政策概要)$', line)
        
        if heading_match or jp_section_match or jp_policy_match:
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
            elif jp_section_match:
                level = 2
                title = jp_section_match.group(0).strip()
            else:
                level = 3
                title = jp_policy_match.group(1).strip()
                
            headings.append((i+1, level, title))
            
            if current_section_start is not None:
                section_content[current_section_start] = (current_section_start, i)
            current_section_start = i+1
    
    if current_section_start is not None:
        section_content[current_section_start] = (current_section_start, len(content.split('\n')))
    
    section_hierarchy = {}
    section_path = []
    
    for i, (line_num, level, title) in enumerate(headings):
        while section_path and section_path[-1][1] >= level:
            section_path.pop()
        
        section_path.append((title, level))
        
        path_str = " > ".join([t for t, _ in section_path])
        section_hierarchy[line_num] = path_str
    
    return section_hierarchy

def find_section_for_line(section_hierarchy, line_num):
    """Find the section for a given line number."""
    section_starts = sorted(section_hierarchy.keys())
    
    for i in range(len(section_starts) - 1):
        if section_starts[i] <= line_num < section_starts[i + 1]:
            return section_hierarchy[section_starts[i]]
    
    if section_starts and line_num >= section_starts[-1]:
        return section_hierarchy[section_starts[-1]]
    
    return "Unknown section"

def extract_line_numbers_from_patch(patch):
    """Extract line numbers from patch."""
    if not patch:
        return []
    
    line_numbers = []
    current_line = None
    
    for line in patch.split('\n'):
        hunk_match = re.match(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@', line)
        if hunk_match:
            current_line = int(hunk_match.group(1))
            continue
        
        if current_line is not None:
            if line.startswith('+') and not line.startswith('+++'):
                line_numbers.append(current_line)
            
            if not line.startswith('-'):
                current_line += 1
    
    return line_numbers

def analyze_pr(pr, label, content_cache=None):
    """Analyze a PR and extract the sections it modifies for the given label."""
    if content_cache is None:
        content_cache = {}
    
    basic_info = pr.get('basic_info', {})
    pr_number = basic_info.get('number')
    if not pr_number:
        print("PR number not found")
        return None
    
    pr_files = pr.get('files', [])
    if not pr_files:
        print(f"No files found for PR #{pr_number}")
        return None
    
    file_patterns = get_label_file_patterns().get(label, [])
    if not file_patterns:
        print(f"No file patterns found for label: {label}")
        return None
    
    label_files = []
    for file_info in pr_files:
        filename = file_info.get('filename', '')
        if filename.endswith('.md') and any(filename.startswith(pattern) for pattern in file_patterns):
            label_files.append(file_info)
    
    if not label_files:
        print(f"No {label} files found for PR #{pr_number}")
        return None
    
    results = []
    
    for file_info in label_files:
        filename = file_info.get('filename', '')
        print(f"Processing file: {filename}")
        
        if filename in content_cache:
            file_content = content_cache[filename]
        else:
            raw_url = file_info.get('raw_url')
            if raw_url:
                file_content = fetch_raw_content(raw_url)
                if file_content:
                    content_cache[filename] = file_content
            else:
                file_content = None
        
        if not file_content:
            print(f"No content found for file: {filename}")
            continue
        
        section_hierarchy = extract_markdown_sections(file_content)
        if not section_hierarchy:
            print(f"No sections found in file: {filename}")
            continue
        
        patch = file_info.get('patch')
        if not patch:
            print(f"No patch found for file: {filename}")
            continue
        
        modified_lines = extract_line_numbers_from_patch(patch)
        if not modified_lines:
            print(f"No modified lines found for file: {filename}")
            continue
        
        affected_sections = set()
        for line_num in modified_lines:
            section = find_section_for_line(section_hierarchy, line_num)
            affected_sections.add(section)
        
        for section in affected_sections:
            results.append({
                'pr_number': pr_number,
                'pr_title': basic_info.get('title', ''),
                'pr_url': basic_info.get('html_url', ''),
                'file': filename,
                'section_path': section
            })
    
    print(f"Found {len(results)} affected sections")
    return results

def generate_markdown_report(pr_analyses, label):
    """Generate a Markdown report from the PR analyses for the specified label."""
    if not pr_analyses:
        return f"# {label}関連PRのセクション分析\n\n分析対象のPRが見つかりませんでした。"
    
    sections_to_prs = defaultdict(list)
    for pr in pr_analyses:
        for result in pr.get("results", []):
            section_key = f"{result['file']}: {result['section_path']}"
            sections_to_prs[section_key].append({
                "number": result['pr_number'],
                "title": result['pr_title'],
                "url": result['pr_url']
            })
    
    report = f"# {label}関連PRのセクション分析\n\n"
    report += f"分析日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    report += "## セクション別PR一覧\n\n"
    for section_key, prs in sorted(sections_to_prs.items()):
        file_path, section_path = section_key.split(': ', 1)
        report += f"### {file_path}\n"
        report += f"#### {section_path}\n"
        report += "このセクションを変更するPR:\n"
        for pr in prs:
            report += f"- PR #{pr['number']}: [{pr['title']}]({pr['url']})\n"
        report += "\n"
    
    report += "## PR別変更セクション一覧\n\n"
    pr_to_sections = defaultdict(list)
    for pr in pr_analyses:
        for result in pr.get("results", []):
            pr_key = f"PR #{result['pr_number']}: {result['pr_title']}"
            pr_url = result['pr_url']
            section_key = f"{result['file']}: {result['section_path']}"
            pr_to_sections[(pr_key, pr_url)].append(section_key)
    
    for (pr_key, pr_url), sections in sorted(pr_to_sections.items()):
        report += f"### [{pr_key}]({pr_url})\n"
        for section in sorted(sections):
            file_path, section_path = section.split(': ', 1)
            report += f"- {file_path}: {section_path}\n"
        report += "\n"
    
    return report

def main():
    parser = argparse.ArgumentParser(description="Fetch raw content and analyze PR sections")
    parser.add_argument("--label", default="教育", help="Label to analyze (default: 教育)")
    parser.add_argument("--output-dir", default="section_reports", help="Output directory for reports")
    parser.add_argument("--limit", type=int, default=5, help="Limit the number of PRs to analyze")
    parser.add_argument("--all-labels", action="store_true", help="Analyze all labels")
    parser.add_argument("--summary", action="store_true", help="Generate a summary report")
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    all_prs = load_pr_data()
    if not all_prs:
        print("No PR data found")
        return
    
    if args.all_labels:
        labels = get_label_file_patterns().keys()
    else:
        labels = [args.label]
    
    label_summaries = {}
    content_cache = {}  # Cache for file content to avoid duplicate fetches
    
    for label in labels:
        print(f"\n{'='*60}")
        print(f"Processing label: {label}")
        print(f"{'='*60}")
        
        labeled_prs = get_labeled_prs(all_prs, label)
        if not labeled_prs:
            label_summaries[label] = {"pr_count": 0, "section_count": 0}
            continue
        
        labeled_prs = labeled_prs[:args.limit]
        
        pr_analyses = []
        total_sections = 0
        for pr in labeled_prs:
            basic_info = pr.get('basic_info', {})
            pr_number = basic_info.get('number')
            print(f"\nAnalyzing PR #{pr_number}: {basic_info.get('title')}")
            results = analyze_pr(pr, label, content_cache)
            if results:
                total_sections += len(results)
                pr_analyses.append({
                    "pr_number": pr_number,
                    "pr_title": basic_info.get('title'),
                    "pr_url": basic_info.get('html_url'),
                    "results": results
                })
        
        label_summaries[label] = {
            "pr_count": len(pr_analyses),
            "section_count": total_sections
        }
        
        report = generate_markdown_report(pr_analyses, label)
        output_file = os.path.join(args.output_dir, f"{label}_section_report.md")
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"Report for '{label}' written to {output_file}")
    
    if args.summary or args.all_labels:
        generate_summary_report(label_summaries, args.output_dir)

def generate_summary_report(label_summaries, output_dir):
    """Generate a summary report of all labels."""
    report = "# マニフェスト政策ラベル別セクション分析サマリー\n\n"
    report += f"分析日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    report += "| ラベル | 分析PR数 | 変更セクション数 |\n"
    report += "|--------|----------|----------------|\n"
    
    total_prs = 0
    total_sections = 0
    
    for label, stats in sorted(label_summaries.items()):
        pr_count = stats["pr_count"]
        section_count = stats["section_count"]
        total_prs += pr_count
        total_sections += section_count
        report += f"| {label} | {pr_count} | {section_count} |\n"
    
    report += f"| **合計** | **{total_prs}** | **{total_sections}** |\n\n"
    
    report += "## 詳細レポートへのリンク\n\n"
    for label in sorted(label_summaries.keys()):
        report += f"- [{label}](./{label}_section_report.md)\n"
    
    output_file = os.path.join(output_dir, "section_analysis_summary.md")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"Summary report written to {output_file}")

if __name__ == "__main__":
    main()
