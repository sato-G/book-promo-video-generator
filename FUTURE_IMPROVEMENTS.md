# 📋 今後の改善課題

このドキュメントは、書籍プロモーション動画生成システムの今後の改善案をまとめたものです。

## 🎨 1. 画像品質の向上

### 問題点
- 現在DALL-E 3で生成される画像がAI生成っぽく見える
- 実写風やリアルな質感が不足
- スタイルの一貫性が低い場合がある

### 改善案

#### 1.1 プロンプトエンジニアリング強化
```python
# ネガティブプロンプトの追加
NEGATIVE_PROMPTS = [
    "AI-generated", "artificial", "fake", "unrealistic",
    "cartoonish", "low quality", "blurry", "distorted",
    "watermark", "text", "logo", "signature"
]

# スタイル別詳細プロンプト
STYLE_ENHANCERS = {
    "Photorealistic": [
        "professional photography",
        "DSLR camera",
        "natural lighting",
        "8K resolution",
        "highly detailed",
        "realistic textures",
        "shallow depth of field"
    ],
    "Cinematic": [
        "film still",
        "movie scene",
        "dramatic lighting",
        "anamorphic lens",
        "color grading",
        "cinematic composition",
        "35mm film"
    ],
    "Anime": [
        "Studio Ghibli style",
        "hand-drawn animation",
        "cel shaded",
        "vibrant colors",
        "detailed background",
        "expressive characters"
    ]
}

# 構図の指定を強化
COMPOSITION_TEMPLATES = {
    "establishing": "wide shot, establishing scene, environmental details",
    "character": "medium shot, character focus, emotional expression",
    "action": "dynamic angle, motion blur, dramatic perspective",
    "detail": "close-up, macro photography, intricate details"
}
```

#### 1.2 DALL-E 3 HD品質の使用
```python
# backend/image_generator_v2.py
response = client.images.generate(
    model="dall-e-3",
    prompt=full_prompt,
    size=size,
    quality="hd",  # "standard" から "hd" に変更
    n=1
)
```
- **メリット**: より高品質、詳細な画像
- **デメリット**: コストが約2倍（standard: $0.040/画像 → hd: $0.080/画像）

#### 1.3 キャラクター一貫性の確保
```python
# 最初のシーンでキャラクターの詳細な説明を生成
# 以降のシーンで同じ説明を使用
character_description = "a young woman with long brown hair, wearing a blue dress, friendly smile"

# 各シーンのプロンプトに追加
scene_prompt = f"{scene_description}, featuring {character_description}"
```

---

## 🖼️ 2. 代替画像生成サービスの導入

### 2.1 Replicate (Nanabanana / Flux)

**特徴**:
- より自然な画像生成
- アニメスタイルに強い
- コスト効率が良い（$0.003～0.01/画像）
- APIが使いやすい

**実装例**:
```python
import replicate

def generate_image_with_flux(prompt, aspect_ratio="9:16"):
    """
    Flux モデルで画像生成
    """
    output = replicate.run(
        "black-forest-labs/flux-1.1-pro",
        input={
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "output_format": "png",
            "output_quality": 100
        }
    )
    return output
```

**参考リンク**:
- https://replicate.com/black-forest-labs/flux-1.1-pro
- https://replicate.com/pricing

### 2.2 Stability AI (Stable Diffusion XL)

**特徴**:
- オープンソース
- カスタマイズ性が高い
- ネガティブプロンプト対応

**実装例**:
```python
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation

stability_api = client.StabilityInference(
    key=os.environ['STABILITY_KEY'],
    engine="stable-diffusion-xl-1024-v1-0"
)

answers = stability_api.generate(
    prompt=prompt,
    negative_prompt="ugly, blurry, low quality",
    steps=50,
    cfg_scale=8.0,
    width=1024,
    height=1024
)
```

### 2.3 Midjourney (将来的)

現在はDiscord経由のみだが、公式API待ち。
画像品質は最高クラス。

---

## 🎤 3. 音声品質の向上

### 問題点
- OpenAI TTSは高品質だが、より自然な日本語が欲しい場合がある
- 声のバリエーションが限定的

### 改善案

#### 3.1 Google Cloud Text-to-Speech

**特徴**:
- WaveNet/Neural2エンジン
- より自然な日本語イントネーション
- 豊富な日本語音声（30種類以上）
- 感情表現が可能（SSML対応）

**実装例**:
```python
from google.cloud import texttospeech

def synthesize_with_google(text, voice_name="ja-JP-Neural2-B"):
    """
    Google Cloud TTSで音声合成
    """
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="ja-JP",
        name=voice_name,
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.2,  # 速度調整
        pitch=0.0,  # ピッチ調整
        effects_profile_id=["small-bluetooth-speaker-class-device"]
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    return response.audio_content
```

**料金**:
- WaveNet: $16.00 / 1M文字
- Neural2: $16.00 / 1M文字
- Standard: $4.00 / 1M文字

**参考リンク**:
- https://cloud.google.com/text-to-speech

#### 3.2 ElevenLabs

**特徴**:
- 超高品質（人間と区別がつかないレベル）
- 感情表現が豊か
- 声のクローニングも可能

**デメリット**:
- コストが高い（$0.30/1000文字程度）
- 主に英語に特化

#### 3.3 VOICEVOX

**特徴**:
- 完全無料
- 日本語特化
- ローカルで実行可能
- アニメ・キャラクター風の声

**実装例**:
```python
import requests

def synthesize_with_voicevox(text, speaker=1):
    """
    VOICEVOXで音声合成（ローカルサーバー必須）
    """
    # 音声クエリを作成
    query_response = requests.post(
        "http://localhost:50021/audio_query",
        params={"text": text, "speaker": speaker}
    )
    query = query_response.json()

    # 音声合成
    synthesis_response = requests.post(
        "http://localhost:50021/synthesis",
        params={"speaker": speaker},
        json=query
    )

    return synthesis_response.content
```

**参考リンク**:
- https://voicevox.hiroshiba.jp/

---

## 🎬 4. 動画品質の向上

### 4.1 プレビュー機能

**現在の問題**:
- 動画生成に数分かかるため、試行錯誤が難しい

**改善案**:
```python
def generate_preview_video(scenes, duration_limit=10):
    """
    最初の10秒だけの低解像度プレビューを生成
    """
    preview_scenes = []
    total_duration = 0

    for scene in scenes:
        if total_duration + scene['duration'] > duration_limit:
            break
        preview_scenes.append(scene)
        total_duration += scene['duration']

    # 低解像度で高速生成
    return render_video(
        preview_scenes,
        resolution=(640, 360),  # 低解像度
        fps=15,  # 低フレームレート
        preset='ultrafast'  # 高速エンコード
    )
```

### 4.2 解像度オプション

```python
RESOLUTION_PRESETS = {
    "4K": (3840, 2160),
    "1080p": (1920, 1080),
    "720p": (1280, 720),
    "480p": (854, 480)
}
```

### 4.3 SNS最適化プリセット

```python
SNS_PRESETS = {
    "TikTok": {
        "aspect_ratio": "9:16",
        "resolution": (1080, 1920),
        "max_duration": 60,
        "fps": 30
    },
    "Instagram Reels": {
        "aspect_ratio": "9:16",
        "resolution": (1080, 1920),
        "max_duration": 90,
        "fps": 30
    },
    "YouTube Shorts": {
        "aspect_ratio": "9:16",
        "resolution": (1080, 1920),
        "max_duration": 60,
        "fps": 24
    },
    "Twitter": {
        "aspect_ratio": "16:9",
        "resolution": (1280, 720),
        "max_duration": 140,
        "fps": 30
    }
}
```

---

## 🌐 5. 多言語対応

### 5.1 対象言語
- 英語（グローバル展開）
- 中国語（簡体字・繁体字）
- 韓国語
- スペイン語

### 5.2 実装方法

```python
# backend/translator.py
from google.cloud import translate_v2 as translate

def translate_scenario(text, target_language="en"):
    """
    シナリオを翻訳
    """
    translate_client = translate.Client()
    result = translate_client.translate(
        text,
        target_language=target_language
    )
    return result['translatedText']

# 画像プロンプトも翻訳
def translate_image_prompt(prompt, target_language="en"):
    # 英語プロンプトはそのまま使用
    if target_language == "en":
        return prompt
    # その他は英語に翻訳
    return translate_scenario(prompt, "en")
```

---

## 🎵 6. BGM機能の拡張

### 6.1 カスタムBGMアップロード

```python
# pages/5_audio_settings.py
uploaded_bgm = st.file_uploader(
    "カスタムBGMをアップロード",
    type=["mp3", "wav", "m4a"],
    help="動画で使用したいBGMファイルをアップロード"
)

if uploaded_bgm:
    # 一時保存
    bgm_path = save_uploaded_file(uploaded_bgm)
    st.session_state.selected_bgm = bgm_path
```

### 6.2 BGM自動選択

```python
def auto_select_bgm(scenario_tone, scenario_content):
    """
    シナリオの内容に基づいてBGMを自動選択
    """
    # Gemini APIで分析
    analysis = analyze_scenario_mood(scenario_content)

    bgm_mapping = {
        "energetic": "natsuyasuminotanken.mp3",
        "modern": "neonpurple.mp3",
        "calm": "yoiyaminoseaside.mp3",
        "dreamy": "yume.mp3"
    }

    return bgm_mapping.get(analysis['mood'], "yume.mp3")
```

### 6.3 BGMのフェードイン/アウト

```python
def add_bgm_with_fade(video, bgm, fade_duration=2.0):
    """
    BGMにフェードイン/アウトを追加
    """
    bgm_clip = AudioFileClip(bgm)

    # フェードイン
    bgm_clip = bgm_clip.audio_fadein(fade_duration)

    # フェードアウト
    bgm_clip = bgm_clip.audio_fadeout(fade_duration)

    return video.set_audio(
        CompositeAudioClip([video.audio, bgm_clip])
    )
```

---

## 🔧 7. システム改善

### 7.1 バッチ処理

複数のEPUBを一度に処理：

```python
def batch_process_epubs(epub_files, settings):
    """
    複数のEPUBファイルを一括処理
    """
    results = []

    for epub_file in epub_files:
        try:
            video = generate_video_pipeline(epub_file, settings)
            results.append({
                "file": epub_file,
                "status": "success",
                "video": video
            })
        except Exception as e:
            results.append({
                "file": epub_file,
                "status": "error",
                "error": str(e)
            })

    return results
```

### 7.2 進行状況の永続化

```python
# backend/progress_manager.py
def save_progress(project_id, step, data):
    """
    進行状況をデータベースに保存
    """
    progress = {
        "project_id": project_id,
        "step": step,
        "data": data,
        "timestamp": datetime.now()
    }

    # SQLiteやFirebaseに保存
    db.save(progress)

def resume_from_progress(project_id):
    """
    保存された進行状況から再開
    """
    progress = db.load(project_id)
    return progress
```

### 7.3 エラーハンドリングの強化

```python
# backend/error_handler.py
def retry_with_backoff(func, max_retries=3, initial_delay=1):
    """
    指数バックオフでリトライ
    """
    for i in range(max_retries):
        try:
            return func()
        except Exception as e:
            if i == max_retries - 1:
                raise
            delay = initial_delay * (2 ** i)
            print(f"エラー発生、{delay}秒後にリトライ: {e}")
            time.sleep(delay)
```

---

## 📊 8. 分析・レポート機能

### 8.1 動画品質スコア

```python
def analyze_video_quality(video_path):
    """
    生成された動画の品質を分析
    """
    analysis = {
        "resolution": get_resolution(video_path),
        "fps": get_fps(video_path),
        "bitrate": get_bitrate(video_path),
        "duration": get_duration(video_path),
        "audio_quality": analyze_audio(video_path),
        "scene_transitions": count_transitions(video_path)
    }

    # スコア計算
    score = calculate_quality_score(analysis)

    return {
        "score": score,
        "details": analysis,
        "recommendations": get_recommendations(analysis)
    }
```

### 8.2 生成履歴の記録

```python
# 各生成の記録を保存
generation_log = {
    "timestamp": datetime.now(),
    "book_name": book_name,
    "scenario_type": scenario['pattern_name'],
    "visual_style": visual_style,
    "num_scenes": num_scenes,
    "generation_time": elapsed_time,
    "api_costs": {
        "gemini": gemini_cost,
        "dalle": dalle_cost,
        "tts": tts_cost
    },
    "video_url": video_path
}
```

---

## 🎯 9. 優先順位

### 高優先度（すぐに実装すべき）
1. ✅ **プロンプトエンジニアリング強化** - コストゼロで品質向上
2. ⭐ **Google Cloud TTS導入** - より自然な日本語
3. ⭐ **プレビュー機能** - UX向上

### 中優先度（検討価値あり）
4. 🔵 **Replicate (Flux) 導入** - コスト削減＋品質向上
5. 🔵 **カスタムBGMアップロード** - ユーザー要望に応える
6. 🔵 **SNS最適化プリセット** - 実用性向上

### 低優先度（将来的に）
7. 🟡 多言語対応
8. 🟡 バッチ処理
9. 🟡 分析・レポート機能

---

## 💰 コスト試算

### 現在の構成（1動画あたり）
- DALL-E 3 standard (5シーン): $0.20
- OpenAI TTS (500文字×5): $0.075
- Gemini Flash (3回): $0.00001
- **合計**: 約 $0.28 / 動画

### 改善後の構成例
- Flux (5シーン): $0.05
- Google Cloud TTS Neural2 (500文字×5): $0.04
- Gemini Flash (3回): $0.00001
- **合計**: 約 $0.09 / 動画

**コスト削減**: 約70%削減可能

---

## 📚 参考リンク

### 画像生成
- [DALL-E 3 Documentation](https://platform.openai.com/docs/guides/images)
- [Replicate Flux Models](https://replicate.com/collections/flux)
- [Stability AI](https://platform.stability.ai/)

### 音声合成
- [Google Cloud TTS](https://cloud.google.com/text-to-speech)
- [ElevenLabs](https://elevenlabs.io/)
- [VOICEVOX](https://voicevox.hiroshiba.jp/)

### 動画処理
- [MoviePy Documentation](https://zulko.github.io/moviepy/)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)

---

## 📝 実装時の注意点

1. **API制限**
   - 各サービスのレート制限に注意
   - リトライロジックを実装

2. **コスト管理**
   - 使用量の監視
   - 月間予算の設定

3. **エラーハンドリング**
   - タイムアウト処理
   - 部分的な失敗からの復旧

4. **テスト**
   - 各改善について十分なテスト
   - ���ーザーフィードバックの収集

---

**最終更新**: 2025-10-27
**バージョン**: v2.0
