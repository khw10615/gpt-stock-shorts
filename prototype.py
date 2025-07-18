import os, datetime, subprocess, textwrap
from dotenv import load_dotenv
load_dotenv()                   # .env 읽기

import openai, yfinance as yf, matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
import ffmpeg                  # ffmpeg‑python 래퍼
import requests

# 1. 주가지수 데이터 ----------------------------------------------------------------
today   = datetime.datetime.now().date()
start   = today - datetime.timedelta(days=7)   # 최근 1주일
ticker  = "^KS11"                              # KOSPI 지수 기호 (Yahoo Finance)
hist    = yf.download(ticker, start=start.isoformat(), end=today.isoformat())
if hist.empty:
    raise ValueError("주가 데이터를 가져오지 못했습니다.")

# 전일 대비
if len(hist) < 2:
    raise ValueError("최근 2거래일 데이터를 찾을 수 없습니다. (휴장일·주말 등)")

prev_close  = hist["Close"].iloc[-2].item()
today_close = hist["Close"].iloc[-1].item()
chg_pct     = round((today_close - prev_close) / prev_close * 100, 2)
direction   = "상승" if chg_pct > 0 else "하락"

# 2. GPT 요약 ------------------------------------------------------------------------
openai.api_key = os.getenv("OPENAI_API_KEY")
prompt = textwrap.dedent(f"""
    오늘 KOSPI 지수는 전일 대비 {chg_pct}% {direction}했습니다.
    주요 원인과 투자자들이 주목할 만한 포인트를 3줄로 요약해 주세요.
    ➊ 한글 30자 이내로 간결 ➋ 숫자·고유명사 정확 ➌ 말미에 📊 이모지 하나.
""").strip()

res = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role":"user","content":prompt}],
    max_tokens=120,
)
summary_txt = res.choices[0].message.content.strip()
print("GPT 요약:\n", summary_txt)

# 3. 차트 PNG ------------------------------------------------------------------------
plt.figure(figsize=(6,3))
plt.plot(hist.index, hist["Close"], linewidth=2)
plt.title("KOSPI 최근 1주일")
plt.tight_layout()
img_path = "chart.png"
plt.savefig(img_path, dpi=300)
plt.close()

# 4. ElevenLabs TTS ------------------------------------------------------------------
tts_api = os.getenv("ELEVEN_API_KEY")
voice_id = "21m00Tcm4TlvDq8ikWAM"     # ElevenLabs 기본 한국어 여성 음성
headers  = {"xi-api-key": tts_api}
payload  = {
    "text": summary_txt,
    "model_id": "eleven_monolingual_v1",
    "voice_settings": {"stability":0.4,"similarity_boost":0.7}
}
audio_path = "voice.wav"
r = requests.post(
    f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream",
    json=payload, headers=headers, stream=True, timeout=60,
)
with open(audio_path, "wb") as f:
    for chunk in r.iter_content(chunk_size=4096):
        f.write(chunk)

# 5. ffmpeg로 영상 합성 ---------------------------------------------------------------
video_path = "output.mp4"
# (a) 차트 이미지 10초 고정
input_stream = ffmpeg.input(img_path, loop=1, t=10, framerate=30)
# (b) 오디오 트랙 삽입
audio_stream = ffmpeg.input(audio_path)
(
    ffmpeg
    .output(input_stream, audio_stream, video_path,
            vcodec="libx264", acodec="aac",
            pix_fmt="yuv420p", shortest=None, loglevel="error")
    .overwrite_output()
    .run()
)
print(f"\n🎬 완료!  {video_path} 생성")