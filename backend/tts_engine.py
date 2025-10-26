#!/usr/bin/env python3
"""
TTS（Text-to-Speech）エンジンモジュール

既存のstep6_generate_narration.pyをラップ
"""

from pathlib import Path
from typing import Dict, Any
from .utils import run_script, get_v1_src_path, load_json, save_json, get_project_root


def synthesize_narration(scenario_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    シナリオテキストからナレーション音声を生成

    Args:
        scenario_data: select_scenario()で選択されたシナリオ情報

    Returns:
        生成された音声ファイル情報
    """
    book_name = scenario_data['book_name']
    pattern = scenario_data['selected_pattern']
    pattern_id = pattern['pattern_id']
    pattern_name = pattern['pattern_name']

    # v1のパターンファイルを使用
    source_file = Path(pattern['source_file'])

    # .txtファイルも確認
    txt_file = source_file.with_suffix('.txt')
    if not txt_file.exists():
        # .jsonファイルから.txtを生成
        pattern_data = load_json(source_file)
        txt_content = pattern_data['pattern_info']['summary']
        txt_file.write_text(txt_content, encoding='utf-8')

    v1_src = get_v1_src_path()
    script = v1_src / "step6_generate_narration.py"

    print(f"🎤 ナレーション生成中: パターン{pattern_id} - {pattern_name}")
    success, output = run_script(str(script), str(txt_file))

    if not success:
        raise RuntimeError(f"ナレーション生成エラー: {output}")

    # 生成されたファイルを探す
    project_root = get_project_root()
    v1_narration_dir = project_root / "v1" / "data" / "narrations" / book_name
    narration_file = v1_narration_dir / f"narration_{pattern_name}.mp3"
    metadata_file = v1_narration_dir / f"narration_{pattern_name}_metadata.json"

    if not narration_file.exists():
        raise FileNotFoundError(f"ナレーションファイルが見つかりません: {narration_file}")

    # メタデータを読み込む
    if metadata_file.exists():
        metadata = load_json(metadata_file)
    else:
        metadata = {
            "book_name": book_name,
            "pattern_info": pattern,
            "text": pattern['summary']
        }

    # data/internal/にコピー
    internal_dir = project_root / "data" / "internal"
    internal_dir.mkdir(parents=True, exist_ok=True)

    new_narration_file = internal_dir / f"narration_{pattern_id}.mp3"
    new_metadata_file = internal_dir / f"narration_{pattern_id}_metadata.json"

    import shutil
    shutil.copy2(narration_file, new_narration_file)

    # メタデータを更新して保存
    narration_data = {
        "book_name": book_name,
        "pattern_id": pattern_id,
        "pattern_name": pattern_name,
        "narration_file": str(new_narration_file),
        "original_text": pattern['summary'],
        "metadata": metadata
    }
    save_json(new_metadata_file, narration_data)

    print(f"✅ ナレーション生成完了: {new_narration_file.name}")

    return narration_data


# FIXME: 将来的にGoogle Cloud TTSへ移行予定
def synthesize_google_tts(text: str, output_path: Path) -> Path:
    """
    Google Cloud TTSでナレーション生成（未実装）

    Args:
        text: 読み上げテキスト
        output_path: 出力ファイルパス

    Returns:
        生成されたファイルパス
    """
    raise NotImplementedError("Google Cloud TTS is not implemented yet")
