"""briefing.txt -> briefing.mp3

GitHub Actions에서 실행돼요.
- 시크릿 GOOGLE_TTS_API_KEY가 있으면 구글 Cloud Text-to-Speech (변수 TTS_VOICE, 기본 ko-KR-Chirp3-HD-Aoede)
- 없으면 마이크로소프트 엣지 음성(edge-tts, 비공식) 사용 (변수 EDGE_VOICE, 기본 ko-KR-HyunsuMultilingualNeural)
- tts/samples.txt에 음성 이름을 한 줄씩 적어두면 samples/<음성>.mp3 비교용 샘플도 만들어요.
"""
import base64, datetime, json, os, subprocess, sys, urllib.request, urllib.error

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


def edge(voice, src, out, rate):
    subprocess.run(["edge-tts", "--voice", voice, f"--rate={rate}", "--file", src, "--write-media", out], check=True, timeout=300)
    return open(out, "rb").read()


def google(key, text):
    preferred = os.environ.get("TTS_VOICE", "").strip()
    voices = ([preferred] if preferred else []) + [v for v in FALLBACK_VOICES if v != preferred]
    last_err = None
    for voice in voices:
        try:
            return voice, b"".join(synth(key, voice, c) for c in chunks(text))
        except urllib.error.HTTPError as e:
            last_err = f"{voice}: HTTP {e.code} {e.read().decode(errors='replace')[:300]}"
            print("실패 ->", last_err)
    raise RuntimeError("구글 음성 모두 실패: " + str(last_err))


def main():
    key = os.environ.get("GOOGLE_TTS_API_KEY", "").strip()
    rate = os.environ.get("EDGE_RATE", "").strip() or "+5%"
    text = open("briefing.txt", encoding="utf-8").read()
    audio = None
    if key:
        try:
            voice, audio = google(key, text)
            engine = "google"
        except Exception as e:
            print(e, "-> 엣지 음성으로 대체")
    if audio is None:
        voice = os.environ.get("EDGE_VOICE", "").strip() or "ko-KR-HyunsuMultilingualNeural"
        audio = edge(voice, "briefing.txt", "briefing.mp3", rate)
        engine = "edge"
    samples = []
    if os.path.exists("tts/samples.txt"):
        os.makedirs("samples", exist_ok=True)
        for v in [l.strip() for l in open("tts/samples.txt", encoding="utf-8") if l.strip() and not l.startswith("#")]:
            try:
                edge(v, "briefing.txt", f"samples/{v}.mp3", rate)
                samples.append({"voice": v, "file": f"samples/{v}.mp3"})
            except Exception as e:
                print("샘플 실패", v, e)
    open("briefing.mp3", "wb").write(audio)
    try:
        date = json.load(open("briefing.json", encoding="utf-8")).get("date", "")
    except Exception:
        date = ""
    meta = {
        "date": date,
        "engine": engine,
        "voice": voice,
        "bytes": len(audio),
        "samples": samples,
        "generatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    }
    json.dump(meta, open("audio.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("완료:", meta)
    return 0


if __name__ == "__main__":
    sys.exit(main())
