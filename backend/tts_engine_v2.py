#!/usr/bin/env python3
"""
TTS（Text-to-Speech）エンジンモジュール v2（v1非依存）

OpenAI TTSを直接使用してナレーション音声を生成
"""

from pathlib import Path
from typing import Dict, Any, List
import openai
import os
from dotenv import load_dotenv
from .utils import get_project_root

load_dotenv()


def synthesize_narration_for_scenes(
    scenes: List[Dict[str, Any]],
    book_name: str,
    voice: str = "alloy",
    speed: float = 1.0,
    model: str = "tts-1"
) -> Dict[int, Path]:
    """
    各シーンのナレーションから音声を生成（OpenAI TTS）

    Args:
        scenes: シーンのリスト
        book_name: 書籍名
        voice: 音声タイプ (alloy, echo, fable, onyx, nova, shimmer)
        speed: 音声速度 (0.25 - 4.0, デフォルト 1.0)
        model: TTSモデル (tts-1 or tts-1-hd)

    Returns:
        {シーン番号: 音声ファイルパス} の辞書
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY環境変数が設定されていません")

    client = openai.OpenAI(api_key=api_key)

    project_root = get_project_root()
    output_dir = project_root / "data" / "output" / "audio" / book_name
    output_dir.mkdir(parents=True, exist_ok=True)

    scene_audio = {}

    for scene in scenes:
        scene_num = scene['scene_number']
        narration = scene['narration']

        print(f"  🎤 シーン{scene_num}のナレーション生成中... (速度: {speed}x)")

        # OpenAI TTSで音声生成
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=narration,
            speed=speed
        )

        # 音声ファイルを保存
        audio_filename = f"scene_{scene_num:02d}_narration.mp3"
        audio_path = output_dir / audio_filename

        response.stream_to_file(audio_path)

        scene_audio[scene_num] = audio_path
        print(f"  ✓ シーン{scene_num}: {audio_path}")

    return scene_audio


def synthesize_single_narration(
    text: str,
    book_name: str,
    filename: str = "narration.mp3",
    voice: str = "alloy"
) -> Path:
    """
    単一のテキストから音声を生成

    Args:
        text: ナレーションテキスト
        book_name: 書籍名
        filename: 出力ファイル名
        voice: 音声タイプ

    Returns:
        生成された音声ファイルのパス
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY環境変数が設定されていません")

    client = openai.OpenAI(api_key=api_key)

    project_root = get_project_root()
    output_dir = project_root / "data" / "output" / "audio" / book_name
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"  🎤 ナレーション生成中...")

    # OpenAI TTSで音声生成
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )

    # 音声ファイルを保存
    audio_path = output_dir / filename
    response.stream_to_file(audio_path)

    print(f"  ✓ 音声生成完了: {audio_path}")

    return audio_path


# 利用可能な音声タイプ
AVAILABLE_VOICES = {
    "alloy": "中性的でバランスの良い声",
    "echo": "男性的で落ち着いた声",
    "fable": "イギリス英語風の男性の声",
    "onyx": "力強い男性の声",
    "nova": "明るく活発な女性の声",
    "shimmer": "柔らかく優しい女性の声"
}
