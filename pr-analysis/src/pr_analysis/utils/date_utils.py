"""
日付ユーティリティモジュール

日付と時刻の解析と書式設定のためのユーティリティを提供します。
"""

import datetime
from typing import Optional, Union


def parse_datetime(
    date_string: str, 
    formats: Optional[list] = None
) -> Optional[datetime.datetime]:
    """
    文字列を日時オブジェクトに変換する

    Args:
        date_string: 変換する日時文字列
        formats: 試行する日時フォーマットのリスト

    Returns:
        変換された日時オブジェクト、変換できない場合はNone
    """
    if not formats:
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",  # ISO 8601 (GitHub API)
            "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO 8601 with microseconds
            "%Y-%m-%dT%H:%M:%S%z",  # ISO 8601 with timezone
            "%Y-%m-%d %H:%M:%S",  # 標準的な日時形式
            "%Y-%m-%d",  # 日付のみ
        ]

    for fmt in formats:
        try:
            dt = datetime.datetime.strptime(date_string, fmt)
            return dt
        except ValueError:
            continue

    try:
        return datetime.datetime.fromisoformat(date_string.replace("Z", "+00:00"))
    except ValueError:
        pass

    return None


def format_datetime(
    dt: Union[datetime.datetime, str], 
    output_format: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """
    日時オブジェクトまたは日時文字列を指定された形式にフォーマットする

    Args:
        dt: フォーマットする日時オブジェクトまたは日時文字列
        output_format: 出力形式

    Returns:
        フォーマットされた日時文字列
    """
    if isinstance(dt, str):
        parsed_dt = parse_datetime(dt)
        if not parsed_dt:
            return dt  # 解析できない場合は元の文字列を返す
        dt = parsed_dt

    return dt.strftime(output_format)


def get_relative_time_description(dt: Union[datetime.datetime, str]) -> str:
    """
    日時オブジェクトまたは日時文字列から相対的な時間説明を取得する

    Args:
        dt: 日時オブジェクトまたは日時文字列

    Returns:
        相対的な時間説明（例: "3日前", "1時間前"）
    """
    if isinstance(dt, str):
        parsed_dt = parse_datetime(dt)
        if not parsed_dt:
            return "不明な日時"
        dt = parsed_dt

    now = datetime.datetime.now(dt.tzinfo) if dt.tzinfo else datetime.datetime.now()
    diff = now - dt

    if diff.days < 0:
        return "未来の日時"
    elif diff.days == 0:
        hours = diff.seconds // 3600
        if hours == 0:
            minutes = diff.seconds // 60
            if minutes == 0:
                return "たった今"
            elif minutes == 1:
                return "1分前"
            else:
                return f"{minutes}分前"
        elif hours == 1:
            return "1時間前"
        else:
            return f"{hours}時間前"
    elif diff.days == 1:
        return "昨日"
    elif diff.days < 7:
        return f"{diff.days}日前"
    elif diff.days < 30:
        weeks = diff.days // 7
        if weeks == 1:
            return "1週間前"
        else:
            return f"{weeks}週間前"
    elif diff.days < 365:
        months = diff.days // 30
        if months == 1:
            return "1ヶ月前"
        else:
            return f"{months}ヶ月前"
    else:
        years = diff.days // 365
        if years == 1:
            return "1年前"
        else:
            return f"{years}年前"


def get_date_range(
    start_date: Union[datetime.datetime, str], 
    end_date: Union[datetime.datetime, str]
) -> int:
    """
    2つの日時間の日数を計算する

    Args:
        start_date: 開始日時
        end_date: 終了日時

    Returns:
        日数
    """
    if isinstance(start_date, str):
        start_date = parse_datetime(start_date)
        if not start_date:
            raise ValueError("開始日時を解析できませんでした")

    if isinstance(end_date, str):
        end_date = parse_datetime(end_date)
        if not end_date:
            raise ValueError("終了日時を解析できませんでした")

    delta = end_date - start_date
    return delta.days
