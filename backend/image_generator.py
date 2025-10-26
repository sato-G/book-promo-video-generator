#!/usr/bin/env python3
"""
画像生成モジュール

既存のstep7_generate_images.pyとstep7_generate_images_inputver.pyをラップ
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from .utils import run_script, get_v1_src_path, load_json, save_json, get_project_root


def generate_images(
    narration_data: Dict[str, Any],
    reference_image: Optional[Path] = None
) -> Dict[str, Any]:
    """
    ナレーション音声から画像を生成

    Args:
        narration_data: synthesize_narration()で生成されたナレーション情報
        reference_image: 参考画像のパス（Noneの場合は通常生成）

    Returns:
        生成された画像情報とストーリーボードデータ
    """
    project_root = get_project_root()
    v1_src = get_v1_src_path()

    # v1のナレーションファイルパスを特定
    book_name = narration_data['book_name']
    pattern_name = narration_data['pattern_name']

    v1_narration_dir = project_root / "v1" / "data" / "narrations" / book_name
    narration_mp3 = v1_narration_dir / f"narration_{pattern_name}.mp3"

    if not narration_mp3.exists():
        raise FileNotFoundError(f"ナレーションファイルが見つかりません: {narration_mp3}")

    # 参考画像の有無で使用するスクリプトを切り替え
    if reference_image:
        print(f"🎨 画像生成中（参考画像あり）: {reference_image.name}")
        script = v1_src / "step7_generate_images_inputver.py"
        success, output = run_script(str(script), str(narration_mp3), str(reference_image))
    else:
        print("🎨 画像生成中（通常モード）")
        script = v1_src / "step7_generate_images.py"
        success, output = run_script(str(script), str(narration_mp3))

    if not success:
        raise RuntimeError(f"画像生成エラー: {output}")

    # 生成された画像のメタデータを読み込む
    pattern_dir_name = f"pattern{narration_data['pattern_id']}_{pattern_name}"
    if reference_image:
        pattern_dir_name += "_inputver"

    v1_images_dir = project_root / "v1" / "data" / "images" / book_name / pattern_dir_name
    metadata_file = v1_images_dir / "images_metadata.json"

    if not metadata_file.exists():
        raise FileNotFoundError(f"画像メタデータが見つかりません: {metadata_file}")

    metadata = load_json(metadata_file)

    # data/internal/storyboard.jsonとして保存
    internal_dir = project_root / "data" / "internal"
    internal_dir.mkdir(parents=True, exist_ok=True)

    # 画像をdata/internal/にコピー
    images_internal_dir = internal_dir / "images"
    images_internal_dir.mkdir(parents=True, exist_ok=True)

    import shutil
    scenes = []

    for img_data in metadata.get('generated_images', []):
        src_image = v1_images_dir / img_data['image_file']
        if src_image.exists():
            dest_image = images_internal_dir / img_data['image_file']
            shutil.copy2(src_image, dest_image)

            scenes.append({
                "scene_id": img_data['segment_index'],
                "start_time": img_data['start_time'],
                "end_time": img_data['end_time'],
                "text": img_data['text'],
                "image_path": str(dest_image),
                "prompt": img_data.get('prompt', '')
            })

    # ストーリーボードデータを作成
    storyboard_data = {
        "book_name": book_name,
        "pattern_id": narration_data['pattern_id'],
        "pattern_name": pattern_name,
        "total_scenes": len(scenes),
        "scenes": scenes,
        "audio_file": narration_data['narration_file'],
        "has_reference_image": reference_image is not None
    }

    storyboard_file = internal_dir / "storyboard.json"
    save_json(storyboard_file, storyboard_data)

    print(f"✅ {len(scenes)}枚の画像を生成しました")

    return storyboard_data


def split_into_scenes(scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    シナリオをシーンに分割（将来的な機能拡張用）

    現在はgenerate_images()内で自動分割されるため、この関数は参照用

    Args:
        scenario: シナリオデータ

    Returns:
        シーンのリスト
    """
    # TODO: より詳細なシーン分割ロジックを実装
    return []
