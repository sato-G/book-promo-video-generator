#!/usr/bin/env python3
"""
書籍概要生成モジュール

EPUBから抽出したテキストから、論文形式の客観的な概要を生成
"""

from pathlib import Path
from typing import Dict, Any
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()


def chunk_text(text: str, chunk_size: int = 2000) -> list[str]:
    """
    テキストを指定サイズのチャンクに分割

    Args:
        text: 分割するテキスト
        chunk_size: チャンクサイズ（文字数）

    Returns:
        チャンクのリスト
    """
    chunks = []
    current_chunk = ""

    # 段落ごとに処理
    paragraphs = text.split('\n\n')

    for para in paragraphs:
        if len(current_chunk) + len(para) <= chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"

    # 最後のチャンクを追加
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def summarize_chunk(chunk: str, chunk_index: int, model) -> str:
    """
    単一チャンクの要約を生成

    Args:
        chunk: チャンクテキスト
        chunk_index: チャンク番号
        model: Gemini model

    Returns:
        要約テキスト
    """
    prompt = f"""
以下のテキスト（チャンク{chunk_index + 1}）を200-300文字で要約してください。

## テキスト
{chunk}

---

**要件:**
- 客観的・中立的に
- 主要な内容を簡潔に
- 事実ベースで

200-300文字の要約のみを出力してください。
"""

    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0.3}
    )

    return response.text.strip()


def generate_book_summary(book_name: str, full_text: str, target_length: int = 800) -> Dict[str, Any]:
    """
    書籍の客観的な概要を生成（論文形式）

    Args:
        book_name: 書籍名
        full_text: 書籍の全文テキスト
        target_length: 目標文字数（デフォルト800文字）

    Returns:
        概要情報を含む辞書
    """

    # Gemini API設定
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY環境変数が設定されていません")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash-lite')

    # テキストが長すぎる場合は最初の部分のみ使用（トークン制限対策）
    max_chars = 50000
    text_for_analysis = full_text[:max_chars] if len(full_text) > max_chars else full_text

    prompt = f"""
あなたは学術論文の要旨を書く専門家です。
以下の書籍テキストを読み、**論文の要旨（アブストラクト）形式**で客観的な概要を作成してください。

## 書籍名
{book_name}

## 書籍テキスト（抜粋）
{text_for_analysis}

---

## タスク

この書籍について、**{target_length}文字程度**の客観的な概要を作成してください。

### 要件

1. **論文の要旨形式**
   - 客観的・中立的な記述
   - 事実ベースの説明
   - 宣伝的な表現は一切使わない
   - 感情的な表現は避ける

2. **含めるべき内容**
   - 書籍の主題・テーマ
   - 扱っている内容の概要
   - 主要な論点やトピック
   - 書籍の構成（章立て等があれば）
   - 対象読者層（客観的に）
   - 書籍の特徴や独自性（ある場合）

3. **文体**
   - 「である」調の論文形式
   - 簡潔で明瞭な文章
   - 専門用語は適宜使用
   - 段落分けは適切に

4. **避けるべき表現**
   - 「面白い」「感動的」などの主観的評価
   - 「必読」「おすすめ」などの宣伝文句
   - 「ぜひ」「きっと」などの勧誘表現
   - 読者への直接的な呼びかけ

5. **文字数**
   - {target_length - 100}～{target_length + 200}文字
   - 適切な段落分けで読みやすく

---

JSON形式で出力してください。

出力形式:
{{
  "summary": "論文形式の概要本文（{target_length}文字程度）",
  "character_count": 実際の文字数,
  "main_topics": ["主要トピック1", "主要トピック2", "主要トピック3"],
  "target_audience": "想定される読者層（客観的表現）",
  "book_type": "書籍の種類（小説、実用書、学術書等）"
}}
"""

    print(f"  🤖 Gemini APIで書籍概要を生成中（目標{target_length}文字）...")
    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.3,  # 客観性を保つため低めに設定
            "response_mime_type": "application/json"
        }
    )

    result = json.loads(response.text)

    print(f"  ✓ 書籍概要生成完了（{result['character_count']}文字）")

    return result


def save_summary(summary: Dict[str, Any], book_name: str) -> Path:
    """
    生成した概要を保存

    Args:
        summary: 概要データ
        book_name: 書籍名

    Returns:
        保存先パス
    """
    from .utils import get_project_root, save_json

    project_root = get_project_root()
    internal_dir = project_root / "data" / "internal"
    internal_dir.mkdir(parents=True, exist_ok=True)

    summary_file = internal_dir / "book_summary.json"

    summary_data = {
        "book_name": book_name,
        **summary
    }

    save_json(summary_file, summary_data)
    print(f"  💾 概要データを保存: {summary_file}")

    return summary_file
