#!/usr/bin/env python3
"""
動画レンダリングモジュール v2

moviepyを使用して、シーン画像と音声から直接動画を生成
v1スクリプトには依存しない
"""

from pathlib import Path
from typing import Dict, Any, List
import json
import subprocess

# moviepy 2.x
from moviepy import (
    ImageClip, AudioFileClip, CompositeVideoClip,
    concatenate_videoclips, TextClip, CompositeAudioClip,
    VideoFileClip
)
from moviepy import vfx

from . import subtitle_generator
import random


def get_project_root() -> Path:
    """プロジェクトルートを取得"""
    return Path(__file__).parent.parent


def apply_ken_burns_effect(clip, effect_type: str = "zoom_in", intensity: float = 1.15):
    """
    Ken Burnsエフェクトを適用（ズーム＆パン）

    Args:
        clip: ImageClip
        effect_type: "zoom_in", "zoom_out", "pan_left", "pan_right", "random"
        intensity: 拡大率（1.0～1.3推奨）

    Returns:
        エフェクト適用後のクリップ
    """
    if effect_type == "random":
        effect_type = random.choice(["zoom_in", "zoom_out", "pan_left", "pan_right"])

    w, h = clip.size
    duration = clip.duration

    if effect_type == "zoom_in":
        # ズームイン: 小→大
        # resizeを時間関数として使用
        zoomed_clip = clip.resized(lambda t: 1.0 + (intensity - 1.0) * (t / duration))
        return zoomed_clip

    elif effect_type == "zoom_out":
        # ズームアウト: 大→小
        zoomed_clip = clip.resized(lambda t: intensity - (intensity - 1.0) * (t / duration))
        return zoomed_clip

    elif effect_type == "pan_left":
        # 左→右パン（画像を拡大して左から右に移動）
        # 画像を拡大してから位置を動かす
        scaled_clip = clip.resized(intensity)
        # 左端から右端へ移動
        pan_offset = int(w * (intensity - 1))
        panned_clip = scaled_clip.with_position(lambda t: (-pan_offset + int(pan_offset * t / duration), "center"))
        return CompositeVideoClip([panned_clip], size=(w, h))

    elif effect_type == "pan_right":
        # 右→左パン（画像を拡大して右から左に移動）
        scaled_clip = clip.resized(intensity)
        pan_offset = int(w * (intensity - 1))
        panned_clip = scaled_clip.with_position(lambda t: (-int(pan_offset * t / duration), "center"))
        return CompositeVideoClip([panned_clip], size=(w, h))

    return clip


def render_video(
    storyboard_data: Dict[str, Any],
    subtitle_type: str = "normal",
    subtitle_colors: tuple = ("FFFFFF", "00FFFF"),
    use_ken_burns: bool = False,
    ken_burns_type: str = "random",
    ken_burns_intensity: float = 1.15,
    transition_type: str = "クロスフェード",
    transition_duration: float = 0.8
) -> Dict[str, Any]:
    """
    ストーリーボードから動画を作成（字幕付き）

    Args:
        storyboard_data: シーン情報
            {
                'book_name': str,
                'total_scenes': int,
                'scenes': [
                    {
                        'scene_number': int,
                        'narration': str,
                        'image_file': str,
                        'audio_file': str,
                        'duration': float
                    }
                ]
            }
        subtitle_type: 字幕タイプ ("karaoke" or "normal")

    Returns:
        生成された動画情報
    """
    project_root = get_project_root()
    book_name = storyboard_data['book_name']
    scenes = storyboard_data['scenes']

    print(f"🎬 動画生成開始: {book_name}")
    print(f"   シーン数: {len(scenes)}")

    # 出力ディレクトリ
    output_dir = project_root / "data" / "output" / "videos" / book_name
    output_dir.mkdir(parents=True, exist_ok=True)

    # 各シーンのクリップを作成
    clips = []

    for scene in scenes:
        scene_num = scene['scene_number']
        image_file = Path(scene['image_file'])
        audio_file = Path(scene['audio_file'])

        if not image_file.exists():
            raise FileNotFoundError(f"画像が見つかりません: {image_file}")
        if not audio_file.exists():
            raise FileNotFoundError(f"音声が見つかりません: {audio_file}")

        print(f"   シーン{scene_num}を処理中...")

        # 音声から実際の長さを取得
        audio_clip = AudioFileClip(str(audio_file))
        duration = audio_clip.duration

        # 画像クリップ作成（音声の長さに合わせる）
        image_clip = ImageClip(str(image_file)).with_duration(duration)

        # Ken Burnsエフェクトを適用
        if use_ken_burns:
            # エフェクトタイプを日本語から英語に変換
            effect_mapping = {
                "ズームイン": "zoom_in",
                "ズームアウト": "zoom_out",
                "左→右パン": "pan_left",
                "右→左パン": "pan_right",
                "ランダム": "random"
            }
            effect_type_en = effect_mapping.get(ken_burns_type, "random")

            print(f"     Ken Burnsエフェクト適用: {ken_burns_type} (強度: {ken_burns_intensity})")
            image_clip = apply_ken_burns_effect(image_clip, effect_type_en, ken_burns_intensity)

        # 音声を設定
        image_clip = image_clip.with_audio(audio_clip)

        # フェードイン・フェードアウト（最初と最後のシーンのみ）
        if scene_num == 1:
            image_clip = image_clip.with_effects([vfx.FadeIn(0.5)])
        if scene_num == len(scenes):
            image_clip = image_clip.with_effects([vfx.FadeOut(0.5)])

        clips.append(image_clip)

    # 全シーンを連結（遷移タイプに応じて）
    # 重要: ナレーション終了後に映像遷移を開始（字幕とのズレを防ぐ）
    if transition_type == "なし（カット）" or len(clips) <= 1:
        print("   全シーンを連結中（カット）...")
        final_clip = concatenate_videoclips(clips, method="compose")

    elif transition_type == "クロスフェード":
        print(f"   全シーンを連結中（クロスフェード: {transition_duration}秒）...")
        # ナレーション終了後にクロスフェード開始
        transition_clips = []
        for i, clip in enumerate(clips):
            if i == 0:
                # 最初のクリップはそのまま
                transition_clips.append(clip)
            else:
                # 前のクリップの最後にフェードアウトを追加（音声なし）
                prev_clip = transition_clips[-1]

                # 前のクリップの最後のフレームを使って遷移用の映像のみクリップを作成
                # 音声は含まない（without_audio）
                prev_last_frame = prev_clip.to_ImageClip(prev_clip.duration).with_duration(transition_duration)
                prev_fade = prev_last_frame.with_effects([vfx.FadeOut(transition_duration)])

                # 現在のクリップの最初にフェードインを追加
                current_first_frame = clip.to_ImageClip(0).with_duration(transition_duration)
                current_fade = current_first_frame.with_effects([vfx.FadeIn(transition_duration)])

                # クロスフェード部分を合成（音声なし）
                crossfade = CompositeVideoClip([prev_fade, current_fade], size=prev_fade.size)

                # 前のクリップ + クロスフェード + 現在のクリップを連結
                transition_clips.append(crossfade)
                transition_clips.append(clip)

        final_clip = concatenate_videoclips(transition_clips, method="compose")

    elif transition_type == "スライド":
        print(f"   全シーンを連結中（スライド: {transition_duration}秒）...")
        # ナレーション終了後にスライド開始
        transition_clips = []
        for i, clip in enumerate(clips):
            if i == 0:
                transition_clips.append(clip)
            else:
                # 前のクリップの最後のフレームでフェードアウト（音声なし）
                prev_clip = transition_clips[-1]
                prev_last_frame = prev_clip.to_ImageClip(prev_clip.duration).with_duration(transition_duration)
                prev_fade = prev_last_frame.with_effects([vfx.FadeOut(transition_duration)])

                # 現在のクリップの最初のフレームでスライドイン（音声なし）
                w, h = clip.size
                current_first_frame = clip.to_ImageClip(0).with_duration(transition_duration)
                current_slide = current_first_frame.with_position(lambda t: (int(w * (1 - t / transition_duration)), 0))

                # スライド部分を合成（音声なし）
                slide_transition = CompositeVideoClip([prev_fade, current_slide], size=(w, h))

                transition_clips.append(slide_transition)
                transition_clips.append(clip)

        final_clip = concatenate_videoclips(transition_clips, method="compose")

    else:
        # デフォルトはカット
        print("   全シーンを連結中（カット）...")
        final_clip = concatenate_videoclips(clips, method="compose")

    # 出力ファイル名
    output_file = output_dir / f"{book_name}_promotional_video.mp4"

    # 動画を書き出し
    print(f"   動画を書き出し中: {output_file.name}")
    final_clip.write_videofile(
        str(output_file),
        fps=24,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile='temp-audio.m4a',
        remove_temp=True,
        threads=4,
        preset='medium'
    )

    # クリップを解放
    final_clip.close()
    for clip in clips:
        clip.close()

    print(f"✅ 動画生成完了（字幕なし): {output_file}")

    # 字幕を追加
    if subtitle_type in ["normal", "karaoke"]:
        final_output_file = add_subtitles_to_video(
            output_file,
            scenes,
            subtitle_type,
            storyboard_data.get('aspect_ratio', '9:16'),
            subtitle_colors
        )
    else:
        final_output_file = output_file

    # 動画情報を返す
    video_data = {
        "book_name": book_name,
        "video_file": str(final_output_file),
        "subtitle_type": subtitle_type,
        "has_bgm": False,
        "total_scenes": len(scenes),
        "duration": sum([AudioFileClip(str(Path(s['audio_file']))).duration for s in scenes])
    }

    return video_data


def add_subtitles_to_video(
    video_file: Path,
    scenes: List[Dict[str, Any]],
    subtitle_type: str,
    aspect_ratio: str = "9:16",
    subtitle_colors: tuple = ("FFFFFF", "00FFFF")
) -> Path:
    """
    動画にASS字幕を追加

    Args:
        video_file: 入力動画ファイル
        scenes: シーン情報のリスト
        subtitle_type: 字幕タイプ ("karaoke" or "normal")
        aspect_ratio: アスペクト比

    Returns:
        字幕付き動画のパス
    """
    print(f"📝 字幕を追加中（{subtitle_type}）...")

    # ASS字幕ファイルを生成
    subtitle_file = video_file.parent / f"{video_file.stem}_subtitles.ass"

    if subtitle_type == "karaoke":
        subtitle_generator.create_karaoke_subtitle_file(
            scenes,
            subtitle_file,
            max_chars=15,
            aspect_ratio=aspect_ratio,
            colors=subtitle_colors
        )
    else:
        subtitle_generator.create_normal_subtitle_file(
            scenes,
            subtitle_file,
            max_chars=20,
            aspect_ratio=aspect_ratio
        )

    print(f"   字幕ファイル生成完了: {subtitle_file.name}")

    # ffmpegで字幕を焼き込み
    output_file = video_file.parent / f"{video_file.stem}_with_subtitles.mp4"

    ffmpeg_cmd = [
        'ffmpeg',
        '-i', str(video_file),
        '-vf', f"ass={subtitle_file}",
        '-c:v', 'libx264',
        '-c:a', 'copy',
        '-y',
        str(output_file)
    ]

    print(f"   字幕を動画に焼き込み中...")
    result = subprocess.run(
        ffmpeg_cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"⚠️ 字幕追加エラー（字幕なしで続行）: {result.stderr[:200]}")
        return video_file

    print(f"✅ 字幕追加完了: {output_file.name}")

    return output_file


def add_bgm_to_video(
    video_file: Path,
    bgm_file: Path,
    volume: float = 0.15
) -> Path:
    """
    動画にBGMを追加

    Args:
        video_file: 動画ファイルのパス
        bgm_file: BGMファイルのパス
        volume: BGM音量 (0.0 - 1.0)

    Returns:
        BGM付き動画のパス
    """
    if not video_file.exists():
        raise FileNotFoundError(f"動画ファイルが見つかりません: {video_file}")
    if not bgm_file.exists():
        raise FileNotFoundError(f"BGMファイルが見つかりません: {bgm_file}")

    print(f"🎵 BGMを追加中: {bgm_file.name}")

    # 動画を読み込み
    video = VideoFileClip(str(video_file))

    # BGMを読み込み（動画の長さにループ）
    bgm = AudioFileClip(str(bgm_file))

    # 音量調整
    from moviepy import afx
    bgm = bgm.with_effects([afx.MultiplyVolume(volume)])

    # BGMをループ（動画の長さに合わせる）
    if bgm.duration < video.duration:
        # BGMが短い場合はループ
        loop_count = int(video.duration / bgm.duration) + 1
        from moviepy import concatenate_audioclips
        bgm = concatenate_audioclips([bgm] * loop_count)

    # BGMを動画の長さに切り詰め
    bgm = bgm.subclipped(0, video.duration)

    # ナレーションとBGMをミックス
    if video.audio:
        mixed_audio = CompositeAudioClip([video.audio, bgm])
        video = video.with_audio(mixed_audio)
    else:
        video = video.with_audio(bgm)

    # 出力ファイル名
    output_file = video_file.parent / f"{video_file.stem}_with_bgm.mp4"

    # 動画を書き出し
    print(f"   BGM付き動画を書き出し中: {output_file.name}")
    video.write_videofile(
        str(output_file),
        fps=24,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile='temp-audio-bgm.m4a',
        remove_temp=True,
        threads=4,
        preset='medium'
    )

    # クリップを解放
    video.close()
    bgm.close()

    print(f"✅ BGM追加完了: {output_file}")

    return output_file
