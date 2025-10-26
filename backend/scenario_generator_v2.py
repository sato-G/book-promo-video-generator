#!/usr/bin/env python3
"""
シナリオ生成モジュール v2（v1非依存）

論文形式の書籍概要から、プロモーション用の3つのシナリオパターンを生成
"""

from pathlib import Path
from typing import Dict, Any, List
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
from .utils import save_json, get_project_root

load_dotenv()


def generate_scenarios_from_summary(book_name: str, summary: str, target_audience: str = "", book_type: str = "") -> List[Dict[str, Any]]:
    """
    論文形式の書籍概要から3つのプロモーション用シナリオパターンを生成

    Args:
        book_name: 書籍名
        summary: 論文形式の書籍概要（800文字程度）
        target_audience: 想定される読者層
        book_type: 書籍の種類

    Returns:
        3つのシナリオパターンのリスト
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY環境変数が設定されていません")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash-lite')

    # 3つのパターンを定義
    patterns = [
        {
            "pattern_id": 1,
            "pattern_name": "丁寧な解説型",
            "tone": "親しみやすく丁寧",
            "target": "初めて読む一般読者",
            "style_instruction": "優しい語り口で、書籍の魅力を分かりやすく伝える。「です・ます」調。",
            "length": "500-700文字"
        },
        {
            "pattern_id": 2,
            "pattern_name": "感情訴求型",
            "tone": "感動的・共感を呼ぶ",
            "target": "書籍の世界観に共感する読者",
            "style_instruction": "読者の感情に訴えかけ、書籍の感動や魅力を伝える。「です・ます」調。",
            "length": "500-700文字"
        },
        {
            "pattern_id": 3,
            "pattern_name": "簡潔PR型",
            "tone": "シンプルで要点をまとめた",
            "target": "時間のない読者・SNS向け",
            "style_instruction": "短く要点をまとめ、書籍の核心的な魅力を伝える。「です・ます」調。",
            "length": "300-500文字"
        }
    ]

    scenario_patterns = []

    for pattern in patterns:
        print(f"  🎬 パターン{pattern['pattern_id']}: {pattern['pattern_name']}を生成中...")

        prompt = f"""
あなたは書籍プロモーションの専門家です。
以下の書籍の論文形式の客観的な概要を読み、**プロモーション用シナリオ**を作成してください。

## 書籍名
{book_name}

## 書籍概要（論文形式・客観的）
{summary}

## 書籍情報
- 想定読者層: {target_audience}
- 書籍の種類: {book_type}

---

## タスク

この書籍のプロモーション用シナリオ（動画ナレーション原稿）を作成してください。

### シナリオパターン: {pattern['pattern_name']}

**トーン:** {pattern['tone']}
**対象読者:** {pattern['target']}
**スタイル:** {pattern['style_instruction']}
**文字数:** {pattern['length']}

### 要件

1. **プロモーション目的**
   - 書籍の魅力を伝え、読みたいと思わせる内容
   - {pattern['style_instruction']}
   - 「です・ます」調の語りかけ口調

2. **含めるべき内容**
   - 書籍の主題・テーマの紹介
   - 読者にとっての価値・魅力
   - 書籍の特徴や独自性
   - 読後に得られるもの（感動、知識、体験など）
   - 対象読者への呼びかけ

3. **避けるべき表現**
   - 過度に煽るような表現
   - 事実と異なる誇張
   - 論文形式のような堅い表現

4. **文字数: {pattern['length']}**
   - 適切な段落分けで読みやすく
   - 動画ナレーションとして自然な流れ

5. **文体の例**
   - 「この本は〜」「あなたは〜」などの語りかけ
   - 「〜でしょうか」「〜ですよね」などの共感表現も可
   - 読者の興味を引く表現

---

JSON形式で出力してください。

出力形式:
{{
  "summary": "プロモーション用シナリオ本文（{pattern['length']}）",
  "character_count": 実際の文字数,
  "key_messages": ["キーメッセージ1", "キーメッセージ2", "キーメッセージ3"],
  "hook": "冒頭の引きつけるフレーズ（30文字以内）"
}}
"""

        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,  # プロモーション用なので創造性を高め
                "response_mime_type": "application/json"
            }
        )

        result = json.loads(response.text)

        # パターン情報を追加
        scenario_patterns.append({
            "pattern_id": pattern['pattern_id'],
            "pattern_name": pattern['pattern_name'],
            "tone": pattern['tone'],
            "target_audience": pattern['target'],
            "summary": result['summary'],
            "character_count": result['character_count'],
            "key_messages": result['key_messages'],
            "hook": result['hook'],
            "use_case": f"{pattern['pattern_name']}のプロモーションシナリオ"
        })

        print(f"  ✓ パターン{pattern['pattern_id']}生成完了（{result['character_count']}文字）")

    return scenario_patterns


def save_scenarios(book_name: str, scenarios: List[Dict[str, Any]]) -> Path:
    """
    生成したシナリオパターンを保存

    Args:
        book_name: 書籍名
        scenarios: シナリオパターンのリスト

    Returns:
        保存先パス
    """
    project_root = get_project_root()
    internal_dir = project_root / "data" / "internal"
    internal_dir.mkdir(parents=True, exist_ok=True)

    scenarios_file = internal_dir / "scenarios.json"

    scenarios_data = {
        "book_name": book_name,
        "patterns": scenarios,
        "total_patterns": len(scenarios)
    }

    save_json(scenarios_file, scenarios_data)
    print(f"  💾 シナリオデータを保存: {scenarios_file}")

    return scenarios_file


def regenerate_scenario(book_name: str, summary: str, pattern_id: int, target_audience: str = "", book_type: str = "") -> Dict[str, Any]:
    """
    特定のパターンのシナリオを再生成

    Args:
        book_name: 書籍名
        summary: 論文形式の書籍概要
        pattern_id: 再生成するパターンID（1-3）
        target_audience: 想定される読者層
        book_type: 書籍の種類

    Returns:
        再生成されたシナリオパターン
    """
    print(f"  🔄 パターン{pattern_id}を再生成中...")

    # 全パターンを生成（該当パターンのみ返す）
    all_scenarios = generate_scenarios_from_summary(book_name, summary, target_audience, book_type)

    for scenario in all_scenarios:
        if scenario['pattern_id'] == pattern_id:
            return scenario

    raise ValueError(f"パターンID {pattern_id} が見つかりません（1-3の範囲で指定してください）")


def select_scenario(pattern_id: int, aspect_ratio: str = "9:16", visual_style: str = "Cinematic", num_scenes: int = 5) -> Dict[str, Any]:
    """
    選択されたシナリオパターンを保存

    Args:
        pattern_id: 選択されたパターンID (1-3)
        aspect_ratio: 動画の比率 (16:9, 9:16, 1:1)
        visual_style: ビジュアルスタイル
        num_scenes: シーン数（デフォルト5）

    Returns:
        選択されたシナリオ情報
    """
    project_root = get_project_root()
    scenarios_file = project_root / "data" / "internal" / "scenarios.json"

    if not scenarios_file.exists():
        raise FileNotFoundError("シナリオファイルが見つかりません。先にgenerate_scenarios_from_summary()を実行してください。")

    from .utils import load_json

    scenarios_data = load_json(scenarios_file)
    selected_pattern = None

    for pattern in scenarios_data['patterns']:
        if pattern['pattern_id'] == pattern_id:
            selected_pattern = pattern
            break

    if not selected_pattern:
        raise ValueError(f"パターンID {pattern_id} が見つかりません")

    # 選択情報を保存
    scenario_data = {
        "book_name": scenarios_data['book_name'],
        "selected_pattern": selected_pattern,
        "aspect_ratio": aspect_ratio,
        "visual_style": visual_style,
        "num_scenes": num_scenes
    }

    scenario_file = project_root / "data" / "internal" / "scenario.json"
    save_json(scenario_file, scenario_data)

    return scenario_data
