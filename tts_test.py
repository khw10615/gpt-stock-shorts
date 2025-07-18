import os, requests, dotenv
dotenv.load_dotenv()               # .env 읽기

API_KEY  = os.getenv("ELEVEN_API_KEY")
VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # ElevenLabs 기본 남성 음성(ID 예시)
TEXT     = "테스트입니다. 잘 들리시나요?"

url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"
r = requests.post(
    url,
    headers={"xi-api-key": API_KEY},
    json={"text": TEXT, "voice_settings": {}},
    stream=True, timeout=60
)

print("HTTP 상태:", r.status_code)
print("Content-Type:", r.headers.get("Content-Type"))

if r.status_code == 200 and r.headers.get("Content-Type", "").startswith("audio"):
    with open("voice_test.wav", "wb") as f:
        for chunk in r.iter_content(4096):
            f.write(chunk)
    print("voice_test.wav 저장 완료!")
else:
    print("TTS 실패\n응답 본문:", r.text[:300])