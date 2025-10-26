#!/usr/bin/env python3
"""
EPUBファイルの解析モジュール

EPUBからテキストを抽出（v1非依存）
"""

import json
from pathlib import Path
from typing import Dict, Any
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from .utils import save_json, get_project_root


def extract_text_from_epub(epub_path: Path) -> str:
    """
    EPUBファイルからテキストを抽出

    Args:
        epub_path: EPUBファイルのパス

    Returns:
        抽出されたテキスト
    """
    book = epub.read_epub(str(epub_path))

    text_content = []

    # すべてのドキュメントアイテムを取得
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            # HTMLコンテンツをパース
            soup = BeautifulSoup(item.get_content(), 'html.parser')

            # テキストを抽出
            text = soup.get_text(separator='\n', strip=True)

            if text:
                text_content.append(text)

    # すべてのテキストを結合
    full_text = '\n\n'.join(text_content)

    return full_text


def parse_epub(epub_path: Path, output_dir: Path) -> Dict[str, Any]:
    """
    EPUBファイルをテキストに変換し、基本情報を返す

    Args:
        epub_path: EPUBファイルのパス
        output_dir: 出力先ディレクトリ（data/raw/）

    Returns:
        基本情報の辞書
    """
    print(f"  📖 EPUBファイルを解析中: {epub_path.name}")

    # EPUBからテキストを抽出
    full_text = extract_text_from_epub(epub_path)

    # 書籍名（ファイル名から）
    book_name = epub_path.stem

    # 出力ディレクトリを作成
    output_dir.mkdir(parents=True, exist_ok=True)

    # テキストファイルとして保存
    text_file = output_dir / f"{book_name}.txt"
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(full_text)

    print(f"  ✓ テキスト抽出完了: {len(full_text)}文字")

    # EPUBファイルもコピー
    epub_dest = output_dir / epub_path.name
    if not epub_dest.exists():
        import shutil
        shutil.copy2(epub_path, epub_dest)

    # 基本情報を作成
    summary = {
        "book_name": book_name,
        "original_file": str(epub_dest),
        "text_file": str(text_file),
        "full_text": full_text,  # 後続処理で使用
        "character_count": len(full_text),
        "preview": full_text[:500] + "..." if len(full_text) > 500 else full_text,
        "status": "parsed"
    }

    # data/internal/に基本情報を保存
    internal_dir = get_project_root() / "data" / "internal"
    internal_dir.mkdir(parents=True, exist_ok=True)
    basic_info_file = internal_dir / "basic_info.json"

    save_data = {k: v for k, v in summary.items() if k != 'full_text'}  # full_textは除外
    save_json(basic_info_file, save_data)

    print(f"  💾 基本情報を保存: {basic_info_file}")

    return summary
