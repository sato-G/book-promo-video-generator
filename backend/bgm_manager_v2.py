#!/usr/bin/env python3
"""
BGM管理モジュール v2

v1スクリプトには依存しない
"""

from pathlib import Path
from typing import List


def get_project_root() -> Path:
    """プロジェクトルートを取得"""
    return Path(__file__).parent.parent


def list_available_bgm() -> List[Path]:
    """
    利用可能なBGMファイルのリストを取得

    Returns:
        BGMファイルのパスリスト
    """
    project_root = get_project_root()

    # 複数の場所からBGMを探す
    bgm_locations = [
        project_root / "data" / "BGM",
        project_root / "assets" / "bgm",
        project_root / "v1" / "data" / "BGM"
    ]

    bgm_files = []
    for location in bgm_locations:
        if location.exists():
            # 音声ファイルを探す
            bgm_files.extend(location.glob("*.mp3"))
            bgm_files.extend(location.glob("*.wav"))
            bgm_files.extend(location.glob("*.m4a"))
            bgm_files.extend(location.glob("*.aac"))

    # 重複を除去してソート
    unique_files = sorted(set(bgm_files))

    return unique_files


def add_bgm(
    video_file: str,
    bgm_file: str,
    volume: float = 0.15
) -> dict:
    """
    動画にBGMを追加

    Args:
        video_file: 動画ファイルのパス（文字列）
        bgm_file: BGMファイルのパス（文字列）
        volume: BGM音量 (0.0 - 1.0)

    Returns:
        BGM付き動画情報
    """
    from .video_renderer_v2 import add_bgm_to_video

    video_path = Path(video_file)
    bgm_path = Path(bgm_file)

    # BGMを追加
    output_file = add_bgm_to_video(video_path, bgm_path, volume)

    return {
        "output_file": str(output_file),
        "original_video": video_file,
        "bgm_file": bgm_file,
        "bgm_volume": volume
    }
