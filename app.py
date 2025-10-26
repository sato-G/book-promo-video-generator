#!/usr/bin/env python3
"""
書籍プロモーション動画自動生成アプリ v2.0

Streamlitベースのマルチページアプリケーション
"""

import streamlit as st
from pathlib import Path

# ページ設定
st.set_page_config(
    page_title="📚 書籍プロモーション動画生成 v2",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS（UIリファレンスを参考）
st.markdown("""
<style>
:root {
    --primary-color: #8B5CF6;
    --secondary-color: #06B6D4;
    --success-color: #10B981;
}

.main-header {
    text-align: center;
    padding: 2rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 1rem;
    margin-bottom: 2rem;
}

.step-card {
    background: white;
    padding: 1.5rem;
    border-radius: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    margin-bottom: 1.5rem;
    transition: all 0.3s ease;
}

.step-card:hover {
    box-shadow: 0 4px 16px rgba(139, 92, 246, 0.2);
    transform: translateY(-2px);
}

.step-badge {
    display: inline-block;
    padding: 0.5rem 1rem;
    margin: 0.25rem;
    border-radius: 2rem;
    background: #f0f0f0;
    font-size: 0.9rem;
}

.step-badge.completed {
    background: #10B981;
    color: white;
}

.step-badge.current {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# セッション状態の初期化
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1

if 'summary' not in st.session_state:
    st.session_state.summary = None

if 'scenarios' not in st.session_state:
    st.session_state.scenarios = None

if 'selected_scenario' not in st.session_state:
    st.session_state.selected_scenario = None

if 'storyboard' not in st.session_state:
    st.session_state.storyboard = None

if 'video_data' not in st.session_state:
    st.session_state.video_data = None


def main():
    """メインページ"""

    st.markdown('<div class="main-header"><h1>📚 書籍プロモーション動画生成 v2</h1><p>EPUBから自動で高品質なプロモーション動画を作成</p></div>', unsafe_allow_html=True)

    # サイドバー
    with st.sidebar:
        st.header("📍 ナビゲーション")

        # ステップ表示
        steps = [
            ("1️⃣ EPUBアップロード", "pages/1_upload_epub.py"),
            ("2️⃣ シナリオ選択", "pages/2_scenario_editor.py"),
            ("3️⃣ ストーリーボード", "pages/3_storyboard.py"),
            ("4️⃣ 音声・BGM設定", "pages/5_audio_settings.py"),
            ("5️⃣ プレビュー＆ダウンロード", "pages/6_preview_download.py")
        ]

        for i, (label, page) in enumerate(steps, 1):
            if i == st.session_state.current_step:
                st.markdown(f'<div class="step-badge current">{label}</div>', unsafe_allow_html=True)
            elif i < st.session_state.current_step:
                st.markdown(f'<div class="step-badge completed">{label}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="step-badge">{label}</div>', unsafe_allow_html=True)

        st.markdown("---")

        # デバッグ情報
        with st.expander("🔧 デバッグ情報"):
            st.write("現在のステップ:", st.session_state.current_step)
            st.write("Summary:", "✅" if st.session_state.get('summary') else "❌")
            st.write("Scenarios:", "✅" if st.session_state.get('scenarios') else "❌")
            st.write("Selected:", "✅" if st.session_state.get('selected_scenario') else "❌")
            st.write("Scenes:", "✅" if st.session_state.get('scenes') else "❌")
            st.write("Scene Images:", f"✅ {len(st.session_state.get('scene_images', {}))}" if st.session_state.get('scene_images') else "❌")
            st.write("Narration:", "✅" if st.session_state.get('narration_audio') else "❌")
            st.write("Final Video:", "✅" if st.session_state.get('final_video') else "❌")

        st.markdown("---")

        # セッション復元機能
        with st.expander("📂 セッション復元（開発用）"):
            st.caption("画像生成まで完了したセッションを読み込んで、途中から再開できます")

            # backend読み込み
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            from backend import session_manager

            # 利用可能なセッション一覧
            sessions = session_manager.get_saved_sessions()
            if sessions:
                # 書籍名を抽出
                book_names = set()
                for session_path in sessions:
                    filename = session_path.name
                    if 'latest' in filename:
                        book_name = filename.replace('session_', '').replace('_latest.json', '')
                        book_names.add(book_name)

                if book_names:
                    selected_book = st.selectbox(
                        "書籍を選択",
                        sorted(book_names),
                        key="restore_book_select"
                    )

                    if st.button("🔄 このセッションを復元", use_container_width=True):
                        session_data = session_manager.load_session_state(selected_book, use_latest=True)
                        if session_data:
                            # session_stateに復元
                            st.session_state.scenes = session_data.get('scenes', [])
                            st.session_state.scene_images = {
                                int(k): Path(v) for k, v in session_data.get('scene_images', {}).items()
                            }
                            st.session_state.selected_scenario = session_data.get('selected_scenario')
                            if 'scene_audio' in session_data:
                                st.session_state.scene_audio = {
                                    int(k): Path(v) for k, v in session_data['scene_audio'].items()
                                }
                            st.session_state.current_step = 4  # 音声・BGM設定へ

                            st.success(f"✅ セッション復元完了: {selected_book}")
                            st.info("画面4（音声・BGM設定）から再開できます")
                            st.rerun()
                        else:
                            st.error("セッションの読み込みに失敗しました")
                else:
                    st.info("復元可能なセッションがありません")
            else:
                st.info("保存されたセッションがありません")

        st.markdown("---")

        if st.button("🔄 すべてリセット"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # メインコンテンツ
    st.markdown("""
    ## 🚀 はじめに

    このアプリでは、EPUBファイルから自動的にプロモーション動画を作成できます。

    ### 📋 処理フロー

    1. **EPUBアップロード** - 書籍ファイルをアップロードして解析
    2. **シナリオ選択** - AIが生成した3つのパターンから選択・編集
    3. **ストーリーボード** - シーン分割＆画像自動生成、ナレーション編集
    4. **音声・BGM設定** - ナレーション音声生成、BGM選択
    5. **プレビュー＆ダウンロード** - 完成した動画をダウンロード

    ### ✨ 特徴

    - **AI自動生成**: Gemini APIで書籍を分析、3つの異なるスタイルのシナリオを生成
    - **シーン分割**: AIがシナリオを最適な複数シーンに自動分割
    - **高品質ナレーション**: OpenAI TTSによる自然な日本語音声
    - **DALL-E 3画像生成**: シーンごとに最適化された高品質な画像
    - **カスタマイズ可能**: 字幕スタイル、BGM、ビジュアルスタイルなど細かく調整可能

    ---

    👈 **左のサイドバーから各ステップに進んでください**
    """)

    # データ確認セクション
    if st.session_state.summary:
        st.success("✅ EPUBファイルが読み込まれています")

        with st.expander("📖 書籍情報を見る"):
            summary = st.session_state.summary
            col1, col2 = st.columns(2)
            with col1:
                st.metric("書籍名", summary.get('book_name', 'N/A'))
                st.metric("文字数", f"{summary.get('character_count', 0):,}")
            with col2:
                st.text_area("プレビュー", summary.get('preview', ''), height=150, disabled=True)

    if st.session_state.scenarios:
        st.success(f"✅ {len(st.session_state.scenarios)}個のシナリオパターンが生成されています")

    if st.session_state.selected_scenario:
        pattern_id = st.session_state.selected_scenario.get('selected_pattern', {}).get('pattern_id', '不明')
        st.success(f"✅ パターン{pattern_id}が選択されています")

    if st.session_state.storyboard:
        st.success(f"✅ {st.session_state.storyboard['total_scenes']}シーンのストーリーボードが作成されています")

    if st.session_state.video_data:
        st.success("✅ 動画が生成されています")

    # クイックアクション
    st.markdown("---")
    st.subheader("🎬 クイックアクション")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📄 新規プロジェクト", use_container_width=True, type="primary"):
            st.switch_page("pages/1_upload_epub.py")

    with col2:
        if st.session_state.summary:
            if st.button("✏️ シナリオ編集へ", use_container_width=True):
                st.switch_page("pages/2_scenario_editor.py")

    with col3:
        if st.session_state.video_data:
            if st.button("📥 ダウンロードへ", use_container_width=True):
                st.switch_page("pages/5_preview_download.py")


if __name__ == '__main__':
    main()
