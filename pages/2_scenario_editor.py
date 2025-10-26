#!/usr/bin/env python3
"""
Page 2: シナリオ編集

3つのシナリオパターンから選択（横並び）し、内容を編集、ビジュアル設定を行う
"""

import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend import scenario_generator_v2

st.set_page_config(
    page_title="2️⃣ シナリオ編集",
    page_icon="📝",
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
.pattern-card {
    background: white;
    padding: 1.5rem;
    border-radius: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    margin-bottom: 1rem;
    transition: all 0.3s ease;
}
.pattern-card:hover {
    box-shadow: 0 4px 16px rgba(139, 92, 246, 0.2);
    transform: translateY(-2px);
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>📝 Step 2: シナリオ編集</h1><p>3つのパターンから選択してカスタマイズ</p></div>', unsafe_allow_html=True)

# サイドバー
with st.sidebar:
    st.header("📍 現在の位置")
    st.info("**Step 2/5**: シナリオ編集")

    if st.button("🏠 ホームに戻る"):
        st.switch_page("app.py")
    if st.button("← 前へ"):
        st.switch_page("pages/1_upload_epub.py")

# 前提チェック
if not st.session_state.get('book_analysis'):
    st.warning("⚠️ 先にEPUBファイルをアップロードしてください")

    # セッション復元を試みる
    from backend import session_manager, utils
    project_root = utils.get_project_root()
    sessions_dir = project_root / "data" / "internal" / "sessions"

    if sessions_dir.exists():
        session_files = list(sessions_dir.glob("session_*_latest.json"))
        if session_files:
            # 最新のセッションファイルを取得
            latest_session_file = max(session_files, key=lambda p: p.stat().st_mtime)
            book_name = latest_session_file.stem.replace('session_', '').replace('_latest', '')

            st.info(f"💾 前回のセッションが見つかりました: **{book_name}**")
            col_r1, col_r2 = st.columns(2)

            with col_r1:
                if st.button("📂 セッションを復元", use_container_width=True, type="primary"):
                    saved_session = session_manager.load_session_state(book_name)
                    if saved_session:
                        # book_analysisを復元
                        if saved_session.get('book_analysis'):
                            st.session_state.book_analysis = saved_session['book_analysis']
                        # その他のデータも復元
                        if saved_session.get('scenarios'):
                            st.session_state.scenarios = saved_session['scenarios']
                        if saved_session.get('selected_scenario'):
                            st.session_state.selected_scenario = saved_session['selected_scenario']
                        st.success("✅ セッションを復元しました")
                        st.rerun()

            with col_r2:
                if st.button("← EPUBアップロードへ", use_container_width=True):
                    st.switch_page("pages/1_upload_epub.py")

            st.stop()

    if st.button("← EPUBアップロードへ"):
        st.switch_page("pages/1_upload_epub.py")
    st.stop()

book_analysis = st.session_state.book_analysis
st.info(f"📁 書籍: **{book_analysis['book_name']}**")

# セッション復元機能
if not st.session_state.get('scenarios'):
    from backend import session_manager
    saved_session = session_manager.load_session_state(book_analysis['book_name'])
    if saved_session and saved_session.get('scenarios'):
        st.info("💾 前回のセッションが見つかりました")
        col_restore1, col_restore2 = st.columns(2)
        with col_restore1:
            if st.button("📂 前回のシナリオを復元", use_container_width=True, type="primary"):
                st.session_state.scenarios = saved_session.get('scenarios')
                if saved_session.get('selected_scenario'):
                    st.session_state.selected_scenario = saved_session.get('selected_scenario')
                if saved_session.get('selected_pattern_id'):
                    st.session_state.selected_pattern_id = saved_session.get('selected_pattern_id')
                if saved_session.get('aspect_ratio'):
                    st.session_state.aspect_ratio = saved_session.get('aspect_ratio')
                if saved_session.get('visual_style'):
                    st.session_state.visual_style = saved_session.get('visual_style')
                if saved_session.get('num_scenes'):
                    st.session_state.num_scenes = saved_session.get('num_scenes')
                st.rerun()
        with col_restore2:
            if st.button("🆕 新しくシナリオを生成", use_container_width=True):
                # 何もせず通常フローへ
                pass

# シナリオ生成
st.markdown("---")
st.subheader("🤖 AI分析")

if not st.session_state.get('scenarios'):
    st.markdown("""
    AIが書籍概要を元に、プロモーション用の3つの異なるスタイルのシナリオを自動生成します。

    **生成されるパターン:**
    - パターン1: 丁寧な解説型（500-700文字）
    - パターン2: 感情訴求型（500-700文字）
    - パターン3: 簡潔PR型（300-500文字）

    処理時間: 約30秒～1分
    """)

    if st.button("🚀 シナリオ生成を実行", type="primary", use_container_width=True):
        with st.spinner("🤖 シナリオを生成中... しばらくお待ちください"):
            try:
                # 新しいv2を使用（論文形式の概要からプロモーション用シナリオを生成）
                patterns = scenario_generator_v2.generate_scenarios_from_summary(
                    book_name=book_analysis['book_name'],
                    summary=book_analysis['summary'],
                    target_audience=book_analysis.get('target_audience', ''),
                    book_type=book_analysis.get('book_type', '')
                )

                # シナリオを保存
                scenario_generator_v2.save_scenarios(book_analysis['book_name'], patterns)

                st.session_state.scenarios = patterns

                # セッション保存
                from backend import session_manager
                session_manager.save_session_state({
                    'book_analysis': book_analysis,
                    'scenarios': patterns
                }, book_analysis['book_name'])

                st.success(f"✅ {len(patterns)}個のシナリオパターンを生成しました！")
                st.balloons()
                st.rerun()

            except Exception as e:
                st.error(f"❌ エラーが発生しました: {str(e)}")
                st.exception(e)
else:
    st.success(f"✅ {len(st.session_state.scenarios)}個のシナリオパターンが生成済みです")

# シナリオ選択（3パターン横並び）
if st.session_state.get('scenarios'):
    st.markdown("---")
    st.subheader("📋 シナリオパターンを選択")

    # 最初の3パターンのみ表示
    patterns_to_show = st.session_state.scenarios[:3]

    col1, col2, col3 = st.columns(3)
    columns = [col1, col2, col3]

    for idx, (col, pattern) in enumerate(zip(columns, patterns_to_show)):
        with col:
            # パターン見出し
            st.markdown(f"### パターン{idx + 1}")
            st.caption(f"{pattern['pattern_name']} ({pattern['character_count']}文字)")

            # 編集可能なシナリオ内容
            # 改行を適切に処理
            formatted_summary = pattern['summary'].replace('。', '。\n\n')
            edited_summary = st.text_area(
                "シナリオ内容（編集可）",
                value=formatted_summary,
                height=350,
                key=f"pattern_{pattern['pattern_id']}_text",
                disabled=False,
                label_visibility="collapsed"
            )

            # 編集内容を保存
            st.session_state.scenarios[idx]['summary'] = edited_summary

            # 選択ボタン
            is_selected = st.session_state.get('selected_pattern_id') == pattern['pattern_id']
            if st.button(
                f"{'✅ 選択中' if is_selected else '選択'}",
                key=f"select_{pattern['pattern_id']}",
                type="primary" if is_selected else "secondary",
                use_container_width=True
            ):
                st.session_state.selected_pattern_id = pattern['pattern_id']
                st.rerun()

# ビジュアル設定（常に表示）
if st.session_state.get('scenarios'):
    st.markdown("---")
    st.subheader("🎨 ビジュアル設定")

    if st.session_state.get('selected_pattern_id'):
        selected_id = st.session_state.selected_pattern_id
        st.success(f"✅ パターン{selected_id}が選択されています")
    else:
        st.info("👆 上からシナリオパターンを1つ選択してください")

    # アスペクト比選択
    st.markdown("### 📐 動画の比率")
    col1, col2, col3 = st.columns(3)

    with col1:
        is_selected_169 = st.session_state.get('aspect_ratio') == "16:9"
        if st.button("📺 16:9 (横型)", use_container_width=True, key="ratio_169", type="primary" if is_selected_169 else "secondary"):
            st.session_state.aspect_ratio = "16:9"
            st.rerun()

    with col2:
        is_selected_916 = st.session_state.get('aspect_ratio') == "9:16"
        if st.button("📱 9:16 (縦型)", use_container_width=True, key="ratio_916", type="primary" if is_selected_916 else "secondary"):
            st.session_state.aspect_ratio = "9:16"
            st.rerun()

    with col3:
        is_selected_11 = st.session_state.get('aspect_ratio') == "1:1"
        if st.button("⬜ 1:1 (正方形)", use_container_width=True, key="ratio_11", type="primary" if is_selected_11 else "secondary"):
            st.session_state.aspect_ratio = "1:1"
            st.rerun()

    if st.session_state.get('aspect_ratio'):
        st.info(f"✅ 選択中: {st.session_state.aspect_ratio}")

    # ビジュアルスタイル選択
    st.markdown("### 🎨 ビジュアルスタイル")

    visual_styles = [
        "Photorealistic", "Picture book", "3D cartoon", "Retro comics",
        "Anime", "Pixel art", "Cinematic", "Hyper cartoon",
        "Illustration", "Dreamtale", "Skytale", "80s film",
        "Minimalist", "Horror", "Sketchbook"
    ]

    cols_per_row = 5
    rows = [visual_styles[i:i+cols_per_row] for i in range(0, len(visual_styles), cols_per_row)]

    for row in rows:
        cols = st.columns(len(row))
        for col, style in zip(cols, row):
            with col:
                is_selected = st.session_state.get('visual_style') == style
                if st.button(
                    style,
                    key=f"style_{style}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary"
                ):
                    st.session_state.visual_style = style
                    st.rerun()

    if st.session_state.get('visual_style'):
        st.info(f"✅ 選択中: {st.session_state.visual_style}")

    # シーン数選択
    st.markdown("---")
    st.subheader("🎬 シーン数設定")

    col_scene1, col_scene2 = st.columns([1, 2])
    with col_scene1:
        num_scenes = st.number_input(
            "シーン数",
            min_value=3,
            max_value=10,
            value=st.session_state.get('num_scenes', 5),
            help="動画を何シーンに分割するか"
        )
        st.session_state.num_scenes = num_scenes

    with col_scene2:
        st.info(f"📊 動画は{num_scenes}シーンに分割されます")

    # 次へ進むボタン（常に表示）
    st.markdown("---")

    if (st.session_state.get('selected_pattern_id') and
        st.session_state.get('aspect_ratio') and
        st.session_state.get('visual_style')):
        if st.button("➡️ 次へ：ストーリーボード作成", type="primary", use_container_width=True):
            # 選択を保存（v2を使用）
            scenario_data = scenario_generator_v2.select_scenario(
                st.session_state.selected_pattern_id,
                st.session_state.aspect_ratio,
                st.session_state.visual_style,
                st.session_state.get('num_scenes', 5)
            )
            st.session_state.selected_scenario = scenario_data
            st.session_state.current_step = 3

            # セッション保存
            from backend import session_manager
            session_manager.save_session_state({
                'book_analysis': book_analysis,
                'scenarios': st.session_state.scenarios,
                'selected_scenario': scenario_data,
                'selected_pattern_id': st.session_state.selected_pattern_id,
                'aspect_ratio': st.session_state.aspect_ratio,
                'visual_style': st.session_state.visual_style,
                'num_scenes': st.session_state.num_scenes
            }, book_analysis['book_name'])

            st.success("✅ 設定を保存しました")
            st.switch_page("pages/3_storyboard.py")
    else:
        st.warning("⚠️ シナリオパターン・アスペクト比・ビジュアルスタイルをすべて選択してください")
        if st.button("次へ", type="primary", use_container_width=True, disabled=True):
            pass  # ボタンを無効化して表示
