"""
コンテンツ分類モジュール

Pull Requestの内容を分析し、分類するための機能を提供します。
"""

import os
import re
from typing import Dict, List, Optional, Any, Union, Tuple

import backoff
import requests


class ContentClassifier:
    """Pull Requestの内容を分類するためのクラス"""

    def __init__(self, api_key: Optional[str] = None):
        """
        ContentClassifierを初期化する

        Args:
            api_key: OpenRouter APIキー（指定がない場合は環境変数から取得）
        """
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            print("警告: OPENROUTER_API_KEYが設定されていません。分類機能は利用できません。")

    @backoff.on_exception(
        backoff.expo,
        requests.exceptions.RequestException,
        max_tries=3,
    )
    def classify_content(self, content: str, categories: List[str]) -> Dict[str, float]:
        """
        コンテンツを指定されたカテゴリに分類する

        Args:
            content: 分類するコンテンツ
            categories: 分類カテゴリのリスト

        Returns:
            カテゴリごとの確率を含む辞書
        """
        if not self.api_key:
            print("エラー: OPENROUTER_API_KEYが設定されていません。分類を実行できません。")
            return {category: 0.0 for category in categories}

        categories_str = ", ".join(categories)

        prompt = f"""
        以下のテキストを次のカテゴリに分類してください: {categories_str}
        
        各カテゴリについて、テキストがそのカテゴリに属する確率を0から1の間で評価してください。
        回答は以下の形式で返してください:
        カテゴリ1: 0.X
        カテゴリ2: 0.Y
        ...
        
        テキスト:
        {content}
        """

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        data = {
            "model": "anthropic/claude-3-opus",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.0,
        }
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            scores = {}
            for line in content.strip().split("\n"):
                if ":" in line:
                    category, score_str = line.split(":", 1)
                    category = category.strip()
                    try:
                        score = float(score_str.strip())
                        if category in categories:
                            scores[category] = score
                    except ValueError:
                        pass
            
            for category in categories:
                if category not in scores:
                    scores[category] = 0.0
                    
            return scores
            
        except Exception as e:
            print(f"分類中にエラーが発生しました: {e}")
            return {category: 0.0 for category in categories}

    def is_readme_pr(self, pr_data: Dict[str, Any]) -> bool:
        """
        PRがREADMEの変更かどうかを判定する

        Args:
            pr_data: PR情報の辞書

        Returns:
            READMEの変更の場合はTrue、それ以外はFalse
        """
        files = pr_data.get("files", [])
        for file in files:
            filename = file.get("filename", "").lower()
            if "readme" in filename or "documentation" in filename:
                return True
                
        commits = pr_data.get("commits", [])
        for commit in commits:
            message = commit.get("commit", {}).get("message", "").lower()
            if "readme" in message or "documentation" in message or "docs" in message:
                return True
                
        basic_info = pr_data.get("basic_info", {})
        title = basic_info.get("title", "").lower()
        body = basic_info.get("body", "").lower()
        
        if "readme" in title or "documentation" in title or "docs" in title:
            return True
            
        if body and ("readme" in body or "documentation" in body or "docs:" in body):
            return True
            
        return False


def classify_content(content: str, categories: List[str], api_key: Optional[str] = None) -> Dict[str, float]:
    """
    コンテンツを指定されたカテゴリに分類する便利関数

    Args:
        content: 分類するコンテンツ
        categories: 分類カテゴリのリスト
        api_key: OpenRouter APIキー（指定がない場合は環境変数から取得）

    Returns:
        カテゴリごとの確率を含む辞書
    """
    classifier = ContentClassifier(api_key)
    return classifier.classify_content(content, categories)


def is_readme_pr(pr_data: Dict[str, Any]) -> bool:
    """
    PRがREADMEの変更かどうかを判定する便利関数

    Args:
        pr_data: PR情報の辞書

    Returns:
        READMEの変更の場合はTrue、それ以外はFalse
    """
    classifier = ContentClassifier()
    return classifier.is_readme_pr(pr_data)
