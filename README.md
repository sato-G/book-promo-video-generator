# 書籍プロモーション動画ジェネレーター

EPUBファイルから自動的にプロモーション動画を生成するStreamlitアプリケーションです。

## 機能

- EPUBファイルのアップロードと解析
- AI による書籍分析とシナリオ生成（複数パターン）
- シーンごとの画像生成（DALL-E 3）
- ナレーション音声合成（OpenAI TTS）
- カラオケ字幕付き動画生成
- BGM追加機能
- プレビューとダウンロード

## 必要な環境

- Python 3.10+
- ffmpeg（字幕追加に必要）
- OpenAI API キー
- Google Gemini API キー

## セットアップ

### 1. リポジトリをクローン

```bash
git clone https://github.com/yourusername/book-promo-video-generator.git
cd book-promo-video-generator
```

### 2. 仮想環境の作成と有効化

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate  # Windows
```

### 3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 4. ffmpeg のインストール

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get install ffmpeg
```

**Windows:**
[FFmpeg公式サイト](https://ffmpeg.org/download.html)からダウンロード

### 5. 環境変数の設定

`.env.example` をコピーして `.env` ファイルを作成：

```bash
cp .env.example .env
```

`.env` ファイルに以下の情報を記入：

```
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 6. アプリの起動

```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` を開きます。

## Streamlit Cloud へのデプロイ

### 1. GitHub リポジトリにプッシュ

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/book-promo-video-generator.git
git push -u origin main
```

### 2. Streamlit Cloud でデプロイ

1. [Streamlit Cloud](https://streamlit.io/cloud) にアクセス
2. GitHubアカウントでログイン
3. "New app" をクリック
4. リポジトリを選択
5. Main file path: `app.py`
6. Advanced settings で以下の環境変数を設定：
   - `OPENAI_API_KEY`
   - `GOOGLE_API_KEY`
7. "Deploy" をクリック

## 使い方

### Step 1: EPUB アップロード
- EPUBファイルをアップロード
- 書籍情報が自動解析されます

### Step 2: シナリオ選択
- 複数のシナリオパターンから選択
- 対象読者層とビジュアルスタイルを設定

### Step 3: ストーリーボード編集
- 各シーンの内容を確認・編集
- 画像プロンプトの確認

### Step 4: 画像生成
- DALL-E 3 で各シーンの画像を生成
- 生成された画像のプレビューと再生成

### Step 5: 音声設定
- ナレーション音声を生成
- 声の種類と速度を選択
- 字幕タイプ（通常/カラオケ）を選択
- BGMの選択と音量調整

### Step 6: プレビュー＆ダウンロード
- 最終動画を生成
- プレビュー表示
- MP4形式でダウンロード

## 技術スタック

- **フレームワーク:** Streamlit
- **AI API:**
  - Google Gemini 2.5 Flash Lite（テキスト分析）
  - OpenAI DALL-E 3（画像生成）
  - OpenAI TTS（音声合成）
- **動画処理:** moviepy
- **字幕処理:** ffmpeg + ASS
- **EPUB解析:** ebooklib

## ディレクトリ構造

```
book-promo-video-generator/
├── app.py                    # メインエントリポイント
├── requirements.txt          # Python依存パッケージ
├── .env                      # 環境変数（gitignore）
├── .gitignore
├── README.md
├── .streamlit/
│   ├── config.toml          # Streamlit設定
│   └── secrets.toml         # シークレット（gitignore）
├── backend/                 # バックエンドモジュール
│   ├── __init__.py
│   ├── book_analyzer.py     # 書籍分析
│   ├── epub_parser.py       # EPUB解析
│   ├── scenario_generator_v2.py  # シナリオ生成
│   ├── scene_splitter.py    # シーン分割
│   ├── summary_generator.py # 要約生成
│   ├── image_generator_v2.py     # 画像生成
│   ├── tts_engine_v2.py     # 音声合成
│   ├── video_renderer_v2.py # 動画レンダリング
│   ├── subtitle_generator.py     # 字幕生成
│   ├── bgm_manager_v2.py    # BGM管理
│   ├── session_manager.py   # セッション管理
│   └── utils.py             # ユーティリティ
├── pages/                   # Streamlitページ
│   ├── 1_upload_epub.py     # Step 1
│   ├── 2_scenario_editor.py # Step 2
│   ├── 3_storyboard.py      # Step 3
│   ├── 5_audio_settings.py  # Step 4+5
│   └── 6_preview_download.py # Step 6
└── data/                    # データディレクトリ（gitignore）
    ├── uploaded/            # アップロードファイル
    ├── output/              # 生成動画
    │   ├── images/         # 生成画像
    │   ├── audio/          # 生成音声
    │   └── videos/         # 最終動画
    └── BGM/                 # BGMファイル
```

## ライセンス

MIT License

## 作者

Sato

## 注意事項

- OpenAI API と Google Gemini API の利用には料金がかかります
- 生成される動画のファイルサイズは大きくなる場合があります
- Streamlit Cloud の無料プランではリソース制限があります
