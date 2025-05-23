#!/usr/bin/env python3

import json
import random
import sys
import time
from pathlib import Path

import dotenv
from content_classifier import ContentClassifier

dotenv.load_dotenv()


def load_pr_data(json_file_path):
    with open(json_file_path, encoding="utf-8") as f:
        pr_data = json.load(f)
    print(f"{len(pr_data)}件のPRデータを読み込みました")
    return pr_data


def extract_unlabeled_prs(pr_data):
    unlabeled_prs = []
    for pr in pr_data:
        if not pr:  # Noneの場合はスキップ
            continue
        if not pr.get("labels"):
            unlabeled_prs.append(pr)

    print(f"{len(unlabeled_prs)}件のラベルなしPRを見つけました")
    return unlabeled_prs


def confidence_to_emoji(confidence):
    if confidence >= 0.8:
        return "🟢自信高い"  # 高信頼度
    elif confidence >= 0.6:
        return "🟡自信あり"  # 中信頼度
    else:
        return "🔴自信なし"  # 低信頼度


def generate_summary(pr, classification):
    title = pr["basic_info"]["title"]
    explanation = classification.get("explanation", "")

    if len(explanation) > 30:
        summary = explanation.split(".")[0]
        if len(summary) > 60:
            summary = summary[:60] + "..."
    else:
        summary = title
        if len(summary) > 60:
            summary = summary[:60] + "..."

    return summary


def main():
    start_time = time.time()

    if len(sys.argv) < 2:
        print("使用方法: python test_classify_improved.py <PRデータのJSONファイルパス>")
        return 1

    json_file_path = sys.argv[1]
    if not Path(json_file_path).exists():
        print(f"エラー: ファイル {json_file_path} が見つかりません")
        return 1

    pr_data = load_pr_data(json_file_path)

    unlabeled_prs = extract_unlabeled_prs(pr_data)

    if len(unlabeled_prs) > 10:
        sample_prs = random.sample(unlabeled_prs, 10)
    else:
        sample_prs = unlabeled_prs

    print(f"ランダムに{len(sample_prs)}件のPRを選択しました")

    try:
        classifier = ContentClassifier()

        print("\n# 「ラベルなし」PRの分類結果\n")

        results = []

        for pr in sample_prs:
            basic = pr["basic_info"]
            pr_number = basic["number"]
            old_title = basic["title"]
            pr_url = basic["html_url"]

            classification = classifier.classify_content(pr)
            category = classification.get("category", "分類不能")
            confidence = classification.get("confidence", 0.0)
            explanation = classification.get("explanation", "")
            digest = classification.get("digest", "")
            title = classification.get("title", "")

            summary = generate_summary(pr, classification)

            confidence_emoji = confidence_to_emoji(confidence)

            results.append(
                {
                    "pr_number": pr_number,
                    "old_title": old_title,
                    "title": title,
                    "digest": digest,
                    "summary": summary,
                    "pr_url": pr_url,
                    "category": category,
                    "confidence": confidence,
                    "confidence_emoji": confidence_emoji,
                    "explanation": explanation,
                }
            )

        for result in results:
            print(f"## {result['title']}\n")
            print(f"- [PR #{result['pr_number']}]({result['pr_url']}) {result['old_title']}")
            print(f"- 要約: {result['digest']}")
            print(f"\n- 提案ラベル: {result['category']} {result['confidence_emoji']}")

            print(f"\n- 提案理由: {result['explanation']}\n")

            print("---\n")

        end_time = time.time()
        elapsed_time = end_time - start_time

        estimated_input_tokens = len(sample_prs) * 2000
        estimated_output_tokens = len(sample_prs) * 1000
        estimated_cost = (estimated_input_tokens / 1000 * 0.005) + (estimated_output_tokens / 1000 * 0.015)

        print("\n## 処理情報")
        print(f"- 処理時間: {elapsed_time:.2f}秒")
        print(f"- 処理件数: {len(sample_prs)}件")
        print(f"- 推定費用: ${estimated_cost:.4f} (非常に大雑把な見積もり)")
        print(f"  - 入力トークン: 約{estimated_input_tokens}トークン")
        print(f"  - 出力トークン: 約{estimated_output_tokens}トークン")

        return 0
    except Exception as e:
        print(f"エラー: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
