#!/usr/bin/env python3
"""
Page 5: 音声・BGM設定

ナレーション音声の生成、声の選択、BGM設定、字幕タイプ選択
"""

import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend import tts_engine_v2, bgm_manager_v2, session_manager

st.set_page_config(
    page_title="5️⃣ 音声・BGM設定",
    page_icon="🎤",
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
.settings-card {
    background: white;
    padding: 1.5rem;
    border-radius: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    margin-bottom: 1.5rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>🎤 Step 4: 音声・BGM設定</h1><p>ナレーション生成と音声設定</p></div>', unsafe_allow_html=True)

# サイドバー
with st.sidebar:
    st.header("📍 現在の位置")
    st.info("**Step 4/5**: 音声・BGM設定")

    if st.button("🏠 ホームに戻る"):
        st.switch_page("app.py")
    if st.button("← 前へ"):
        st.switch_page("pages/3_storyboard.py")

# 前提チェック
if not st.session_state.get('scenes') or not st.session_state.get('scene_images'):
    st.warning("⚠️ 先にストーリーボードを完了してください")
    if st.button("← ストーリーボードへ"):
        st.switch_page("pages/3_storyboard.py")
    st.stop()

scenes = st.session_state.scenes
scenario = st.session_state.selected_scenario

st.info(f"📁 書籍: **{scenario['book_name']}** / 全{len(scenes)}シーン")

# ナレーション音声生成
st.markdown("---")
st.subheader("🎤 ナレーション音声生成")

with st.container():
    # 音声設定
    st.markdown("### 🎙️ 音声設定")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("**声の種類を選択**")

        voice_descriptions = {
            "nova": "🌟 Nova - 明るく活発な女性の声（日本語推奨）",
            "shimmer": "✨ Shimmer - 柔らかく落ち着いた女性の声",
            "alloy": "⚖️ Alloy - 中性的でバランスの取れた声",
            "echo": "🎭 Echo - 落ち着いた男性の声",
            "fable": "🎩 Fable - イギリス英語風の男性の声",
            "onyx": "💼 Onyx - 力強く深みのある男性の声"
        }

        voice_name = st.radio(
            "声の種類",
            options=["nova", "shimmer", "alloy", "echo", "fable", "onyx"],
            format_func=lambda x: voice_descriptions[x],
            index=0,  # nova
            label_visibility="collapsed"
        )

    with col2:
        voice_model = st.selectbox(
            "音質",
            ["tts-1-hd", "tts-1"],
            index=0,
            help="tts-1-hd: 高品質（推奨）\ntts-1: 標準品質（高速）"
        )

        voice_speed = st.slider(
            "読み上げ速度",
            min_value=0.5,
            max_value=2.0,
            value=1.2,
            step=0.1,
            help="1.0 = 通常速度、1.2 = やや速め（推奨）"
        )

    st.markdown("---")

    # 全シーンのナレーション統合
    full_narration = " ".join([scene['narration'] for scene in scenes])
    st.text_area(
        "生成するナレーション（全シーン統合）",
        value=full_narration,
        height=150,
        disabled=True,
        label_visibility="visible"
    )

    st.caption(f"📊 合計文字数: {len(full_narration)}文字")

    # ナレーション生成ボタン
    if 'scene_audio' not in st.session_state:
        st.markdown("""
        **処理時間:** 約30-60秒

        OpenAI TTSを使用して、高品質な日本語ナレーションを生成します。
        """)

        if st.button("🚀 ナレーション音声を生成", type="primary", use_container_width=True):
            with st.spinner("🎤 ナレーション音声を生成中..."):
                try:
                    # v2を使用（各シーンのナレーションから音声を生成）
                    scene_audio = tts_engine_v2.synthesize_narration_for_scenes(
                        scenes=scenes,
                        book_name=scenario['book_name'],
                        voice=voice_name,
                        speed=voice_speed,
                        model=voice_model
                    )

                    st.session_state.scene_audio = scene_audio
                    st.session_state.voice_settings = {
                        'voice_name': voice_name,
                        'voice_model': voice_model,
                        'voice_speed': voice_speed
                    }

                    # セッション保存
                    session_manager.save_session_state({
                        'scenes': scenes,
                        'scene_images': st.session_state.scene_images,
                        'scene_audio': scene_audio,
                        'selected_scenario': scenario,
                        'voice_settings': st.session_state.voice_settings
                    }, scenario['book_name'])

                    st.success("✅ ナレーション音声を生成しました！")
                    st.balloons()
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ エラーが発生しました: {str(e)}")
                    st.exception(e)
    else:
        st.success("✅ ナレーション音声生成済み")

        scene_audio = st.session_state.scene_audio

        # 各シーンの音声プレビュー
        for scene_num, audio_path in scene_audio.items():
            with st.expander(f"🎤 シーン{scene_num}の音声"):
                if audio_path.exists():
                    st.audio(str(audio_path))

        if st.button("🔄 再生成", use_container_width=True):
            del st.session_state.scene_audio
            st.rerun()

# 字幕設定
st.markdown("---")
st.subheader("📝 字幕設定")

with st.container():
    col_sub1, col_sub2 = st.columns(2)

    with col_sub1:
        subtitle_type = st.radio(
            "字幕タイプ",
            ["カラオケ字幕（文字単位でハイライト）", "通常字幕（シンプル表示）"],
            key="subtitle_type_radio"
        )

        subtitle_type_value = "karaoke" if subtitle_type.startswith("カラオケ") else "normal"
        st.session_state.subtitle_type = subtitle_type_value

    with col_sub2:
        subtitle_color = st.radio(
            "字幕色",
            ["白色 → 黄色", "白色 → 水色", "白色 → ピンク", "白色のみ"],
            index=0,
            help="カラオケ字幕のハイライトカラー"
        )

        # 色の設定を保存
        color_mapping = {
            "白色 → 黄色": ("FFFFFF", "00FFFF"),  # 白→黄
            "白色 → 水色": ("FFFFFF", "FFFF00"),  # 白→シアン
            "白色 → ピンク": ("FFFFFF", "FF69B4"),  # 白→ピンク
            "白色のみ": ("FFFFFF", "FFFFFF")  # 白→白
        }

        st.session_state.subtitle_colors = color_mapping[subtitle_color]

# BGM設定
st.markdown("---")
st.subheader("🎵 BGM設定")

with st.container():
    use_bgm = st.checkbox("BGMを追加する", value=True, help="デフォルトで有効")

    selected_bgm = None
    bgm_volume = 0.15

    # BGMファイル一覧取得（常に表示）
    bgm_files = bgm_manager_v2.list_available_bgm()

    if bgm_files and use_bgm:
        col_bgm1, col_bgm2 = st.columns([2, 1])

        with col_bgm1:
            st.markdown("**BGMを選択**")

            # BGM名から表示用の名前を作成
            bgm_display_names = {
                "natsuyasuminotanken.mp3": "🌻 夏休みの探検 - 明るく軽快",
                "neonpurple.mp3": "💜 ネオンパープル - モダンでクール",
                "yoiyaminoseaside.mp3": "🌊 宵闇のシーサイド - 落ち着いた雰囲気",
                "yume.mp3": "💭 夢 - 柔らかく幻想的"
            }

            # BGM選択（ラジオボタン）
            bgm_options = [f.name for f in bgm_files]
            selected_bgm_name = st.radio(
                "BGM選択",
                options=bgm_options,
                format_func=lambda x: bgm_display_names.get(x, x),
                index=0,
                label_visibility="collapsed"
            )

            selected_bgm = next(f for f in bgm_files if f.name == selected_bgm_name)

            # プレビュー
            if selected_bgm.exists():
                st.audio(str(selected_bgm))

        with col_bgm2:
            # 音量調整
            bgm_volume = st.slider(
                "BGM音量",
                min_value=0.0,
                max_value=1.0,
                value=0.15,
                step=0.05,
                help="0.0 = 無音、1.0 = 最大音量"
            )

            st.metric("音量レベル", f"{int(bgm_volume * 100)}%")

    elif not bgm_files:
        st.warning("⚠️ BGMファイルが見つかりません")

    # 設定を保存
    st.session_state.use_bgm = use_bgm
    st.session_state.selected_bgm = str(selected_bgm) if selected_bgm else None
    st.session_state.bgm_volume = bgm_volume

# Ken Burnsエフェクト設定
st.markdown("---")
st.subheader("🎬 映像エフェクト")

with st.container():
    use_ken_burns = st.checkbox(
        "Ken Burnsエフェクトを適用（画像にズーム＆パン効果）",
        value=True,
        help="静止画像にゆっくりとしたズームとパンの動きを追加します。ショート動画っぽい雰囲気になります。"
    )

    if use_ken_burns:
        col_kb1, col_kb2 = st.columns(2)

        with col_kb1:
            ken_burns_type = st.radio(
                "エフェクトタイプ",
                ["ズームイン", "ズームアウト", "左→右パン", "右→左パン", "ランダム"],
                index=4,
                help="ランダム: 各シーンで異なる動きを自動選択"
            )

        with col_kb2:
            ken_burns_intensity = st.slider(
                "エフェクトの強さ",
                min_value=1.0,
                max_value=1.3,
                value=1.15,
                step=0.05,
                help="1.0 = 動きなし、1.3 = 大きな動き"
            )
            st.caption(f"拡大率: {int((ken_burns_intensity - 1) * 100)}%")

    # 設定を保存
    st.session_state.use_ken_burns = use_ken_burns
    if use_ken_burns:
        st.session_state.ken_burns_type = ken_burns_type
        st.session_state.ken_burns_intensity = ken_burns_intensity

    st.markdown("---")

    # クロスフェード遷移設定
    use_crossfade = st.checkbox(
        "シーン間にクロスフェード遷移を追加",
        value=True,
        help="シーンとシーンの切り替わりを滑らかにします"
    )

    if use_crossfade:
        crossfade_duration = st.slider(
            "クロスフェード時間（秒）",
            min_value=0.3,
            max_value=2.0,
            value=0.8,
            step=0.1,
            help="シーン間の重なり時間"
        )
    else:
        crossfade_duration = 0.0

    # 設定を保存
    st.session_state.use_crossfade = use_crossfade
    st.session_state.crossfade_duration = crossfade_duration

# 次へ進むボタン
st.markdown("---")

if st.session_state.get('scene_audio'):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("➡️ 次へ：プレビュー・ダウンロード", type="primary", use_container_width=True):
            st.session_state.current_step = 6
            st.switch_page("pages/6_preview_download.py")
else:
    st.warning("⚠️ ナレーション音声を生成してください")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.button("次へ", type="primary", use_container_width=True, disabled=True)
