#!/usr/bin/env python3
"""
セッション管理モジュール

Streamlitのセッション状態を保存・復元する
"""

from pathlib import Path
import json
from typing import Dict, Any, Optional
from datetime import datetime
from .utils import get_project_root


def save_session_state(session_data: Dict[str, Any], book_name: str) -> Path:
    """
    セッション状態をJSONファイルに保存

    Args:
        session_data: セッション状態の辞書
        book_name: 書籍名

    Returns:
        保存先パス
    """
    project_root = get_project_root()
    save_dir = project_root / "data" / "internal" / "sessions"
    save_dir.mkdir(parents=True, exist_ok=True)

    # タイムスタンプ付きファイル名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"session_{book_name}_{timestamp}.json"
    save_path = save_dir / filename

    # 最新セッションファイルも保存（上書き）
    latest_path = save_dir / f"session_{book_name}_latest.json"

    # パスオブジェクトを文字列に変換
    serializable_data = {}
    for key, value in session_data.items():
        if isinstance(value, Path):
            serializable_data[key] = str(value)
        elif isinstance(value, dict):
            # 辞書内のPathも変換
            serializable_data[key] = _convert_paths_to_strings(value)
        elif isinstance(value, list):
            # リスト内のPathも変換
            serializable_data[key] = [_convert_paths_to_strings(item) if isinstance(item, dict) else item for item in value]
        else:
            serializable_data[key] = value

    # JSON保存
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_data, f, ensure_ascii=False, indent=2)

    with open(latest_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_data, f, ensure_ascii=False, indent=2)

    print(f"  💾 セッション保存: {save_path}")

    return save_path


def load_session_state(book_name: str, use_latest: bool = True) -> Optional[Dict[str, Any]]:
    """
    セッション状態をJSONファイルから復元

    Args:
        book_name: 書籍名
        use_latest: True の場合、最新のセッションファイルを使用

    Returns:
        セッション状態の辞書。ファイルがない場合はNone
    """
    project_root = get_project_root()
    save_dir = project_root / "data" / "internal" / "sessions"

    if use_latest:
        session_file = save_dir / f"session_{book_name}_latest.json"
    else:
        # 最新のタイムスタンプ付きファイルを検索
        session_files = list(save_dir.glob(f"session_{book_name}_*.json"))
        if not session_files:
            return None
        session_file = max(session_files, key=lambda p: p.stat().st_mtime)

    if not session_file.exists():
        return None

    with open(session_file, 'r', encoding='utf-8') as f:
        session_data = json.load(f)

    print(f"  📂 セッション復元: {session_file}")

    return session_data


def _convert_paths_to_strings(obj: Any) -> Any:
    """
    再帰的にPathオブジェクトを文字列に変換
    """
    if isinstance(obj, Path):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: _convert_paths_to_strings(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_convert_paths_to_strings(item) for item in obj]
    else:
        return obj


def get_saved_sessions(book_name: Optional[str] = None) -> list[Path]:
    """
    保存されているセッションファイルのリストを取得

    Args:
        book_name: 書籍名（指定した場合、その書籍のセッションのみ）

    Returns:
        セッションファイルのパスリスト
    """
    project_root = get_project_root()
    save_dir = project_root / "data" / "internal" / "sessions"

    if not save_dir.exists():
        return []

    if book_name:
        pattern = f"session_{book_name}_*.json"
    else:
        pattern = "session_*.json"

    session_files = list(save_dir.glob(pattern))
    # 新しい順にソート
    session_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    return session_files
