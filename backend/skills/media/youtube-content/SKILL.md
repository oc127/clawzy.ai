---
name: youtube-content
description: Download, transcribe, and analyze YouTube video content
version: 1.0.0
tags: [youtube, video, transcript, download, media]
category: media
platform: all
triggers: [YouTube, 動画, video, トランスクリプト, 字幕, transcript, yt-dlp, 動画要約, download video]
---

## 使用場面
YouTube 動画のトランスクリプト取得、動画の要約生成、コンテンツのダウンロード。

## 字幕・トランスクリプトの取得
```python
from youtube_transcript_api import YouTubeTranscriptApi
# pip install youtube-transcript-api

def get_transcript(video_id: str, lang: str = "ja") -> str:
    """YouTube 動画のトランスクリプトを取得"""
    try:
        # 日本語を優先、なければ英語
        transcript = YouTubeTranscriptApi.get_transcript(
            video_id, 
            languages=[lang, "en"]
        )
        return " ".join(t["text"] for t in transcript)
    except Exception as e:
        return f"字幕取得エラー: {e}"

# URL から video_id を抽出
import re
def extract_video_id(url: str) -> str:
    patterns = [
        r"youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Invalid YouTube URL: {url}")

# 使用例
url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
video_id = extract_video_id(url)
transcript = get_transcript(video_id)
print(f"字幕文字数: {len(transcript)}")
```

## yt-dlp で動画情報取得・ダウンロード
```python
import yt_dlp
# pip install yt-dlp

def get_video_info(url: str) -> dict:
    """動画のメタデータを取得（ダウンロードなし）"""
    ydl_opts = {"quiet": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title"),
            "channel": info.get("channel"),
            "duration": info.get("duration"),  # 秒
            "view_count": info.get("view_count"),
            "description": info.get("description", "")[:500],
            "upload_date": info.get("upload_date"),
        }

def download_audio(url: str, output_path: str = "./audio") -> str:
    """音声のみをダウンロード（文字起こし用）"""
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{output_path}/%(title)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "128",
        }],
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return f"{output_path}/{info['title']}.mp3"
```

## Whisper で文字起こし
```python
import whisper
# pip install openai-whisper

model = whisper.load_model("base")  # tiny, base, small, medium, large

def transcribe_audio(audio_path: str, language: str = "ja") -> str:
    result = model.transcribe(audio_path, language=language)
    return result["text"]
```

## 注意事項
- 著作権で保護されたコンテンツのダウンロードは利用規約に反する場合がある
- 個人利用・研究目的の範囲内で使用する
- `youtube-transcript-api` は字幕が公開されている動画のみ対応

## 検証
動画タイトルと字幕が正しく取得できれば完了。
