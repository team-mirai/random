"""
ファイルユーティリティモジュール

JSONファイルの読み込みと保存などのファイル操作ユーティリティを提供します。
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_json_file(file_path: Union[str, Path]) -> Any:
    """
    JSONファイルを読み込む

    Args:
        file_path: JSONファイルのパス

    Returns:
        読み込んだJSONデータ
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return []


def save_json_file(data: Any, file_path: Union[str, Path]) -> bool:
    """
    JSONファイルを保存する

    Args:
        data: 保存するデータ
        file_path: 保存先ファイルパス

    Returns:
        保存に成功した場合はTrue、失敗した場合はFalse
    """
    try:
        os.makedirs(os.path.dirname(str(file_path)), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved data to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving to {file_path}: {e}")
        return False


def ensure_directory(directory_path: Union[str, Path]) -> bool:
    """
    ディレクトリが存在することを確認し、存在しない場合は作成する

    Args:
        directory_path: 確認/作成するディレクトリパス

    Returns:
        ディレクトリが存在する（または作成された）場合はTrue、失敗した場合はFalse
    """
    try:
        os.makedirs(str(directory_path), exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {directory_path}: {e}")
        return False


def get_file_extension(file_path: Union[str, Path]) -> str:
    """
    ファイルの拡張子を取得する

    Args:
        file_path: ファイルパス

    Returns:
        ファイルの拡張子（ドットを含む）
    """
    return os.path.splitext(str(file_path))[1].lower()


def list_files(
    directory_path: Union[str, Path], 
    pattern: str = "*", 
    recursive: bool = False
) -> List[Path]:
    """
    ディレクトリ内のファイルを一覧表示する

    Args:
        directory_path: 検索するディレクトリパス
        pattern: 検索パターン（glob形式）
        recursive: サブディレクトリも検索するかどうか

    Returns:
        ファイルパスのリスト
    """
    path = Path(directory_path)
    if recursive:
        return list(path.glob(f"**/{pattern}"))
    else:
        return list(path.glob(pattern))


def get_latest_file(
    directory_path: Union[str, Path], 
    pattern: str = "*"
) -> Optional[Path]:
    """
    ディレクトリ内の最新のファイルを取得する

    Args:
        directory_path: 検索するディレクトリパス
        pattern: 検索パターン（glob形式）

    Returns:
        最新のファイルパス、ファイルが見つからない場合はNone
    """
    files = list_files(directory_path, pattern)
    if not files:
        return None
    
    return max(files, key=lambda f: f.stat().st_mtime)
