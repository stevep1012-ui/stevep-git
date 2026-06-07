# MoneyPrinterTurbo + YouTube Bird 통합 가이드

## 개요

**MoneyPrinterTurbo** (AI 영상 생성) + **YouTube Bird** (음악 혼합 및 발행)을 통합하여, 주제만으로 완전한 유튜브 쇼츠를 자동 생성합니다.

```
주제 입력
    ↓
MoneyPrinterTurbo 생성 (자동)
    ↓
음악 자동 선택
    ↓
FFmpeg 렌더링
    ↓
YouTube 메타데이터 생성
    ↓
최종 패키지 (발행 준비 완료)
```

---

## 설치

### 1단계: MoneyPrinterTurbo 설치

```bash
# MoneyPrinterTurbo 클론
git clone https://github.com/harry0703/MoneyPrinterTurbo.git
cd MoneyPrinterTurbo

# 의존성 설치 (uv 권장)
uv sync --frozen

# 또는 pip 사용
python3.11 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 2단계: 환경 변수 설정

```bash
# ~/.bashrc 또는 ~/.zshrc에 추가 (영구 설정)
export MONEYPRINTER_TURBO_DIR="/path/to/MoneyPrinterTurbo"
export MONEYPRINTER_TURBO_COMMAND="python main.py"

# 또는 명령 실행 전 임시 설정
export MONEYPRINTER_TURBO_DIR="/path/to/MoneyPrinterTurbo"
export MONEYPRINTER_TURBO_COMMAND="python main.py"
python3 -m tools.youtube_healing.turbo_harness --topic "숲속 새소리" --confirm-source-rights ...
```

### 3단계: 음악 카탈로그 설정

```bash
# YouTube Bird 프로젝트 루트에서
cp config/youtube_healing/music_catalog.example.json config/youtube_healing/music_catalog.json

# 원하는 배경음악으로 편집
# (이미 Musopen 공개 도메인 음악으로 구성됨)
```

---

## 사용법

### 기본: 새 영상 생성 및 발행

```bash
python3 -m tools.youtube_healing.turbo_harness \
  --topic "숲속 새소리 힐링" \
  --confirm-source-rights \
  --music-catalog config/youtube_healing/music_catalog.json
```

**출력**:
- ✅ MoneyPrinterTurbo에서 영상 생성
- ✅ YouTube Bird로 자동 임포트
- ✅ 최종 음악 혼합 영상 렌더링
- ✅ YouTube 메타데이터 생성
- ✅ `outputs/youtube-healing/2026-06-05-숲속새소리힐링/` 패키지 생성

### 고급: 기존 Turbo 영상 재사용

```bash
# Turbo 생성 영상 목록 확인
ls /path/to/MoneyPrinterTurbo/storage/tasks/

# 기존 영상 사용 (다시 생성하지 않음)
python3 -m tools.youtube_healing.turbo_harness \
  --topic "Forest Meditation" \
  --use-existing-video "topic_12345_final.mp4" \
  --confirm-source-rights \
  --music-catalog config/youtube_healing/music_catalog.json \
  --bilingual
```

### 옵션 상세

| 옵션 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `--topic` | ✅ | - | Turbo 주제 (예: "새소리 명상") |
| `--use-existing-video` | | 새로 생성 | Turbo 영상 재사용 (생성 스킵) |
| `--music-catalog` | ✅ | - | 음악 카탈로그 JSON 경로 |
| `--confirm-source-rights` | | False | 생성·가져온 영상 자산의 사용 권리를 확인 |
| `--output-root` | | `outputs/youtube-healing` | 최종 패키지 폴더 |
| `--bilingual` | | False | 한국어+영어 메타데이터 |
| `--shooting-date` | | 오늘 | 생성 날짜 (YYYY-MM-DD) |
| `--general-location` | | `generated` | 촬영 위치 라벨 |

---

## 출력 구조

각 실행마다 다음과 같은 완전한 패키지가 생성됩니다:

```
outputs/youtube-healing/2026-06-05-숲속새소리힐링/
├── final_video.mp4              # 🎬 최종 영상 (음악 혼합, 준비 완료)
├── thumbnail.jpg                # 🎨 자동 생성 썸네일
├── youtube_metadata.md          # 📝 제목, 설명, 해시태그
├── media_profile.json           # 📊 영상 정보 (해상도, 길이 등)
├── music_selection.json         # 🎵 선택된 배경음악
├── license_log.json             # ⚖️  음악 라이선스 증거
├── policy_report.json           # 🛡️  정책 검증 결과
├── approval_checklist.md        # ✅ 발행 전 체크리스트
└── asset_manifest.json          # 📋 소스 정보
```

모든 파일이 준비되면 **대시보드**에서:
- 최종 영상 미리보기
- 음악 음량 조정 및 승인
- YouTube 또는 Instagram에 직접 발행

---

## 예제

### 예제 1: 한국어 명상 영상

```bash
python3 -m tools.youtube_healing.turbo_harness \
  --topic "숲속 명상 음악" \
  --confirm-source-rights \
  --music-catalog config/youtube_healing/music_catalog.json \
  --general-location "forest" \
  --bilingual
```

**결과**:
- MoneyPrinterTurbo: 9:16 세로 영상 생성
- YouTube Bird: 배경음악 자동 선택 및 혼합
- 메타데이터: 한국어+영어 제목, 설명, 해시태그

### 예제 2: 일괄 생성

```bash
# 5개 주제로 5개 영상 생성
topics=("산림욕 명상" "새소리 힐링" "강물 소리" "바람 소리" "새들의 아침")

for topic in "${topics[@]}"; do
  python3 -m tools.youtube_healing.turbo_harness \
    --topic "$topic" \
    --confirm-source-rights \
    --music-catalog config/youtube_healing/music_catalog.json
done

# 모든 패키지가 outputs/youtube-healing/에 생성됨
```

### 예제 3: 기존 Turbo 영상으로 배치 처리

```bash
# Turbo에 이미 있는 영상들 확인
ls /path/to/MoneyPrinterTurbo/storage/tasks/

# 각 영상에 다른 음악과 메타데이터 적용
python3 -m tools.youtube_healing.turbo_harness \
  --topic "Healing Music" \
  --use-existing-video "final_video_1.mp4" \
  --confirm-source-rights \
  --music-catalog config/youtube_healing/music_catalog.json \
  --bilingual

python3 -m tools.youtube_healing.turbo_harness \
  --topic "Nature Sounds" \
  --use-existing-video "final_video_2.mp4" \
  --confirm-source-rights \
  --music-catalog config/youtube_healing/music_catalog.json \
  --bilingual
```

---

## 워크플로우

### 단계 1: CLI 실행 (5-10분)

```bash
python3 -m tools.youtube_healing.turbo_harness --topic "주제" --confirm-source-rights ...
```

✅ 자동 완료:
- Turbo 영상 생성 (또는 기존 사용)
- 음악 카탈로그에서 선택
- FFmpeg로 음악 혼합
- YouTube 메타데이터 생성

### 단계 2: 대시보드에서 검수 (2-3분)

```bash
python3 -m tools.youtube_healing.dashboard_server --host 127.0.0.1 --port 8787
```

웹 브라우저에서: `http://127.0.0.1:8787/`

**Step 2 (작업 영상)** → 생성된 패키지 선택:
- 🎬 최종 영상 재생
- 🎵 음악 음량 미리듣기 및 승인
- 📝 메타데이터 확인

**Step 3 (자막과 효과)**:
- 자막 추가 (옵션)
- 인트로/아웃트로 추가 (옵션)

**Step 4 (업로드 준비)**:
- 💾 YouTube 발행 계획 생성
- 📺 YouTube에 업로드 (unlisted/private/public)
- 📸 Instagram Reels 업로드 (옵션)

### 단계 3: YouTube/Instagram 발행 (2-5분)

대시보드에서 직접 발행:
- ✅ YouTube: `https://youtu.be/{video_id}`
- ✅ Instagram Reels: 공유 가능

---

## 트러블슈팅

### ❌ MoneyPrinterTurbo not found

```
❌ MoneyPrinterTurbo not found at /path/to/MoneyPrinterTurbo
```

**해결**:
```bash
# 1. 설치 경로 확인
ls -d /path/to/MoneyPrinterTurbo

# 2. 환경 변수 설정
export MONEYPRINTER_TURBO_DIR="/correct/path"

# 3. 다시 실행
python3 -m tools.youtube_healing.turbo_harness --topic "주제" ...
```

### ❌ MONEYPRINTER_TURBO_COMMAND not set

```
❌ MONEYPRINTER_TURBO_COMMAND not set
```

**해결**:
```bash
export MONEYPRINTER_TURBO_COMMAND="python main.py"
python3 -m tools.youtube_healing.turbo_harness --topic "주제" --confirm-source-rights ...
```

### ❌ Turbo video not found

```
❌ Turbo video not found: topic_123.mp4
```

**해결**:
```bash
# 사용 가능한 Turbo 영상 확인
ls /path/to/MoneyPrinterTurbo/storage/tasks/

# 정확한 파일명 사용 (--use-existing-video)
python3 -m tools.youtube_healing.turbo_harness \
  --topic "주제" \
  --use-existing-video "task-id/final-1.mp4" \
  --confirm-source-rights \
  --music-catalog config/youtube_healing/music_catalog.json
```

---

## 다음 단계

✅ **CLI로 생성 완료**:
- final_video.mp4 (음악 혼합, 발행 준비 완료)
- 모든 메타데이터 생성

➡️ **대시보드에서 마무리**:
- 음악 음량 승인
- 자막 추가 (선택)
- YouTube/Instagram 발행

🚀 **완전 자동화 가능**:
- 매일 다른 주제로 실행
- 5-10분마다 완성된 영상 생성

---

## 비용 고려사항

| 항목 | 비용 | 설명 |
|------|------|------|
| MoneyPrinterTurbo | 무료 | 오픈소스 |
| 배경음악 | 무료 | Musopen 공개 도메인 |
| YouTube 업로드 | 무료 | 채널 필요 |
| Instagram Reels | 무료 | 비즈니스 계정 필요 |
| 클라우드 배포 | 가능 | Docker (선택사항) |

---

## 라이선스 및 규정

- ✅ AI 생성 콘텐츠 (Turbo)
- ✅ 공개 도메인 음악 (Musopen)
- ✅ 정책 검증 자동화
- ✅ 라이선스 증거 자동 기록

발행 전에 항상 **approval_checklist.md** 확인!

---

## 추가 지원

- 📖 [README.md](README.md) - 전체 설명서
- 🔌 [API.md](API.md) - REST API 레퍼런스
- 💾 [GitHub](https://github.com/harry0703/MoneyPrinterTurbo) - MoneyPrinterTurbo
- 🌐 [YouTube Bird](https://github.com/) - 이 프로젝트

---

**생성일**: 2026-06-05
**버전**: 1.0 (turbo_harness.py)
