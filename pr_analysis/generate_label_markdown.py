#!/usr/bin/env python3

import argparse
import json
import os
from collections import defaultdict
from pathlib import Path

def load_pr_data(json_file_path):
    """PRデータをJSONファイルから読み込む"""
    with open(json_file_path, 'r', encoding='utf-8') as f:
        pr_data = json.load(f)
    print(f"{len(pr_data)}件のPRデータを読み込みました")
    return pr_data

def group_prs_by_label(pr_data):
    """PRをラベルごとにグループ化する"""
    label_to_prs = defaultdict(list)
    
    for pr in pr_data:
        if not pr:  # Noneの場合はスキップ
            continue
            
        if not pr.get('labels'):
            label_to_prs['ラベルなし'].append(pr)
            continue
            
        for label in pr.get('labels', []):
            label_name = label.get('name')
            if label_name:
                label_to_prs[label_name].append(pr)
    
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

def main():
    parser = argparse.ArgumentParser(description='PRデータをラベルごとにグループ化してMarkdownを生成する')
    parser.add_argument('--input', default='all_pr_data.json', help='入力JSONファイルのパス')
    parser.add_argument('--output-dir', default='label_reports', help='出力ディレクトリ')
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"エラー: 入力ファイル {args.input} が見つかりません")
        return 1
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    pr_data = load_pr_data(input_path)
    
    label_to_prs = group_prs_by_label(pr_data)
    
    for label_name, prs in label_to_prs.items():
        generate_label_markdown(label_name, prs, output_dir)
    
    generate_label_index(label_to_prs, output_dir)
    
    print(f"全てのラベル ({len(label_to_prs)} 種類) のMarkdownを生成しました")
    return 0

if __name__ == "__main__":
    exit(main())
