#!/usr/bin/env python3
"""
動画レンダリングモジュール

既存のstep8(動画作成), step9(字幕), step10(BGM)をラップ
"""

from pathlib import Path
from typing import Dict, Any, Optional
from .utils import run_script, get_v1_src_path, load_json, save_json, get_project_root


def render_video(
    storyboard_data: Dict[str, Any],
    subtitle_type: str = "karaoke"
) -> Dict[str, Any]:
    """
    ストーリーボードから動画を作成（字幕付き）

    Args:
        storyboard_data: generate_images()で生成されたストーリーボード情報
        subtitle_type: 字幕タイプ ("karaoke" or "normal")

    Returns:
        生成された動画情報
    """
    project_root = get_project_root()
    v1_src = get_v1_src_path()

    book_name = storyboard_data['book_name']
    pattern_id = storyboard_data['pattern_id']
    pattern_name = storyboard_data['pattern_name']

    # v1の画像メタデータファイルを特定
    pattern_dir_name = f"pattern{pattern_id}_{pattern_name}"
    if storyboard_data.get('has_reference_image'):
        pattern_dir_name += "_inputver"

    v1_images_dir = project_root / "v1" / "data" / "images" / book_name / pattern_dir_name
    metadata_file = v1_images_dir / "images_metadata.json"

    v1_narration_dir = project_root / "v1" / "data" / "narrations" / book_name
    narration_file = v1_narration_dir / f"narration_{pattern_name}.mp3"

    if not metadata_file.exists():
        raise FileNotFoundError(f"画像メタデータが見つかりません: {metadata_file}")
    if not narration_file.exists():
        raise FileNotFoundError(f"ナレーションファイルが見つかりません: {narration_file}")

    # Step 8: 動画作成
    print("🎬 動画作成中...")
    script8 = v1_src / "step8_create_video.py"
    success, output = run_script(str(script8), str(metadata_file), str(narration_file))

    if not success:
        raise RuntimeError(f"動画作成エラー: {output}")

    # 生成された動画を探す
    v1_video_dir = project_root / "v1" / "data" / "videos" / book_name / pattern_dir_name
    base_video_name = f"{book_name}_pattern{pattern_id}"
    if storyboard_data.get('has_reference_image'):
        base_video_name += "_inputver"
    base_video = v1_video_dir / f"{base_video_name}.mp4"

    if not base_video.exists():
        raise FileNotFoundError(f"基本動画が見つかりません: {base_video}")

    # Step 9: 字幕追加
    print(f"📝 字幕追加中（{subtitle_type}）...")
    if subtitle_type == "karaoke":
        script9 = v1_src / "step9_add_subtitles_karaoke.py"
    else:
        script9 = v1_src / "step9_add_subtitles.py"

    success, output = run_script(str(script9), str(base_video))

    if not success:
        raise RuntimeError(f"字幕追加エラー: {output}")

    # 字幕付き動画を探す
    subtitle_suffix = "_with_subtitles_karaoke" if subtitle_type == "karaoke" else "_with_subtitles"
    subtitle_video = v1_video_dir / f"{base_video_name}{subtitle_suffix}.mp4"

    if not subtitle_video.exists():
        raise FileNotFoundError(f"字幕付き動画が見つかりません: {subtitle_video}")

    # data/output/にコピー
    output_dir = project_root / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    preview_video = output_dir / "preview.mp4"
    import shutil
    shutil.copy2(subtitle_video, preview_video)

    video_data = {
        "book_name": book_name,
        "pattern_id": pattern_id,
        "pattern_name": pattern_name,
        "video_file": str(preview_video),
        "subtitle_type": subtitle_type,
        "has_bgm": False
    }

    # data/internal/video.jsonに保存
    internal_dir = project_root / "data" / "internal"
    video_file_data = internal_dir / "video.json"
    save_json(video_file_data, video_data)

    print(f"✅ 動画作成完了: {preview_video.name}")

    return video_data


def render_preview(config: Dict[str, Any]) -> Path:
    """
    設定に基づいてプレビュー動画を生成

    Args:
        config: 詳細設定情報（config.json）

    Returns:
        プレビュー動画のパス
    """
    # TODO: より詳細な設定対応
    # 現在はrender_video()を直接使用
    storyboard_file = get_project_root() / "data" / "internal" / "storyboard.json"
    if not storyboard_file.exists():
        raise FileNotFoundError("ストーリーボードファイルが見つかりません")

    storyboard_data = load_json(storyboard_file)
    video_data = render_video(storyboard_data, config.get('subtitle_type', 'karaoke'))

    return Path(video_data['video_file'])
