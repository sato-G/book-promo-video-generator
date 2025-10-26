#!/usr/bin/env python3
"""
ASS字幕生成モジュール

カラオケ字幕（文字単位でハイライト）を生成
"""

from pathlib import Path
from typing import List, Dict, Any
from moviepy import AudioFileClip


def split_text_into_chunks(text: str, max_chars: int = 15) -> List[str]:
    """
    テキストを読みやすいチャンクに分割（句読点考慮）

    Args:
        text: テキスト
        max_chars: 1チャンクの最大文字数

    Returns:
        チャンクのリスト
    """
    chunks = []
    current_pos = 0

    while current_pos < len(text):
        # 次のチャンクを取得
        chunk_end = min(current_pos + max_chars, len(text))
        chunk_text = text[current_pos:chunk_end]

        # まだテキストが残っている場合、句読点で区切る
        if chunk_end < len(text):
            # 後ろから句読点を探す
            best_cut = -1
            for delimiter in ['。', '、', '！', '？']:
                idx = chunk_text.rfind(delimiter)
                if idx != -1 and idx > len(chunk_text) * 0.4:  # 後半40%以降にあればOK
                    best_cut = idx + 1
                    break

            if best_cut != -1:
                chunk_text = chunk_text[:best_cut]
                chunk_end = current_pos + best_cut

        chunks.append(chunk_text.strip())
        current_pos = chunk_end

    return chunks


def format_time(seconds: float) -> str:
    """
    秒数をASS形式の時刻に変換

    Args:
        seconds: 秒数

    Returns:
        ASS形式の時刻文字列（h:mm:ss.cc）
    """
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def create_karaoke_subtitle_file(
    scenes: List[Dict[str, Any]],
    output_file: Path,
    max_chars: int = 15,
    aspect_ratio: str = "9:16",
    colors: tuple = ("FFFFFF", "00FFFF")
) -> None:
    """
    ASS形式のカラオケ字幕ファイルを作成

    Args:
        scenes: シーン情報のリスト
            [{'scene_number': 1, 'narration': 'テキスト', 'duration_seconds': 10.0}, ...]
        output_file: 出力字幕ファイルパス
        max_chars: 1チャンクの最大文字数
        aspect_ratio: アスペクト比（9:16 or 16:9）
    """
    # アスペクト比に応じた解像度設定
    if aspect_ratio == "9:16":
        play_res_x = 1080
        play_res_y = 1920
        font_size = 90
        margin_v = 150
    else:  # 16:9
        play_res_x = 1920
        play_res_y = 1080
        font_size = 70
        margin_v = 100

    # ASS形式のヘッダー
    ass_content = f"""[Script Info]
Title: Book Promotion Video
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: {play_res_x}
PlayResY: {play_res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Noto Sans CJK JP,{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,3,5,60,60,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []
    current_time = 0.0

    for scene in scenes:
        text = scene['narration']

        # 音声ファイルから実際の長さを取得
        if 'audio_file' in scene and Path(scene['audio_file']).exists():
            audio_clip = AudioFileClip(str(scene['audio_file']))
            duration = audio_clip.duration
            audio_clip.close()
        else:
            # フォールバック: duration_secondsを使用
            duration = scene.get('duration_seconds', 5.0)

        # テキストをチャンクに分割
        chunks = split_text_into_chunks(text, max_chars)

        # 各チャンクの表示時間を計算
        chunk_duration = duration / len(chunks) if len(chunks) > 0 else duration

        chunk_start_time = current_time

        for chunk in chunks:
            chunk_start = chunk_start_time
            chunk_end = chunk_start + chunk_duration

            # カラオケ効果: 文字ごとに色を変える
            total_chars = len(chunk)
            if total_chars == 0:
                chunk_start_time = chunk_end
                continue

            char_duration = chunk_duration / total_chars

            # 各文字の状態ごとにイベントを作成
            for char_idx in range(total_chars + 1):
                event_start = chunk_start + (char_idx * char_duration)

                if char_idx == total_chars:
                    # 最後のイベント（全部黄色）は次のチャンク開始まで
                    event_end = chunk_end
                else:
                    event_end = event_start + char_duration

                # 字幕テキスト生成（カラオケ効果）
                white_color = colors[0]
                highlight_color = colors[1]

                if char_idx == 0:
                    # 全部白
                    subtitle_text = f"{{\\c&H{white_color}&}}{chunk}"
                elif char_idx >= total_chars:
                    # 全部ハイライト色
                    subtitle_text = f"{{\\c&H{highlight_color}&}}{chunk}"
                else:
                    # 一部がハイライト色、残りが白
                    highlight_part = chunk[:char_idx]
                    white_part = chunk[char_idx:]
                    subtitle_text = f"{{\\c&H{highlight_color}&}}{highlight_part}{{\\c&H{white_color}&}}{white_part}"

                event_start_str = format_time(event_start)
                event_end_str = format_time(event_end)

                event = f"Dialogue: 0,{event_start_str},{event_end_str},Default,,0,0,0,,{subtitle_text}"
                events.append(event)

            chunk_start_time = chunk_end

        current_time += duration

    # イベントをファイルに書き込み
    ass_content += '\n'.join(events)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(ass_content)


def create_normal_subtitle_file(
    scenes: List[Dict[str, Any]],
    output_file: Path,
    max_chars: int = 20,
    aspect_ratio: str = "9:16"
) -> None:
    """
    ASS形式の通常字幕ファイルを作成（ハイライトなし）

    Args:
        scenes: シーン情報のリスト
        output_file: 出力字幕ファイルパス
        max_chars: 1チャンクの最大文字数
        aspect_ratio: アスペクト比
    """
    # アスペクト比に応じた解像度設定
    if aspect_ratio == "9:16":
        play_res_x = 1080
        play_res_y = 1920
        font_size = 80
        margin_v = 150
    else:  # 16:9
        play_res_x = 1920
        play_res_y = 1080
        font_size = 60
        margin_v = 100

    # ASS形式のヘッダー
    ass_content = f"""[Script Info]
Title: Book Promotion Video
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: {play_res_x}
PlayResY: {play_res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Noto Sans CJK JP,{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,3,5,60,60,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []
    current_time = 0.0

    for scene in scenes:
        text = scene['narration']

        # 音声ファイルから実際の長さを取得
        if 'audio_file' in scene and Path(scene['audio_file']).exists():
            audio_clip = AudioFileClip(str(scene['audio_file']))
            duration = audio_clip.duration
            audio_clip.close()
        else:
            # フォールバック: duration_secondsを使用
            duration = scene.get('duration_seconds', 5.0)

        # テキストをチャンクに分割
        chunks = split_text_into_chunks(text, max_chars)

        # 各チャンクの表示時間を計算
        chunk_duration = duration / len(chunks) if len(chunks) > 0 else duration

        for chunk in chunks:
            chunk_start = current_time
            chunk_end = current_time + chunk_duration

            event_start_str = format_time(chunk_start)
            event_end_str = format_time(chunk_end)

            # 通常字幕（白色固定）
            subtitle_text = chunk

            event = f"Dialogue: 0,{event_start_str},{event_end_str},Default,,0,0,0,,{subtitle_text}"
            events.append(event)

            current_time = chunk_end

    # イベントをファイルに書き込み
    ass_content += '\n'.join(events)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(ass_content)
