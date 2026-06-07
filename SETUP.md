# YouTube Bird Studio - Setup Guide

빠른 시작 가이드입니다. 약 5분 안에 시작할 수 있습니다.

## 요구사항

- **Python**: 3.9 이상
- **FFmpeg**: 오디오/비디오 처리 필수
- **MoneyPrinterTurbo**: 영상 생성 엔진 (선택)

## 1단계: 환경 설정

### macOS
```bash
# FFmpeg 설치
brew install ffmpeg

# Python 의존성 설치 (필요 시)
pip install -r requirements.txt
```

### Linux (Ubuntu/Debian)
```bash
# FFmpeg 설치
sudo apt-get update
sudo apt-get install ffmpeg

# Python 의존성
pip install -r requirements.txt
```

### Windows
1. [FFmpeg 다운로드](https://ffmpeg.org/download.html)
2. PATH에 추가

## 2단계: 음악 카탈로그 준비

### 옵션 A: 샘플 카탈로그 사용 (빠른 시작)
```bash
cp config/youtube_healing/music_catalog.sample.json config/youtube_healing/music_catalog.json
```

### 옵션 B: 직접 작성
1. YouTube Audio Library 또는 Musopen에서 음악 다운로드
2. `config/youtube_healing/music_catalog.json` 작성

**카탈로그 형식:**
```json
[
  {
    "track_id": "unique-id",
    "title": "곡 제목",
    "artist": "아티스트",
    "duration_seconds": 180,
    "local_path": "assets/music/file.mp3",
    "mood_tags": ["calm", "ambient"],
    "has_vocals": false,
    "strong_beat": false,
    "evidence": {
      "source_name": "YouTube Audio Library",
      "source_url": "https://...",
      "license_terms": "라이선스 조건",
      "attribution_required": false,
      "access_date": "2026-06-07"
    }
  }
]
```

## 3단계: 대시보드 실행

```bash
# 웹 대시보드 시작 (기본 포트 8787)
python3 -m tools.youtube_healing.dashboard_server

# 다른 포트 사용
python3 -m tools.youtube_healing.dashboard_server --port 3000

# 멀티유저 모드 (optional)
python3 -m tools.youtube_healing.dashboard_server \
  --multi-user-root data/users \
  --port 8787
```

브라우저에서 열기: http://127.0.0.1:8787/

## 4단계: 첫 영상 생성

### 웹 UI에서:
1. **단계 1**: 영상 및 음악 파일 업로드
2. **단계 2**: 작업 설정 (제목, 음악 선택)
3. **단계 3**: 자막 추가 (선택)
4. **단계 4**: 검토 및 업로드

### 명령줄에서:
```bash
python3 -m tools.youtube_healing.turbo_harness \
  --topic "숲속 새소리" \
  --music-catalog config/youtube_healing/music_catalog.json \
  --output-root outputs/youtube-healing \
  --confirm-source-rights
```

## 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `MONEYPRINTER_TURBO_COMMAND` | Turbo 실행 명령 | (필요 시) |
| `INSTAGRAM_APP_ID` | Instagram API ID | (선택) |
| `INSTAGRAM_APP_SECRET` | Instagram API 비밀 | (선택) |

## 문제 해결

### "FFmpeg not found"
```bash
# FFmpeg 설치 확인
ffmpeg -version
```

### "MoneyPrinterTurbo not found"
- Turbo는 선택사항 (영상 생성 기능만 필요)
- 직접 찍은 영상이나 이미지로도 동작

### "No music tracks found"
- `music_catalog.json` 경로 확인
- `local_path`의 음악 파일이 실제로 존재하는지 확인

## 다음 단계

- [ ] 첫 영상 생성해보기
- [ ] YouTube에 업로드 설정
- [ ] Instagram 연동 (선택)
- [ ] 자막 자동 생성 활용

## 지원

문제가 있으면:
1. 대시보드 우측 하단 Toast 알림 확인
2. 브라우저 개발자 도구 Console 확인
3. 로그 파일 확인 (`logs/` 디렉토리)
