#!/usr/bin/env python3
"""
Page 6: プレビュー＆ダウンロード

動画生成、プレビュー、ダウンロード
"""

import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend import video_renderer_v2, bgm_manager_v2

st.set_page_config(
    page_title="6️⃣ 完成",
    page_icon="🎉",
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
.completion-card {
    background: white;
    padding: 2rem;
    border-radius: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    margin-bottom: 1.5rem;
    text-align: center;
}
.stats-card {
    background: #f0f0f0;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>🎉 Step 5: プレビュー＆ダウンロード</h1><p>動画の生成と完成</p></div>', unsafe_allow_html=True)

# サイドバー
with st.sidebar:
    st.header("📍 現在の位置")
    st.success("**Step 5/5**: プレビュー＆ダウンロード")

    if st.button("🏠 ホームに戻る"):
        st.switch_page("app.py")
    if st.button("← 前へ"):
        st.switch_page("pages/5_audio_settings.py")

    st.markdown("---")

    if st.button("🔄 新しいプロジェクトを開始"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("app.py")

# 前提チェック
if not st.session_state.get('scene_audio') or not st.session_state.get('scene_images'):
    st.warning("⚠️ 先に音声設定とシーン編集を完了してください")
    if st.button("← 音声設定へ"):
        st.switch_page("pages/5_audio_settings.py")
    st.stop()

scenes = st.session_state.scenes
scenario = st.session_state.selected_scenario
scene_audio = st.session_state.scene_audio

st.info(f"📁 書籍: **{scenario['book_name']}** / 全{len(scenes)}シーン")

# 動画生成
st.markdown("---")
st.subheader("🎬 動画生成")

if 'final_video' not in st.session_state:
    st.markdown("""
    全てのシーン画像とナレーション音声を組み合わせて、最終動画を生成します。

    **処理内容:**
    - シーン画像の統合
    - ナレーション音声の追加
    - 字幕の生成と追加
    - BGMの追加（設定している場合）

    **処理時間:** 約2-5分
    """)

    if st.button("🚀 最終動画を生成", type="primary", use_container_width=True):
        with st.spinner("🎬 動画を生成中...（数分かかります）"):
            try:
                # シーンデータと画像・音声パスを準備
                storyboard_data = {
                    'book_name': scenario['book_name'],
                    'scenes': [],
                    'total_scenes': len(scenes),
                    'aspect_ratio': scenario.get('aspect_ratio', '9:16')
                }

                for scene in scenes:
                    scene_num = scene['scene_number']
                    image_path = st.session_state.scene_images.get(scene_num)
                    audio_path = scene_audio.get(scene_num)

                    if image_path and audio_path:
                        storyboard_data['scenes'].append({
                            'scene_number': scene_num,
                            'narration': scene['narration'],
                            'image_file': str(image_path),
                            'audio_file': str(audio_path),
                            'duration_seconds': scene['duration_seconds']
                        })

                # 動画レンダリング（v2使用）
                video_data = video_renderer_v2.render_video(
                    storyboard_data,
                    subtitle_type=st.session_state.get('subtitle_type', 'normal'),
                    subtitle_colors=st.session_state.get('subtitle_colors', ('FFFFFF', '00FFFF')),
                    use_ken_burns=st.session_state.get('use_ken_burns', False),
                    ken_burns_type=st.session_state.get('ken_burns_type', 'ランダム'),
                    ken_burns_intensity=st.session_state.get('ken_burns_intensity', 1.15),
                    transition_type=st.session_state.get('transition_type', 'クロスフェード'),
                    transition_duration=st.session_state.get('transition_duration', 0.8)
                )

                # BGM追加
                if st.session_state.get('use_bgm') and st.session_state.get('selected_bgm'):
                    st.info("🎵 BGMを追加中...")
                    video_with_bgm = bgm_manager_v2.add_bgm(
                        video_data['video_file'],
                        st.session_state.selected_bgm,
                        volume=st.session_state.get('bgm_volume', 0.15)
                    )
                    video_data['video_file'] = video_with_bgm['output_file']
                    video_data['has_bgm'] = True
                else:
                    video_data['has_bgm'] = False

                st.session_state.final_video = video_data
                st.session_state.current_step = 6

                st.success("✅ 動画生成完了！")
                st.balloons()
                st.rerun()

            except Exception as e:
                st.error(f"❌ エラーが発生しました: {str(e)}")
                st.exception(e)
else:
    st.success("✅ 動画生成済み")

    video_data = st.session_state.final_video
    video_file = Path(video_data['video_file'])

    # 動画プレビュー
    st.markdown("---")
    st.subheader("🎬 動画プレビュー")

    if video_file.exists():
        # 動画を中央寄せで小さく表示（さらに縮小）
        col_left, col_video, col_right = st.columns([3, 2, 3])
        with col_video:
            st.video(str(video_file))

        # ファイル情報
        file_size_mb = video_file.stat().st_size / (1024 * 1024)
        st.info(f"📊 ファイルサイズ: {file_size_mb:.2f} MB")
        st.caption(f"💾 保存場所: {video_file}")
    else:
        st.error(f"❌ 動画ファイルが見つかりません: {video_file}")
        st.stop()

    # ダウンロードセクション
    st.markdown("---")
    st.subheader("📥 ダウンロード")

    # ダウンロードボタン
    with open(video_file, 'rb') as f:
        video_bytes = f.read()

    col_dl1, col_dl2, col_dl3 = st.columns([1, 2, 1])

    with col_dl2:
        st.download_button(
            label="📥 動画をダウンロード",
            data=video_bytes,
            file_name=video_file.name,
            mime="video/mp4",
            type="primary",
            use_container_width=True
        )

    # 追加アクション
    st.markdown("---")
    st.subheader("🚀 次のアクション")

    col_a1, col_a2, col_a3, col_a4 = st.columns(4)

    with col_a1:
        if st.button("📝 シナリオを変更", use_container_width=True):
            # シナリオ選択からやり直す
            keys_to_delete = ['scenes', 'scene_images', 'scene_audio', 'final_video']
            for key in keys_to_delete:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.current_step = 2
            st.switch_page("pages/2_scenario_editor.py")

    with col_a2:
        if st.button("🎬 ストーリーボード編集", use_container_width=True):
            # ストーリーボードに戻る（動画のみ削除）
            if 'final_video' in st.session_state:
                del st.session_state.final_video
            if 'scene_audio' in st.session_state:
                del st.session_state.scene_audio
            st.session_state.current_step = 3
            st.switch_page("pages/3_storyboard.py")

    with col_a3:
        if st.button("🎤 音声設定を変更", use_container_width=True):
            # 音声設定からやり直す
            if 'scene_audio' in st.session_state:
                del st.session_state.scene_audio
            if 'final_video' in st.session_state:
                del st.session_state.final_video
            st.session_state.current_step = 4
            st.switch_page("pages/5_audio_settings.py")

    with col_a4:
        if st.button("🔄 新規プロジェクト", use_container_width=True, type="secondary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state.current_step = 1
            st.switch_page("pages/1_upload_epub.py")
