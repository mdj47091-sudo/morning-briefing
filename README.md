# 모닝 매크로 브리핑

매일 아침 AI(Claude)가 거시경제 뉴스를 검색·요약해 `briefing.txt`를 업데이트합니다.
아이폰 단축어 자동화가 알람을 끄면 이 파일을 가져와 시리 음성으로 읽어줍니다.

- 앱(홈 화면에 추가): https://mdj47091-sudo.github.io/morning-briefing/
- 오늘 대본: [briefing.txt](briefing.txt)
- 앱 데이터: [briefing.json](briefing.json), 지난 브리핑: [archive/](archive/)
- Raw 링크(단축어용): https://raw.githubusercontent.com/mdj47091-sudo/morning-briefing/main/briefing.txt

투자 권유가 아닌 학습용 요약입니다.

## AI 성우 음성
`briefing.txt`가 바뀌면 GitHub Actions(`.github/workflows/tts.yml`)가 구글 Cloud Text-to-Speech로 `briefing.mp3`를 만들어요.
- 필요한 설정: 저장소 Settings → Secrets and variables → Actions → 시크릿 `GOOGLE_TTS_API_KEY`
- 음성 변경(선택): 같은 화면 Variables 탭에서 `TTS_VOICE` (예: `ko-KR-Chirp3-HD-Charon`)
