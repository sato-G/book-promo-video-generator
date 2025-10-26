#!/usr/bin/env python3
"""
共通ユーティリティ関数
"""

import subprocess
from pathlib import Path
from typing import Tuple, Optional
import json


def run_script(script_path: str, *args, cwd: Optional[Path] = None) -> Tuple[bool, str]:
    """
    既存スクリプトを実行するヘルパー関数

    Args:
        script_path: 実行するスクリプトのパス
        *args: スクリプトに渡す引数
        cwd: 作業ディレクトリ（Noneの場合はプロジェクトルート）

    Returns:
        (成功フラグ, 出力テキスト)
    """
    if cwd is None:
        cwd = get_project_root()

    try:
        cmd = ["python3", script_path] + list(args)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=cwd
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, f"Error: {e.stderr}\n{e.stdout}"
    except Exception as e:
        return False, f"Exception: {str(e)}"


def get_project_root() -> Path:
    """プロジェクトのルートディレクトリを取得"""
    return Path(__file__).parent.parent


def get_v1_src_path() -> Path:
    """v1のsrcディレクトリパスを取得"""
    return get_project_root() / "v1" / "src"


def load_json(file_path: Path) -> dict:
    """JSONファイルを読み込む"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(file_path: Path, data: dict, indent: int = 2):
    """JSONファイルに保存"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def ensure_dir(path: Path) -> Path:
    """ディレクトリが存在することを保証"""
    path.mkdir(parents=True, exist_ok=True)
    return path
