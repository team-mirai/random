#!/usr/bin/env python3

import os
import requests
import json
from pathlib import Path
import backoff

class ContentClassifier:
    """PRの内容を分析し、適切なカテゴリに分類するクラス"""
    
    def __init__(self, api_key=None, repo_root=None):
        """初期化
        
        Args:
            api_key: OpenRouter APIキー（Noneの場合は環境変数から取得）
            repo_root: リポジトリのルートディレクトリ（Noneの場合はカレントディレクトリの親）
        """
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter APIキーが設定されていません。環境変数OPENROUTER_API_KEYを設定してください。")
        
        self.repo_root = Path(repo_root) if repo_root else Path(__file__).parent.parent
        self.existing_files = self._get_existing_files()
        
    def _get_existing_files(self):
        """リポジトリ内の既存のマークダウンファイルを取得する"""
        existing_files = []
        for path in self.repo_root.glob("**/*.md"):
            if "pr_analysis" not in str(path.relative_to(self.repo_root)):
                existing_files.append(path)
        return existing_files
    
    @backoff.on_exception(
        backoff.expo,
        requests.exceptions.RequestException,
        max_tries=3,
    )
    def classify_content(self, pr_data):
        """PRの内容を分析して分類する
        
        Args:
            pr_data: PR情報を含む辞書
        
        Returns:
            dict: 分類結果（カテゴリ名、信頼度、説明を含む）
        """
        content = self._extract_pr_content(pr_data)
        
        result = self._analyze_with_openrouter(content)
        
        return result
    
    def _extract_pr_content(self, pr_data):
        """PRから分析に必要なテキストを抽出する"""
        texts = []
        
        basic = pr_data.get("basic_info", {})
        if basic.get("title"):
            texts.append(f"タイトル: {basic['title']}")
        if basic.get("body"):
            texts.append(f"説明: {basic['body']}")
        
        commits = pr_data.get("commits", [])
        commit_msgs = []
        for commit in commits:
            if commit.get("commit", {}).get("message"):
                commit_msgs.append(commit["commit"]["message"])
        if commit_msgs:
            texts.append("コミットメッセージ:\n" + "\n".join(commit_msgs))
        
        comments = pr_data.get("comments", [])
        comment_texts = []
        for comment in comments:
            if comment.get("body"):
                comment_texts.append(comment["body"])
        if comment_texts:
            texts.append("コメント:\n" + "\n".join(comment_texts))
        
        return "\n\n".join(texts)
    
    def _analyze_with_openrouter(self, content):
        """OpenRouter APIを使用してコンテンツを分析する"""
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        file_names = [str(f.relative_to(self.repo_root)) for f in self.existing_files]
        
        prompt = f"""
        あなたはPull Requestの内容を分析し、最も関連性の高いファイルに分類するアシスタントです。
        以下のPRの内容を分析して、最も関連性の高いマークダウンファイルを選択してください。
        どのファイルにも関連性がない場合は「分類不能」と判断してください。
        
        {content}
        
        {', '.join(file_names)}
        
        JSONフォーマットで以下の内容を返してください:
        {{
          "category": "ファイル名または「分類不能」",
          "confidence": 0～1の数値（信頼度）,
          "explanation": "分類理由の簡潔な説明"
        }}
        """
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "openai/gpt-4o",  # 高性能モデルを使用
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "response_format": {"type": "json_object"}
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        try:
            content = result["choices"][0]["message"]["content"]
            classification = json.loads(content)
            return classification
        except (KeyError, json.JSONDecodeError) as e:
            print(f"APIレスポンスの解析に失敗しました: {e}")
            return {
                "category": "分類不能",
                "confidence": 0.0,
                "explanation": "APIレスポンスの解析に失敗しました"
            }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="PRの内容を分類するツール")
    parser.add_argument("--input", required=True, help="PRデータを含むJSONファイル")
    args = parser.parse_args()
    
    with open(args.input, "r", encoding="utf-8") as f:
        pr_data = json.load(f)
    
    classifier = ContentClassifier()
    result = classifier.classify_content(pr_data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
