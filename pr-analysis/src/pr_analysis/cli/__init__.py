"""
コマンドラインインターフェースモジュール

PR分析ツールのコマンドラインインターフェースを提供します。
"""

from .analyzer import main as analyzer_main
from .fetcher import main as fetcher_main
from .reporter import main as reporter_main

__all__ = ["analyzer_main", "fetcher_main", "reporter_main"]
