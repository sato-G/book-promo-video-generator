#!/usr/bin/env python3
"""
Page 3: ストーリーボード（シーン分割＋画像生成）

シナリオを複数のシーンに分割し、各シーンの画像を自動生成
"""

import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend import scene_splitter, image_generator_v2, session_manager

st.set_page_config(
    page_title="3️⃣ ストーリーボード",
    page_icon="🎬",
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
.scene-card {
    background: white;
    padding: 1.5rem;
    border-radius: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    margin-bottom: 1.5rem;
    border-left: 4px solid #8B5CF6;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>🎬 Step 3: ストーリーボード</h1><p>シーン分割と画像生成</p></div>', unsafe_allow_html=True)

# サイドバー
with st.sidebar:
    st.header("📍 現在の位置")
    st.info("**Step 3/5**: ストーリーボード")

    if st.button("🏠 ホームに戻る"):
        st.switch_page("app.py")
    if st.button("← 前へ"):
        st.switch_page("pages/2_scenario_editor.py")

# 前提チェック
if not st.session_state.get('selected_scenario'):
    st.warning("⚠️ 先にシナリオを選択してください")
    if st.button("← シナリオ選択へ"):
        st.switch_page("pages/2_scenario_editor.py")
    st.stop()

scenario = st.session_state.selected_scenario
num_scenes = st.session_state.get('num_scenes', 5)

# 現在の設定を表示
col_info, col_edit_settings = st.columns([4, 1])

with col_info:
    st.info(f"📁 書籍: **{scenario['book_name']}** | シナリオ: **{scenario['selected_pattern']['pattern_name']}** | シーン数: {num_scenes}")
    st.caption(f"ビジュアルスタイル: {scenario.get('visual_style', 'Cinematic')} | アスペクト比: {scenario.get('aspect_ratio', '9:16')}")

with col_edit_settings:
    if st.button("⚙️ 設定変更", use_container_width=True, help="Step 2に戻って設定を変更"):
        # シーンと画像を削除してStep 2に戻る
        if 'scenes' in st.session_state:
            del st.session_state.scenes
        if 'scene_images' in st.session_state:
            del st.session_state.scene_images
        st.session_state.current_step = 2
        st.switch_page("pages/2_scenario_editor.py")

# 自動シーン分割＆画像生成
if 'scenes' not in st.session_state:
    st.markdown("---")
    st.subheader("🚀 自動処理を開始")

    st.markdown(f"""
    以下の処理を自動的に実行します：

    1. **シーン分割**: シナリオを{num_scenes}シーンに分割
    2. **画像生成**: 各シーンの画像をDALL-E 3で生成

    **推定処理時間:** 約{num_scenes * 30}秒～{num_scenes * 60}秒
    """)

    if st.button("🚀 シーン分割＆画像生成を開始", type="primary", use_container_width=True):
        # プログレスバー
        progress_container = st.container()

        with progress_container:
            # Step 1: シーン分割
            status_text = st.empty()
            status_text.markdown("### 📝 Step 1/2: シーン分割中...")

            try:
                scenes = scene_splitter.split_into_scenes(scenario, num_scenes)
                scene_splitter.save_scenes(scenes, scenario['book_name'])
                st.session_state.scenes = scenes

                status_text.success(f"✅ {len(scenes)}シーンに分割完了")

                # Step 2: 画像生成
                status_text.markdown("### 🎨 Step 2/2: 各シーンの画像を生成中...")

                progress_bar = st.progress(0)
                scene_images = {}

                for idx, scene in enumerate(scenes):
                    scene_num = scene['scene_number']
                    st.write(f"🎨 シーン{scene_num}の画像を生成中... ({idx + 1}/{len(scenes)})")

                    try:
                        # 画像生成（v2を使用）
                        generated_path = image_generator_v2.generate_image_for_scene(
                            scene_prompt=scene['image_prompt'],
                            book_name=scenario['book_name'],
                            scene_number=scene_num,
                            visual_style=scenario.get('visual_style', 'Cinematic'),
                            aspect_ratio=scenario.get('aspect_ratio', '9:16')
                        )

                        scene_images[scene_num] = generated_path

                        # 途中経過を保存（エラー時も復元可能に）
                        st.session_state.scene_images = scene_images
                        session_manager.save_session_state({
                            'scenes': scenes,
                            'scene_images': scene_images,
                            'selected_scenario': scenario
                        }, scenario['book_name'])

                    except Exception as e:
                        st.error(f"❌ シーン{scene_num}でエラー: {str(e)}")
                        # エラーが出ても途中まで保存
                        st.session_state.scene_images = scene_images
                        session_manager.save_session_state({
                            'scenes': scenes,
                            'scene_images': scene_images,
                            'selected_scenario': scenario,
                            'error_at_scene': scene_num
                        }, scenario['book_name'])

                    progress_bar.progress((idx + 1) / len(scenes))

                st.session_state.scene_images = scene_images
                st.session_state.current_step = 4

                status_text.empty()
                progress_bar.empty()
                st.success("✅ すべての処理が完了しました！")
                st.balloons()
                st.rerun()

            except Exception as e:
                st.error(f"❌ エラーが発生しました: {str(e)}")
                st.exception(e)

    st.stop()

# シーン一覧表示＆編集
st.markdown("---")

# ヘッダーと再生成ボタン
col_header, col_regen = st.columns([3, 1])

with col_header:
    st.subheader("🎬 シーン一覧")

with col_regen:
    if st.button("🔄 ストーリーボード再生成", use_container_width=True, help="Step 2の設定で新しくシーンと画像を生成"):
        # 確認ダイアログ
        st.warning("⚠️ 現在のシーンと画像がすべて削除され、新しく生成されます。")
        col_confirm1, col_confirm2 = st.columns(2)
        with col_confirm1:
            if st.button("✅ はい、再生成する", type="primary", use_container_width=True):
                # セッションから削除
                if 'scenes' in st.session_state:
                    del st.session_state.scenes
                if 'scene_images' in st.session_state:
                    del st.session_state.scene_images
                st.rerun()
        with col_confirm2:
            if st.button("❌ キャンセル", use_container_width=True):
                st.rerun()
        st.stop()

scenes = st.session_state.scenes
total_duration = sum(scene['duration_seconds'] for scene in scenes)

st.info(f"🎬 全{len(scenes)}シーン / ⏱️ 合計推定時間: {total_duration}秒")

# 各シーンカード（縦並び、左に小さい画像、右にナレーション）
for scene in scenes:
    scene_num = scene['scene_number']

    with st.container():
        st.markdown("---")

        # 左：小さい画像、右：ナレーション（1:3の比率）
        col_image, col_content = st.columns([1, 3])

        # 左側：画像プレビュー（小さく）
        with col_image:
            st.markdown(f"**🎬 シーン {scene_num}**")

            if scene_num in st.session_state.scene_images:
                image_path = st.session_state.scene_images[scene_num]
                st.image(str(image_path), use_container_width=True)

                # 画像再生成ボタン
                if st.button(f"🔄", key=f"regen_{scene_num}", help="画像を再生成"):
                    with st.spinner(f"🎨 再生成中..."):
                        try:
                            generated_path = image_generator_v2.regenerate_image_for_scene(
                                scene_prompt=scene['image_prompt'],
                                book_name=scenario['book_name'],
                                scene_number=scene_num,
                                visual_style=scenario.get('visual_style', 'Cinematic'),
                                aspect_ratio=scenario.get('aspect_ratio', '9:16')
                            )
                            st.session_state.scene_images[scene_num] = generated_path
                            st.success(f"✅ 完了")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ エラー")
            else:
                st.warning("未生成")

        # 右側：ナレーションと詳細
        with col_content:
            st.markdown(f"### シーン {scene_num}")

            # ナレーション編集
            edited_narration = st.text_area(
                "ナレーション（編集可）",
                value=scene['narration'],
                height=120,
                key=f"narration_edit_{scene_num}"
            )

            # 編集内容を保存
            scene_idx = scene_num - 1
            st.session_state.scenes[scene_idx]['narration'] = edited_narration

            col_time, col_prompt = st.columns([1, 2])

            with col_time:
                st.caption(f"⏱️ 推定時間: {scene['duration_seconds']}秒")

            with col_prompt:
                # 画像プロンプト表示
                with st.expander("🔍 画像プロンプト"):
                    st.code(scene['image_prompt'], language="text")

# シーン追加機能
st.markdown("---")
st.subheader("➕ シーン追加")

col_add1, col_add2 = st.columns([3, 1])

with col_add1:
    new_narration = st.text_area(
        "新しいシーンのナレーション",
        placeholder="追加したいシーンのナレーション内容を入力してください（60-100文字推奨）",
        height=100,
        key="new_scene_narration"
    )

with col_add2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ シーンを追加", use_container_width=True):
        if new_narration.strip():
            with st.spinner("🎨 新しいシーンの画像を生成中..."):
                try:
                    # 新しいシーンを作成
                    new_scene_num = len(scenes) + 1
                    new_scene = {
                        "scene_number": new_scene_num,
                        "narration": new_narration.strip(),
                        "image_prompt": f"Scene illustration for: {new_narration[:50]}... in {scenario.get('visual_style', 'Cinematic')} style",
                        "duration_seconds": 10
                    }

                    # 画像生成（v2を使用）
                    generated_path = image_generator_v2.generate_image_for_scene(
                        scene_prompt=new_scene['image_prompt'],
                        book_name=scenario['book_name'],
                        scene_number=new_scene_num,
                        visual_style=scenario.get('visual_style', 'Cinematic'),
                        aspect_ratio=scenario.get('aspect_ratio', '9:16')
                    )

                    # シーンリストと画像に追加
                    st.session_state.scenes.append(new_scene)
                    st.session_state.scene_images[new_scene_num] = generated_path

                    st.success(f"✅ シーン{new_scene_num}を追加しました！")
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ エラー: {str(e)}")
        else:
            st.warning("⚠️ ナレーション内容を入力してください")

# 次へ進むボタン
st.markdown("---")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    all_images_ready = all(scene['scene_number'] in st.session_state.scene_images for scene in scenes)

    if all_images_ready:
        if st.button("➡️ 次へ：音声・BGM設定", type="primary", use_container_width=True):
            st.session_state.current_step = 5
            st.switch_page("pages/5_audio_settings.py")
    else:
        st.warning("⚠️ すべてのシーンの画像が必要です")
        st.button("次へ", type="primary", use_container_width=True, disabled=True)
