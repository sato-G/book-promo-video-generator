#!/usr/bin/env python3
"""
BGM管理モジュール

既存のstep10_add_bgm.pyをラップ
"""

from pathlib import Path
from typing import Dict, Any, Optional
from .utils import run_script, get_v1_src_path, load_json, save_json, get_project_root


def add_bgm(
    video_data: Dict[str, Any],
    bgm_file: Path,
    volume: float = 0.15
) -> Dict[str, Any]:
    """
    動画にBGMを追加

    Args:
        video_data: render_video()で生成された動画情報
        bgm_file: BGMファイルのパス
        volume: BGM音量 (0.0 - 1.0)

    Returns:
        BGM付き動画情報
    """
    project_root = get_project_root()
    v1_src = get_v1_src_path()

    # v1の字幕付き動画を探す
    book_name = video_data['book_name']
    pattern_id = video_data['pattern_id']
    pattern_name = video_data['pattern_name']

    # v1のvideoディレクトリを探す
    v1_video_dir = project_root / "v1" / "data" / "videos" / book_name

    # パターンディレクトリを探す（複数の可能性）
    pattern_dirs = list(v1_video_dir.glob(f"pattern{pattern_id}_*"))
    if not pattern_dirs:
        raise FileNotFoundError(f"パターンディレクトリが見つかりません: pattern{pattern_id}_*")

    # 字幕付き動画を探す
    subtitle_video = None
    for pattern_dir in pattern_dirs:
        candidates = list(pattern_dir.glob("*_with_subtitles*.mp4"))
        # BGMなしの字幕動画を優先
        for candidate in candidates:
            if '_with_bgm' not in candidate.stem:
                subtitle_video = candidate
                break
        if subtitle_video:
            break

    if not subtitle_video:
        raise FileNotFoundError("字幕付き動画が見つかりません")

    if not bgm_file.exists():
        raise FileNotFoundError(f"BGMファイルが見つかりません: {bgm_file}")

    # Step 10: BGM追加
    print(f"🎵 BGM追加中: {bgm_file.name} (音量: {volume})")

    # 環境変数でBGM音量を設定
    import os
    env = os.environ.copy()
    env['BGM_VOLUME'] = str(volume)

    script10 = v1_src / "step10_add_bgm.py"
    success, output = run_script(str(script10), str(subtitle_video), str(bgm_file))

    if not success:
        raise RuntimeError(f"BGM追加エラー: {output}")

    # BGM付き動画を探す
    bgm_video = subtitle_video.parent / f"{subtitle_video.stem}_with_bgm.mp4"

    if not bgm_video.exists():
        raise FileNotFoundError(f"BGM付き動画が見つかりません: {bgm_video}")

    # data/output/final.mp4としてコピー
    output_dir = project_root / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    final_video = output_dir / "final.mp4"
    import shutil
    shutil.copy2(bgm_video, final_video)

    final_data = {
        "book_name": book_name,
        "pattern_id": pattern_id,
        "pattern_name": pattern_name,
        "video_file": str(final_video),
        "subtitle_type": video_data.get('subtitle_type', 'karaoke'),
        "has_bgm": True,
        "bgm_file": str(bgm_file),
        "bgm_volume": volume
    }

    # data/internal/final_video.jsonに保存
    internal_dir = project_root / "data" / "internal"
    final_file_data = internal_dir / "final_video.json"
    save_json(final_file_data, final_data)

    print(f"✅ BGM追加完了: {final_video.name}")

    return final_data


def list_available_bgm() -> list:
    """
    利用可能なBGMファイルのリストを取得

    Returns:
        BGMファイルのパスリスト
    """
    project_root = get_project_root()

    # 複数の場所からBGMを探す
    bgm_locations = [
        project_root / "v1" / "data" / "BGM",
        project_root / "data" / "BGM",
        project_root / "assets" / "bgm"
    ]

    bgm_files = []
    for location in bgm_locations:
        if location.exists():
            bgm_files.extend(location.glob("*.mp3"))
            bgm_files.extend(location.glob("*.wav"))

    return sorted(set(bgm_files))
