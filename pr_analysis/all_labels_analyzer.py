#!/usr/bin/env python3
"""
Script to analyze PRs for all policy labels and generate section analysis reports.
"""

import argparse
import json
import os
from datetime import datetime

from label_section_analyzer import (
    analyze_pr,
    generate_markdown_report,
    get_label_file_patterns,
    get_labeled_prs,
)


def main():
    parser = argparse.ArgumentParser(description="Analyze PRs for all policy labels")
    parser.add_argument(
        "--output-dir", default="label_reports", help="Output directory for reports"
    )
    parser.add_argument("--limit", type=int, default=20, help="Limit PRs per label")
    parser.add_argument(
        "--labels", nargs="*", help="Specific labels to process (default: all)"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--summary", action="store_true", help="Generate a summary report of all labels"
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    all_labels = list(get_label_file_patterns().keys())
    labels_to_process = args.labels if args.labels else all_labels

    label_summaries = {}

    for label in labels_to_process:
        print(f"\n{'='*60}")
        print(f"Processing label: {label}")
        print(f"{'='*60}")

        labeled_prs = get_labeled_prs(label)
        print(f"Found {len(labeled_prs)} PRs with label '{label}'")

        if not labeled_prs:
            label_summaries[label] = {"pr_count": 0, "section_count": 0}
            continue

        labeled_prs = labeled_prs[: args.limit]

        pr_analyses = []
        total_sections = 0
        for pr in labeled_prs:
            pr_number = pr["number"]
            print(f"\nAnalyzing PR #{pr_number}: {pr['title']}")
            results = analyze_pr(pr_number, label)
            if results:
                total_sections += len(results)
                pr_analyses.append(
                    {
                        "pr_number": pr_number,
                        "pr_title": pr["title"],
                        "pr_url": pr["url"],
                        "results": results,
                    }
                )

        label_summaries[label] = {
            "pr_count": len(pr_analyses),
            "section_count": total_sections,
        }

        if args.format == "json":
            output = json.dumps(pr_analyses, ensure_ascii=False, indent=2)
            output_file = os.path.join(args.output_dir, f"{label}_pr_report.json")
        else:
            output = generate_markdown_report(pr_analyses, label)
            output_file = os.path.join(args.output_dir, f"{label}_pr_report.md")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)

        print(f"Report for '{label}' written to {output_file}")

    if args.summary:
        generate_summary_report(label_summaries, args.output_dir)


def generate_summary_report(label_summaries, output_dir):
    """Generate a summary report of all labels."""
    report = "# マニフェスト政策ラベル別PR分析サマリー\n\n"
    report += f"分析日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    report += "| ラベル | PR数 | 変更セクション数 |\n"
    report += "|--------|------|----------------|\n"

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
        report += f"- [{label}](./{label}_pr_report.md)\n"

    output_file = os.path.join(output_dir, "all_labels_summary.md")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Summary report written to {output_file}")


if __name__ == "__main__":
    main()
