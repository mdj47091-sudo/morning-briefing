"""briefing.txt -> briefing.mp3 (Google Cloud Text-to-Speech)

GitHub Actions에서 실행돼요. 저장소 시크릿 GOOGLE_TTS_API_KEY가 없으면 아무것도 하지 않고 끝나요.
음성은 저장소 변수 TTS_VOICE로 바꿀 수 있어요 (기본: ko-KR-Chirp3-HD-Aoede).
"""
import base64, datetime, json, os, sys, urllib.request, urllib.error

API = "https://texttospeech.googleapis.com/v1/text:synthesize?key="
FALLBACK_VOICES = ["ko-KR-Chirp3-HD-Aoede", "ko-KR-Neural2-A", "ko-KR-Wavenet-A"]
MAX_BYTES = 4500  # 요청 하나당 5000바이트 제한보다 조금 작게


def chunks(text):
    paras = [p.strip() for p in text.split("\n") if p.strip()]
    buf = ""
    for p in paras:
        cand = (buf + "\n" + p).strip()
        if len(cand.encode("utf-8")) > MAX_BYTES and buf:
            yield buf
            buf = p
        else:
            buf = cand
    if buf:
        yield buf


def synth(key, voice, text):
    body = {
        "input": {"text": text},
        "voice": {"languageCode": "ko-KR", "name": voice},
        "audioConfig": {"audioEncoding": "MP3"},
    }
    req = urllib.request.Request(API + key, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return base64.b64decode(json.load(r)["audioContent"])


def main():
    key = os.environ.get("GOOGLE_TTS_API_KEY", "").strip()
    if not key:
        print("GOOGLE_TTS_API_KEY 시크릿이 없어서 음성 생성을 건너뜀")
        return 0
    text = open("briefing.txt", encoding="utf-8").read()
    preferred = os.environ.get("TTS_VOICE", "").strip()
    voices = ([preferred] if preferred else []) + [v for v in FALLBACK_VOICES if v != preferred]
    last_err = None
    for voice in voices:
        try:
            audio = b"".join(synth(key, voice, c) for c in chunks(text))
            break
        except urllib.error.HTTPError as e:
            last_err = f"{voice}: HTTP {e.code} {e.read().decode(errors='replace')[:300]}"
            print("실패 ->", last_err)
    else:
        print("모든 음성 실패:", last_err)
        return 1
    open("briefing.mp3", "wb").write(audio)
    try:
        date = json.load(open("briefing.json", encoding="utf-8")).get("date", "")
    except Exception:
        date = ""
    meta = {
        "date": date,
        "voice": voice,
        "bytes": len(audio),
        "generatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    }
    json.dump(meta, open("audio.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("완료:", meta)
    return 0


if __name__ == "__main__":
    sys.exit(main())
