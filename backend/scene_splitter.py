#!/usr/bin/env python3
"""
シーン分割モジュール

選択されたシナリオを複数のシーンに分割する
"""

from pathlib import Path
from typing import Dict, Any, List
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()


def split_into_scenes(
    scenario: Dict[str, Any], num_scenes: int = 5
) -> List[Dict[str, Any]]:
    """
    シナリオを複数のシーンに分割

    Args:
        scenario: 選択されたシナリオデータ
        num_scenes: 分割するシーン数（デフォルト5）

    Returns:
        シーンのリスト（各シーンにはナレーション、画像プロンプト、タイミング情報を含む）
    """

    # Gemini API設定
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY環境変数が設定されていません")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash-lite")

    # シナリオテキスト
    summary = scenario["selected_pattern"]["summary"]
    book_name = scenario["book_name"]
    visual_style = scenario.get("visual_style", "Cinematic")
    aspect_ratio = scenario.get("aspect_ratio", "9:16")

    # シナリオの文字数を取得
    scenario_length = len(summary)
    chars_per_scene = scenario_length // num_scenes

    prompt = f"""
以下の書籍紹介シナリオを、{num_scenes}つのシーンに分割してください。
**重要: シナリオの内容を削除・省略せず、全文を{num_scenes}個のシーンに分割してください。**

## 書籍名
{book_name}

## シナリオ（全文）
{summary}

## 動画設定
- アスペクト比: {aspect_ratio}
- ビジュアルスタイル: {visual_style}

---

## タスク

このシナリオ全文（{scenario_length}文字）を{num_scenes}つのシーンに分割し、各シーンに以下を含めてください：

1. **シーン番号** (1-{num_scenes})
2. **ナレーションテキスト**
   - **必ずシナリオ全文を使用し、内容を削除・省略しないこと**
   - 文字数や句読点の位置で自然に分割する
   - 1シーンあたり約{chars_per_scene}文字を目安とする
   - 区切りのいいところ（句点「。」の後）で分割する
3. **画像プロンプト** (DALL-E 3用、英語、{visual_style}スタイルを反映)
4. **推定時間** (秒、ナレーション文字数÷10で計算)

## 重要な要件

- **シナリオの内容を一切カットしない**（全文を必ず使用）
- ナレーションは自然な流れで分割する（句読点を考慮）
- 各シーンは独立して意味が通じるように
- 画像プロンプトはシーンの内容を視覚的に表現し、具体的なビジュアル要素を含める
- **{visual_style}スタイルに完全に適合した画像プロンプトを作成**
  - Anime: アニメ風のキャラクター、鮮やかな色彩、デフォルメ表現
  - Photorealistic: 実写的、リアルな質感、自然な光と影
  - Cinematic: 映画的、ドラマチックなライティング、奥行きのある構図
  - Picture book: 絵本風、優しい色合い、シンプルなフォルム
  - Illustration: イラスト調、芸術的、スタイライズ
- 画像プロンプトは詳細に記述（50-100語の英語）

---

JSON形式で出力してください。

出力形式:
{{
  "scenes": [
    {{
      "scene_number": 1,
      "narration": "シナリオから抽出したナレーション文（カットなし）",
      "image_prompt": "DALL-E prompt in English with {visual_style} style",
      "duration_seconds": 推定秒数
    }},
    ...
  ]
}}
"""

    print(f"  🤖 Gemini APIでシーン分割中（{num_scenes}シーン）...")
    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.7,
            "response_mime_type": "application/json",
        },
    )

    result = json.loads(response.text)
    scenes = result["scenes"]

    print(f"  ✓ {len(scenes)}シーンに分割完了")

    return scenes


def save_scenes(scenes: List[Dict[str, Any]], book_name: str) -> Path:
    """
    シーンデータを保存

    Args:
        scenes: シーンリスト
        book_name: 書籍名

    Returns:
        保存先パス
    """
    from .utils import get_project_root, save_json

    project_root = get_project_root()
    internal_dir = project_root / "data" / "internal"
    internal_dir.mkdir(parents=True, exist_ok=True)

    scenes_file = internal_dir / "scenes.json"

    scenes_data = {
        "book_name": book_name,
        "scenes": scenes,
        "total_scenes": len(scenes),
    }

    save_json(scenes_file, scenes_data)
    print(f"  💾 シーンデータを保存: {scenes_file}")

    return scenes_file
