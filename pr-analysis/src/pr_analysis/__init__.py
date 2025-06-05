"""
PR Analysis パッケージ

GitHub Pull Requestを分析するためのツールです。
"""

from .api.github import GitHubAPIClient
from .fetcher import PRFetcher, fetch_prs
from .analyzer import ContentClassifier, classify_content, is_readme_pr, PRAnalyzer, analyze_prs
from .reporter import (
    generate_markdown,
    generate_summary_markdown,
    generate_issues_and_diffs_markdown,
    generate_file_based_markdown,
    convert_json_to_csv,
)
from .utils import load_json_file, save_json_file, parse_datetime, format_datetime

__version__ = "0.1.0"

__all__ = [
    "GitHubAPIClient",
    
    "PRFetcher",
    "fetch_prs",
    
    "ContentClassifier",
    "classify_content",
    "is_readme_pr",
    "PRAnalyzer",
    "analyze_prs",
    
    "generate_markdown",
    "generate_summary_markdown",
    "generate_issues_and_diffs_markdown",
    "generate_file_based_markdown",
    "convert_json_to_csv",
    
    "load_json_file",
    "save_json_file",
    "parse_datetime",
    "format_datetime",
]
