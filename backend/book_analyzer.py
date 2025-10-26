#!/usr/bin/env python3
"""
書籍分析モジュール（画面1用）

EPUB → テキスト化 → チャンク化 → チャンクまとめ → 全体概要（論文形式800字）
"""

from pathlib import Path
from typing import Dict, Any, List
import google.generativeai as genai
import os
import json
import time
from dotenv import load_dotenv
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

# .envファイルから環境変数を読み込む
load_dotenv()


def extract_text_from_epub(epub_path: Path) -> str:
    """EPUBからテキストを抽出"""
    book = epub.read_epub(str(epub_path))
    text_content = []

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            text = soup.get_text(separator='\n', strip=True)
            if text:
                text_content.append(text)

    return '\n\n'.join(text_content)


def chunk_text(text: str, chunk_size: int = 40000) -> List[str]:
    """テキストをチャンクに分割（40000文字ずつ）"""
    chunks = []
    current_chunk = ""
    paragraphs = text.split('\n\n')

    for para in paragraphs:
        if len(current_chunk) + len(para) <= chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def summarize_chunks(chunks: List[str]) -> List[str]:
    """各チャンクを1000-1500文字にまとめる"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY環境変数が設定されていません")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash-lite')

    summaries = []

    for i, chunk in enumerate(chunks):
        print(f"  📝 チャンク{i+1}/{len(chunks)}をまとめ中...")

        prompt = f"""
以下のテキストを1000-1500文字で要約してください。

{chunk}

**要件:**
- 客観的・中立的に
- 主要な内容を漏らさず含める
- 事実ベース
- 詳細な要約

1000-1500文字の要約のみを出力してください。
"""

        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.3}
        )

        summaries.append(response.text.strip())

        # API制限回避のため、リクエスト間に遅延を追加
        if i < len(chunks) - 1:  # 最後のチャンク以外
            time.sleep(2)  # 2秒待機

    return summaries


def generate_final_summary(chunk_summaries: List[str], book_name: str) -> Dict[str, Any]:
    """チャンクまとめから全体概要を生成（論文形式800字）"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY環境変数が設定されていません")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash-lite')

    all_summaries = '\n\n'.join([f"【部分{i+1}】\n{s}" for i, s in enumerate(chunk_summaries)])

    prompt = f"""
あなたは学術論文の要旨を書く専門家です。
以下は書籍「{book_name}」の各部分の要約です。これを読み、**論文の要旨（アブストラクト）形式**で全体概要を作成してください。

## 各部分の要約
{all_summaries}

---

## タスク

この書籍について、**800文字程度**の客観的な概要を論文形式で作成してください。

### 要件

1. **論文の要旨形式**
   - 客観的・中立的な記述
   - 「である」調
   - 宣伝的な表現は一切使わない

2. **含めるべき内容**
   - 書籍の主題・テーマ
   - 扱っている内容の概要
   - 主要な論点
   - 書籍の構成
   - 対象読者層（客観的に）

3. **避けるべき表現**
   - 「面白い」「感動的」などの主観的評価
   - 「必読」「おすすめ」などの宣伝文句
   - 読者への呼びかけ

4. **文字数: 700-900文字**

---

JSON形式で出力してください。

出力形式:
{{
  "summary": "論文形式の概要本文",
  "character_count": 実際の文字数,
  "main_topics": ["主要トピック1", "主要トピック2", "主要トピック3"],
  "target_audience": "想定される読者層",
  "book_type": "書籍の種類"
}}
"""

    print(f"  🤖 全体概要を生成中...")
    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.3,
            "response_mime_type": "application/json"
        }
    )

    result = json.loads(response.text)
    print(f"  ✓ 全体概要生成完了（{result['character_count']}文字）")

    return result


def analyze_book(epub_path: Path, output_dir: Path) -> Dict[str, Any]:
    """
    書籍を分析（画面1の全処理）

    1. EPUBからテキスト抽出
    2. チャンク化
    3. チャンクごとにまとめ
    4. 全体概要生成（論文形式800字）

    Returns:
        分析結果の辞書
    """
    print(f"\n{'='*80}")
    print(f"📚 書籍分析開始: {epub_path.name}")
    print(f"{'='*80}\n")

    # 1. テキスト抽出
    print("📖 Step 1/4: テキスト抽出中...")
    full_text = extract_text_from_epub(epub_path)
    print(f"  ✓ {len(full_text)}文字を抽出")

    book_name = epub_path.stem

    # テキストファイルとして保存
    output_dir.mkdir(parents=True, exist_ok=True)
    text_file = output_dir / f"{book_name}.txt"
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(full_text)

    # 2. チャンク化
    print("\n🔍 Step 2/4: チャンク化中...")
    chunks = chunk_text(full_text, chunk_size=2000)
    print(f"  ✓ {len(chunks)}個のチャンクに分割")

    # 3. チャンクまとめ
    print("\n📝 Step 3/4: 各チャンクをまとめ中...")
    chunk_summaries = summarize_chunks(chunks)
    print(f"  ✓ {len(chunk_summaries)}個のまとめを生成")

    # 4. 全体概要生成
    print("\n✨ Step 4/4: 全体概要を生成中...")
    final_summary = generate_final_summary(chunk_summaries, book_name)

    # 結果をまとめる
    result = {
        "book_name": book_name,
        "text_file": str(text_file),
        "character_count": len(full_text),
        "num_chunks": len(chunks),
        "chunk_summaries": chunk_summaries,
        **final_summary
    }

    # data/internal/に保存
    from .utils import get_project_root, save_json

    internal_dir = get_project_root() / "data" / "internal"
    internal_dir.mkdir(parents=True, exist_ok=True)

    analysis_file = internal_dir / "book_analysis.json"
    save_json(analysis_file, result)

    print(f"\n{'='*80}")
    print(f"✅ 分析完了！")
    print(f"{'='*80}\n")

    return result
