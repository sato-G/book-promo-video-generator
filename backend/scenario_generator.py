#!/usr/bin/env python3
"""
シナリオ生成モジュール

既存のstep1-4のスクリプトをラップして5パターンのシナリオを生成
"""

from pathlib import Path
from typing import Dict, Any, List
from .utils import run_script, get_v1_src_path, save_json, load_json, get_project_root


def generate_scenarios(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    書籍概要から5つのシナリオパターンを生成

    処理フロー:
    1. step1: テキスト分割
    2. step2: チャンク分析
    3. step3: 要約統合
    4. step4: 最終要約（5パターン生成）

    Args:
        summary: parse_epub()で生成された概要情報

    Returns:
        5つのシナリオパターンのリスト
    """
    book_name = summary['book_name']
    text_file = Path(summary['text_file'])

    if not text_file.exists():
        raise FileNotFoundError(f"テキストファイルが見つかりません: {text_file}")

    v1_src = get_v1_src_path()
    project_root = get_project_root()

    # Step 1: テキスト分割
    print("📄 Step 1: テキスト分割中...")
    script1 = v1_src / "step1_split_text.py"
    success, output = run_script(str(script1), str(text_file))
    if not success:
        raise RuntimeError(f"Step 1エラー: {output}")

    # Step 2: チャンク分析
    print("🔍 Step 2: チャンク分析中...")
    chunks_index = project_root / "v1" / "data" / "chunks" / book_name / "index.json"
    script2 = v1_src / "step2_analyze_chunks.py"
    success, output = run_script(str(script2), str(chunks_index))
    if not success:
        raise RuntimeError(f"Step 2エラー: {output}")

    # Step 3: 要約統合
    print("📊 Step 3: 要約統合中...")
    summaries_file = project_root / "v1" / "data" / "summaries" / book_name / "chunk_summaries_1000char.json"
    script3 = v1_src / "step3_integrate_summaries.py"
    success, output = run_script(str(script3), str(summaries_file))
    if not success:
        raise RuntimeError(f"Step 3エラー: {output}")

    # Step 4: 最終要約（5パターン）
    print("✨ Step 4: 5パターン生成中...")
    integrated_file = project_root / "v1" / "data" / "summaries" / book_name / "integrated_1000char_summaries.json"
    script4 = v1_src / "step4_create_final_summary.py"
    success, output = run_script(str(script4), str(integrated_file))
    if not success:
        raise RuntimeError(f"Step 4エラー: {output}")

    # 生成されたパターンを読み込む
    patterns_dir = project_root / "v1" / "data" / "final_summaries" / book_name
    patterns = []

    for pattern_file in sorted(patterns_dir.glob("pattern*.json")):
        pattern_data = load_json(pattern_file)
        patterns.append({
            "pattern_id": pattern_data['pattern_info']['pattern_id'],
            "pattern_name": pattern_data['pattern_info']['pattern_name'],
            "summary": pattern_data['pattern_info']['summary'],
            "character_count": pattern_data['pattern_info']['character_count'],
            "target_audience": pattern_data['pattern_info']['target_audience'],
            "tone": pattern_data['pattern_info']['tone'],
            "use_case": pattern_data['pattern_info']['use_case'],
            "source_file": str(pattern_file)
        })

    # data/internal/scenarios.jsonに保存
    internal_dir = project_root / "data" / "internal"
    internal_dir.mkdir(parents=True, exist_ok=True)
    scenarios_file = internal_dir / "scenarios.json"

    scenarios_data = {
        "book_name": book_name,
        "patterns": patterns,
        "total_patterns": len(patterns)
    }
    save_json(scenarios_file, scenarios_data)

    print(f"✅ {len(patterns)}個のシナリオパターンを生成しました")

    return patterns


def select_scenario(pattern_id: int, aspect_ratio: str = "9:16", visual_style: str = "Cinematic") -> Dict[str, Any]:
    """
    選択されたシナリオパターンを保存

    Args:
        pattern_id: 選択されたパターンID (1-5)
        aspect_ratio: 動画の比率 (16:9, 9:16, 1:1)
        visual_style: ビジュアルスタイル

    Returns:
        選択されたシナリオ情報
    """
    project_root = get_project_root()
    scenarios_file = project_root / "data" / "internal" / "scenarios.json"

    if not scenarios_file.exists():
        raise FileNotFoundError("シナリオファイルが見つかりません。先にgenerate_scenarios()を実行してください。")

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
        "visual_style": visual_style
    }

    scenario_file = project_root / "data" / "internal" / "scenario.json"
    save_json(scenario_file, scenario_data)

    return scenario_data
