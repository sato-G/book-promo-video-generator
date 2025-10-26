#!/usr/bin/env python3
"""
Page 1: EPUBアップロード＆概要抽出

EPUBファイルをアップロード→テキスト変換→チャンク分け→概要抽出まで実行
"""

import streamlit as st
from pathlib import Path
import sys

# backend モジュールのパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend import book_analyzer

st.set_page_config(
    page_title="1️⃣ EPUBアップロード＆概要抽出",
    page_icon="📚",
    layout="wide"
)

# カスタムCSS
st.markdown("""
<style>
.main-header {
    text-align: center;
    padding: 2rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 1rem;
    margin-bottom: 2rem;
}
.upload-section {
    background: white;
    padding: 2rem;
    border-radius: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.result-section {
    background: white;
    padding: 2rem;
    border-radius: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    min-height: 400px;
}
.process-step {
    padding: 1rem;
    margin: 0.5rem 0;
    border-left: 4px solid #8B5CF6;
    background: #F0F2F6;
    border-radius: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>📚 Step 1: EPUBアップロード＆概要抽出</h1><p>書籍ファイルを解析して概要を生成します</p></div>', unsafe_allow_html=True)

# サイドバー
with st.sidebar:
    st.header("📍 現在の位置")
    st.info("**Step 1/5**: EPUBアップロード")

    if st.button("🏠 ホームに戻る"):
        st.switch_page("app.py")

# メインコンテンツ：左右2カラム
col_left, col_right = st.columns([1, 1])

# 左側：アップロードエリア
with col_left:
    st.markdown("### 📖 EPUBファイルをアップロード")

    uploaded_file = st.file_uploader(
        "ファイルを選択",
        type=['epub'],
        help="EPUB形式の電子書籍ファイルに対応しています"
    )

    if uploaded_file:
        st.success(f"✅ {uploaded_file.name}")
        st.info(f"📊 サイズ: {uploaded_file.size / 1024:.1f} KB")

        # 解析＆概要生成ボタン
        if st.button("🚀 解析して概要を生成", type="primary", use_container_width=True):

            progress_placeholder = st.empty()
            status_placeholder = st.empty()

            try:
                # EPUBファイルを保存
                output_dir = Path("data/raw")
                output_dir.mkdir(parents=True, exist_ok=True)

                epub_path = output_dir / uploaded_file.name
                with open(epub_path, 'wb') as f:
                    f.write(uploaded_file.read())

                # プログレス表示用コンテナ
                progress_container = st.container()

                with progress_container:
                    # Step 1: テキスト抽出
                    st.markdown('<div class="process-step">📄 Step 1/4: テキスト抽出中...</div>', unsafe_allow_html=True)

                    # Step 2: チャンク化（book_analyzer内で実行）
                    st.markdown('<div class="process-step">🔍 Step 2/4: チャンク化中...</div>', unsafe_allow_html=True)

                    # Step 3: チャンクまとめ（book_analyzer内で実行）
                    st.markdown('<div class="process-step">📝 Step 3/4: 各チャンクをまとめ中...</div>', unsafe_allow_html=True)

                    # Step 4: 全体概要生成（book_analyzer内で実行）
                    st.markdown('<div class="process-step">✨ Step 4/4: 全体概要を生成中...</div>', unsafe_allow_html=True)

                # 新しいbook_analyzerを使用（チャンク化→チャンクまとめ→論文形式概要まで全自動）
                result = book_analyzer.analyze_book(epub_path, output_dir)

                # セッション状態に保存
                st.session_state.book_analysis = result
                st.session_state.current_step = 2

                progress_placeholder.empty()
                status_placeholder.success("✅ 書籍分析が完了しました！")
                st.balloons()
                st.rerun()

            except Exception as e:
                progress_placeholder.empty()
                status_placeholder.error(f"❌ エラー: {str(e)}")
                st.exception(e)

    else:
        st.markdown("""
        **対応ファイル形式:**
        - EPUB (.epub)

        **推奨ファイルサイズ:**
        - 10MB以下

        **処理時間:**
        - 約1-2分
        """)

# 右側：結果表示エリア
with col_right:
    st.markdown("### 📊 書籍概要")

    if st.session_state.get('book_analysis'):
        result = st.session_state.book_analysis

        # 書籍情報
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("書籍名", result['book_name'])
        with col_b:
            st.metric("文字数", f"{result['character_count']:,}")
        with col_c:
            st.metric("チャンク数", result['num_chunks'])

        st.markdown("---")

        # 論文形式の概要表示
        st.markdown("**📝 書籍の概要（論文形式）:**")
        st.caption(f"{result['character_count']}文字 | {result['book_type']}")
        st.info("💡 この概要は、書籍の内容を客観的に説明したものです（論文の要旨形式）。この内容を確認・修正した上で、次のステップでプロモーション用シナリオを作成します。")

        # 編集可能な概要
        edited_summary = st.text_area(
            "概要内容（編集可）",
            value=result['summary'],
            height=350,
            disabled=False,
            label_visibility="collapsed",
            key="summary_edit"
        )

        # 編集内容を保存
        st.session_state.book_analysis['summary'] = edited_summary

        # 主要トピック表示
        with st.expander("📌 主要トピック"):
            for topic in result['main_topics']:
                st.write(f"- {topic}")

        # チャンクまとめを表示（デバッグ・確認用）
        with st.expander("🔍 チャンクまとめ（詳細）"):
            for i, chunk_summary in enumerate(result['chunk_summaries']):
                st.markdown(f"**チャンク{i+1}:**")
                st.write(chunk_summary)
                st.markdown("---")

        st.markdown("---")

        # シナリオ作成へのボタン
        if st.button("➡️ シナリオ作成へ進む", type="primary", use_container_width=True):
            st.switch_page("pages/2_scenario_editor.py")

    else:
        st.info("👈 左側からEPUBファイルをアップロードしてください")
        st.markdown("""
        **処理内容:**
        1. EPUBからテキストを抽出
        2. テキストを40000文字ずつチャンクに分割
        3. 各チャンクを1000-1500文字に要約
        4. チャンクまとめから論文形式の全体概要を生成（800文字程度）

        **生成される概要の特徴:**
        - 論文の要旨（アブストラクト）形式
        - 客観的・中立的な記述
        - 宣伝的表現なし
        - 事実ベースの内容説明

        処理完了後、ここに結果が表示されます。
        """)
