#!/usr/bin/env python3

import argparse
import json
import os
import random
from collections import defaultdict
from pathlib import Path

from content_classifier import ContentClassifier
from tqdm import tqdm


def load_pr_data(json_file_path):
    """PRデータをJSONファイルから読み込む"""
    with open(json_file_path, encoding='utf-8') as f:
        pr_data = json.load(f)
    print(f"{len(pr_data)}件のPRデータを読み込みました")
    return pr_data

def group_prs_by_label(pr_data):
    """PRをラベルごとにグループ化する"""
    label_to_prs = defaultdict(list)
    
    for pr in pr_data:
        if not pr:  # Noneの場合はスキップ
            continue
        
        has_labels = False
        
        if pr.get('labels'):
            has_labels = True
            for label in pr.get('labels', []):
                label_name = label.get('name')
                if label_name:
                    label_to_prs[label_name].append(pr)
        
        if 'basic_info' in pr and pr['basic_info'].get('labels'):
            has_labels = True
            for label in pr['basic_info']['labels']:
                label_name = label.get('name')
                if label_name:
                    if pr not in label_to_prs[label_name]:
                        label_to_prs[label_name].append(pr)
        
        if not has_labels:
            label_to_prs['ラベルなし'].append(pr)
    
    return label_to_prs

def generate_label_markdown(label_name, prs, output_dir):
    """特定のラベルに関連するPRのMarkdownを生成する"""
    output_path = os.path.join(output_dir, f"label_{label_name}.md")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# ラベル「{label_name}」のPull Request一覧\n\n")
        f.write(f"合計: {len(prs)}件のPR\n\n")
        
        f.write("## PR一覧\n\n")
        f.write("| # | タイトル | 作成者 | 状態 | 作成日 | 更新日 |\n")
        f.write("|---|---------|--------|------|--------|--------|\n")
        
        for pr in sorted(prs, key=lambda x: x['basic_info']['number']):
            basic = pr['basic_info']
            pr_number = basic['number']
            title = basic['title']
            user = basic['user']['login']
            state = basic['state']
            created_at = basic['created_at'].split('T')[0]
            updated_at = basic['updated_at'].split('T')[0]
            
            f.write(f"| #{pr_number} | [{title}]({basic['html_url']}) | {user} | {state} | {created_at} | {updated_at} |\n")
        
        f.write("\n## PR詳細\n\n")
        
        for pr in sorted(prs, key=lambda x: x['basic_info']['number']):
            basic = pr['basic_info']
            pr_number = basic['number']
            title = basic['title']
            
            f.write(f"### #{pr_number}: {title}\n\n")
            
            if basic.get('body'):
                f.write("#### 説明\n\n")
                f.write(f"{basic['body']}\n\n")
            
            if pr.get('files'):
                f.write("#### 変更ファイル\n\n")
                for file in pr['files']:
                    f.write(f"- {file['filename']}\n")
                f.write("\n")
            
            f.write("---\n\n")
    
    print(f"ラベル「{label_name}」のMarkdownを {output_path} に保存しました")
    return output_path

def generate_label_index(label_to_prs, output_dir):
    """ラベルごとのPR数とリンクを含むインデックスMarkdownを生成する"""
    output_path = os.path.join(output_dir, "labels_index.md")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# PRラベル別インデックス\n\n")
        f.write("| ラベル | PR数 |\n")
        f.write("|--------|------|\n")
        
        for label_name, prs in sorted(label_to_prs.items(), key=lambda x: len(x[1]), reverse=True):
            label_file = f"label_{label_name}.md"
            f.write(f"| [{label_name}]({label_file}) | {len(prs)} |\n")
    
    print(f"ラベルインデックスを {output_path} に保存しました")
    return output_path

def classify_unlabeled_prs(unlabeled_prs, sample_size=0, confidence_threshold=0.7):
    """ラベルなしのPRを内容に基づいて既存のカテゴリに分類する"""
    if sample_size > 0 and sample_size < len(unlabeled_prs):
        print(f"{len(unlabeled_prs)}件のラベルなしPRから{sample_size}件をランダムに選択します")
        prs_to_classify = random.sample(unlabeled_prs, sample_size)
    else:
        print(f"{len(unlabeled_prs)}件のラベルなしPRを分類します")
        prs_to_classify = unlabeled_prs
    
    try:
        classifier = ContentClassifier()
        
        classified_prs = {}
        still_unlabeled = []
        
        for pr in tqdm(prs_to_classify, desc="PRの分類"):
            classification = classifier.classify_content(pr)
            category = classification.get("category", "分類不能")
            confidence = classification.get("confidence", 0.0)
            
            if category == "分類不能" or confidence < confidence_threshold:
                still_unlabeled.append(pr)
                continue
                
            if category not in classified_prs:
                classified_prs[category] = []
            classified_prs[category].append(pr)
            
        return classified_prs, still_unlabeled
    except Exception as e:
        print(f"分類中にエラーが発生しました: {e}")
        return {}, unlabeled_prs

def main():
    parser = argparse.ArgumentParser(description='PRデータをラベルごとにグループ化してMarkdownを生成する')
    parser.add_argument('--input', default='all_pr_data.json', help='入力JSONファイルのパス')
    parser.add_argument('--output-dir', default='label_reports', help='出力ディレクトリ')
    parser.add_argument('--classify-unlabeled', action='store_true', help='ラベルなしのPRを既存のカテゴリに分類する')
    parser.add_argument('--sample', type=int, default=0, help='ラベルなしのPRからサンプリングする数（0は全て）')
    parser.add_argument('--confidence-threshold', type=float, default=0.7, help='分類の信頼度のしきい値（0.0〜1.0）')
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"エラー: 入力ファイル {args.input} が見つかりません")
        return 1
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    pr_data = load_pr_data(input_path)
    
    label_to_prs = group_prs_by_label(pr_data)
    
    if args.classify_unlabeled and 'ラベルなし' in label_to_prs:
        unlabeled_prs = label_to_prs.pop('ラベルなし')
        classified_prs, still_unlabeled = classify_unlabeled_prs(
            unlabeled_prs, 
            sample_size=args.sample,
            confidence_threshold=args.confidence_threshold
        )
        
        for category, prs in classified_prs.items():
            if category not in label_to_prs:
                label_to_prs[category] = []
            label_to_prs[category].extend(prs)
            
        if still_unlabeled:
            label_to_prs['ラベルなし'] = still_unlabeled
            
        print("\n分類結果の概要:")
        print(f"- 元のラベルなしPR: {len(unlabeled_prs)}件")
        print(f"- 自動分類されたPR: {sum(len(prs) for prs in classified_prs.values())}件")
        print(f"- 分類できなかったPR: {len(still_unlabeled)}件")
        
        for category, prs in sorted(classified_prs.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"  - {category}: {len(prs)}件")
            
        if args.sample > 0:
            print("\n詳細な分類結果:")
            for category, prs in sorted(classified_prs.items(), key=lambda x: len(x[1]), reverse=True):
                print(f"\n== {category} ==")
                for pr in prs:
                    print(f"- #{pr['basic_info']['number']} {pr['basic_info']['title']}")
                    
        classification_summary_path = os.path.join(output_dir, "unlabeled_classification_summary.md")
        
        with open(classification_summary_path, 'w', encoding='utf-8') as f:
            f.write("# ラベルなしPRの分類結果\n\n")
            f.write(f"元のラベルなしPR: {len(unlabeled_prs)}件\n")
            f.write(f"自動分類されたPR: {sum(len(prs) for prs in classified_prs.values())}件\n")
            f.write(f"分類できなかったPR: {len(still_unlabeled)}件\n\n")
            
            f.write("## カテゴリ別の分類結果\n\n")
            f.write("| カテゴリ | PR数 |\n")
            f.write("|---------|------|\n")
            
            for category, prs in sorted(classified_prs.items(), key=lambda x: len(x[1]), reverse=True):
                f.write(f"| {category} | {len(prs)} |\n")
                
            for category, prs in sorted(classified_prs.items(), key=lambda x: len(x[1]), reverse=True):
                f.write(f"\n### {category}\n\n")
                for pr in prs:
                    f.write(f"- [#{pr['basic_info']['number']} {pr['basic_info']['title']}]({pr['basic_info']['html_url']})\n")
                
        print(f"分類結果の要約を {classification_summary_path} に保存しました")
    
    for label_name, prs in label_to_prs.items():
        generate_label_markdown(label_name, prs, output_dir)
    
    generate_label_index(label_to_prs, output_dir)
    
    print(f"全てのラベル ({len(label_to_prs)} 種類) のMarkdownを生成しました")
    return 0

if __name__ == "__main__":
    exit(main())
