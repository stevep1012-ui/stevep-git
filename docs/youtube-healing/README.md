# YouTube Healing Video Automation

This local workflow prepares upload-ready YouTube healing video packages from owned bird-sound videos with automated music mixing, subtitle insertion, and publishing to YouTube or Instagram.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Web Dashboard (Recommended)](#web-dashboard)
3. [Command-Line Interface](#command-line-interface)
4. [Publishing Pipeline](#publishing-pipeline)
5. [Advanced Features](#advanced-features)
6. [MoneyPrinter Turbo Integration](#moneyprinter-turbo-integration)
7. [Cloud Deployment](#cloud-deployment)

---

## Quick Start

**Fastest way to get started (5 minutes):**

1. Start the local dashboard:
   ```bash
   python3 -m tools.youtube_healing.dashboard_server --host 127.0.0.1 --port 8787
   ```

2. Open http://localhost:8787 in a browser.

3. Upload your own bird-sound video and background music.

4. Select workflow mode ("일반 자동 작업" for direct upload-ready package).

5. Create a work package and preview the final video.

6. Approve the music volume and create a publish plan.

7. Upload to YouTube or Instagram directly from the dashboard.

---

## Web Dashboard

The dashboard provides a guided workflow with real-time preview and approval gates.

### Start Dashboard

macOS:
```bash
python3 -m tools.youtube_healing.dashboard_server --host 127.0.0.1 --port 8787
```

Windows:
```bat
python -m tools.youtube_healing.dashboard_server --host 127.0.0.1 --port 8787
```

Then open: **http://127.0.0.1:8787/**

### Dashboard Workflow Steps

1. **영상과 음악** (Step 1: Files)
   - Import your own video file (MP4, MOV, M4V).
   - Import background music (MP3, WAV, M4A).
   - Select workflow mode:
     - 일반 자동 작업 (direct video → final output)
     - MoneyPrinter Turbo (compose with AI-generated content)

2. **작업 영상** (Step 2: Packages)
   - Create a work package with selected media.
   - Media are combined into a sequence.
   - FFmpeg renders the final mixed video.

3. **자막과 효과** (Step 3: Subtitles)
   - Add intro/outro videos with fade transitions.
   - Add lower-third captions or timed text overlays.
   - Re-encode for compatibility.
   - Output saved as `subtitled_video.mp4`.

4. **업로드 준비** (Step 4: Review & Upload)
   - Watch final video and approve music volume.
   - Create metadata (title, description, hashtags).
   - Create a publish plan.
   - Upload to YouTube (unlisted, private, public) or Instagram Reels.

### Multi-User Local Network Mode

Run the dashboard for multiple users on the same Wi-Fi:

macOS:
```bash
bash scripts/run_multiuser_dashboard.sh
```

Windows:
```bat
scripts\run_multiuser_dashboard.bat
```

Each user enters a **사용자 ID** (user ID) in the dashboard. Their uploads and packages are stored separately under `data/users/<user_id>/`.

**Note:** This is a local-network prototype. Before opening to the internet, add real login, HTTPS, per-user YouTube OAuth, and content moderation.

---

## Command-Line Interface

For scripted or batch workflows, use the CLI harness directly.

### Inputs

- Owned source video, preferably vertical 1080x1920 for Shorts.
- Local music file from YouTube Audio Library or Musopen public domain music.
- `music_catalog.json` with license evidence for the selected music.

## Create Music Catalog

Copy `config/youtube_healing/music_catalog.example.json` to a private working file:

```bash
cp config/youtube_healing/music_catalog.example.json config/youtube_healing/music_catalog.json
```

Edit `config/youtube_healing/music_catalog.json` with the actual track title, artist, downloaded file path, license terms, and access date shown by the source page.

The MVP accepts:

- YouTube Audio Library music with a valid YouTube Studio audio-library URL.
- Musopen public domain music with a valid `musopen.org/music/...` source URL.

Placeholder license text, weak terms such as "free" or "no copyright music", unsupported music sources, and invalid source URLs block rendering and create an approval checklist for manual correction.

### CLI Run

```bash
python3 -m tools.youtube_healing.harness \
  --source "/path/to/owned-bird-video.mp4" \
  --music-catalog config/youtube_healing/music_catalog.json \
  --output-root outputs/youtube-healing \
  --general-location "forest" \
  --privacy-notes "no people visible"
```

Optional flags:

- `--shooting-date YYYY-MM-DD` (default: today)
- `--not-owned` (mark source as not owned by user)
- `--bilingual` (generate Korean + English metadata)

### CLI Output

The workflow creates a dated review folder under `outputs/youtube-healing` by default.

If policy blockers exist, the workflow writes:

- `asset_manifest.json`
- `media_profile.json`
- `policy_report.json`
- `approval_checklist.md`

If music selection succeeds but another policy blocker exists, the workflow also writes:

- `music_selection.json`
- `license_log.json`

If no policy blockers exist, the workflow also writes:

- `final_video.mp4`
- `thumbnail.jpg`
- `edit_report.json`
- `youtube_metadata.md`

---

## Publishing Pipeline

Before API upload, review the background music volume in the dashboard final review step:

1. Select the package.
2. Adjust `배경음악 볼륨 프리뷰`.
3. Click `프리뷰 만들기` and listen to the preview.
4. Click `이 볼륨으로 승인`.

Approval writes `music_volume_approval.json`. YouTube and Instagram upload commands block if this approval file is missing.

Create a publishing plan after approval. YouTube defaults to `unlisted`.

```bash
python3 -m tools.youtube_healing.publish_agent \
  --package-dir outputs/youtube-healing/YOUR_PACKAGE_FOLDER \
  --privacy-status unlisted
```

If `--title` is omitted, the tool asks for the YouTube title before writing `publish_plan.json`.

YouTube upload requires OAuth setup values:

- `YOUTUBE_CLIENT_SECRET_FILE`
- `YOUTUBE_TOKEN_FILE`

Instagram Reels publishing requires a professional Instagram account, Graph API access, and:

- `INSTAGRAM_APP_ID`
- `INSTAGRAM_APP_SECRET`
- `INSTAGRAM_REDIRECT_URI`
- `INSTAGRAM_ACCESS_TOKEN`
- `INSTAGRAM_USER_ID`
- `INSTAGRAM_VIDEO_URL`

Instagram cannot publish this local file directly from disk; `INSTAGRAM_VIDEO_URL` must be a public HTTPS video URL that Meta can fetch.

For dashboard login, set the Meta app values first:

```bash
export INSTAGRAM_APP_ID="your-meta-app-id"
export INSTAGRAM_APP_SECRET="your-meta-app-secret"
export INSTAGRAM_REDIRECT_URI="http://127.0.0.1:8787/api/instagram/callback"
```

Then open the dashboard final review step and click `Instagram 로그인`. The token is saved per local user under that user's private config folder. Do not share `instagram_token.json`.

After writing `publish_plan.json`, upload to Instagram Reels:

```bash
INSTAGRAM_ACCESS_TOKEN="your-token" \
INSTAGRAM_USER_ID="your-ig-user-id" \
INSTAGRAM_VIDEO_URL="https://your-public-host/final_video.mp4" \
python3 -m tools.youtube_healing.publish_agent \
  --package-dir outputs/youtube-healing/YOUR_PACKAGE_FOLDER \
  --title "힐링되는 새소리" \
  --upload-instagram
```

The dashboard also shows `Instagram 자동 업로드` in the final review step. It uses the same environment variables and writes `instagram_upload_report.json` after publishing.

## Local Dashboard

Run the cross-platform local dashboard:

macOS:

```bash
python3 -m tools.youtube_healing.dashboard_server --host 127.0.0.1 --port 8787
```

Windows:

```bat
python -m tools.youtube_healing.dashboard_server --host 127.0.0.1 --port 8787
```

Then open:

```text
http://127.0.0.1:8787/
```

For phone access on the same Wi-Fi, run with `--host 0.0.0.0` and open the computer's LAN IP address from iPhone or Android. Keep this local network only unless you intentionally secure it for external access.

Multi-user LAN mode:

macOS:

```bash
bash scripts/run_multiuser_dashboard.sh
```

Windows:

```bat
scripts\run_multiuser_dashboard.bat
```

In multi-user mode, each mobile user enters a `사용자 ID` in the dashboard. Their uploads and generated packages are stored separately under `data/users/<user_id>/`.

This is a local-network prototype, not public authentication. Before opening it to the internet, add real login, HTTPS, per-user YouTube OAuth, storage quotas, and content moderation.

## MoneyPrinter Turbo Integration

The dashboard can run a configured local MoneyPrinter Turbo command, then import finished videos into the local video list.

Set the MoneyPrinter Turbo root, command, and output folder before starting the dashboard. The command is split without a shell and `{topic}` is replaced by the dashboard topic input.

macOS:

```bash
export MONEYPRINTER_TURBO_DIR="/path/to/MoneyPrinterTurbo"
export MONEYPRINTER_TURBO_OUTPUT_DIR="/path/to/MoneyPrinterTurbo/storage/tasks"
export MONEYPRINTER_TURBO_COMMAND="python main.py"
python3 -m tools.youtube_healing.dashboard_server --host 127.0.0.1 --port 8787 --multi-user-root data/users
```

Windows:

```bat
set MONEYPRINTER_TURBO_DIR=C:\path\to\MoneyPrinterTurbo
set MONEYPRINTER_TURBO_OUTPUT_DIR=C:\path\to\MoneyPrinterTurbo\storage\tasks
set MONEYPRINTER_TURBO_COMMAND=python main.py
python -m tools.youtube_healing.dashboard_server --host 127.0.0.1 --port 8787 --multi-user-root data\users
```

Then use `Turbo 결과 연동 > Turbo 엔진 실행`, select a generated result, and click `Turbo 결과 가져오기` in the first dashboard step.

Only finished `.mp4`, `.mov`, and `.m4v` files are imported. Review licensing for any stock video, voice, music, image, or script generated by MoneyPrinter Turbo before uploading.

## Cloud Web App Mode

Cloud deployment files:

- `Dockerfile`
- `.env.cloud.example`
- `docs/youtube-healing/cloud-webapp-architecture.md`

Public cloud mode refuses to start unless:

- `APP_BASE_URL` starts with `https://`
- `AUTH_MODE` is not `local`
- `SESSION_SECRET` is at least 32 characters

In public cloud mode, the app ignores browser-supplied `user_id` and uses a trusted authenticated user header. Put it behind Google IAP, Cloudflare Access, or an equivalent auth proxy.

Example:

```bash
APP_BASE_URL=https://your-domain.example \
AUTH_MODE=google \
SESSION_SECRET=replace-with-at-least-32-random-characters \
AUTH_USER_HEADER=X-Goog-Authenticated-User-Email \
python3 -m tools.youtube_healing.dashboard_server \
  --host 0.0.0.0 \
  --port 8787 \
  --multi-user-root data/users \
  --public-cloud
```

Header examples:

- Google IAP: `X-Goog-Authenticated-User-Email`
- Cloudflare Access: `Cf-Access-Authenticated-User-Email`
- Custom auth proxy: `X-Authenticated-User`

## Subtitles After Music Mix

The dashboard can add burned-in subtitles after `final_video.mp4` is created.

Subtitle methods:

- `시작/끝 문구`: show the same text at the beginning and end.
- `하단 고정`: show one lower-third caption during a selected time range.
- `시간대별 문구`: add multiple timed captions. Each line uses `start,end,text`.

The result is saved as `subtitled_video.mp4` in the selected package folder.

## Approval Rules

Upload only after checking:

- The final video plays correctly.
- Bird sound remains primary.
- Music license evidence is saved.
- No private person, license plate, house number, or sensitive location is visible.
- Metadata does not claim guaranteed healing, medical, sleep, anxiety, or therapy effects.

---

## MoneyPrinter Turbo Integration

Generate healing videos using **MoneyPrinterTurbo**, then mix music and prepare metadata for human review.

### Setup

1. **Install MoneyPrinterTurbo** (if not already installed):
   ```bash
   git clone https://github.com/harry0703/MoneyPrinterTurbo.git
   cd MoneyPrinterTurbo
   uv sync --frozen  # or: python3.11 -m venv .venv && pip install -r requirements.txt
   ```

2. **Configure YouTube Bird** with Turbo paths:
   ```bash
   # Set environment variables
   export MONEYPRINTER_TURBO_DIR="/path/to/MoneyPrinterTurbo"
   export MONEYPRINTER_TURBO_OUTPUT_DIR="/path/to/MoneyPrinterTurbo/storage/tasks"
   export MONEYPRINTER_TURBO_COMMAND="python main.py"
   ```

3. **Configure music catalog**:
   ```bash
   cp config/youtube_healing/music_catalog.example.json config/youtube_healing/music_catalog.json
   # Edit with your preferred background music
   ```

### CLI: Generate an Upload-Ready Review Package

**Generate a new Turbo video and publish**:

```bash
python3 -m tools.youtube_healing.turbo_harness \
  --topic "숲속 새소리 힐링 명상" \
  --confirm-source-rights \
  --music-catalog config/youtube_healing/music_catalog.json \
  --output-root outputs/youtube-healing \
  --bilingual
```

**Reuse existing Turbo video**:

```bash
python3 -m tools.youtube_healing.turbo_harness \
  --topic "Forest Bird Sounds" \
  --use-existing-video "topic_1_final.mp4" \
  --confirm-source-rights \
  --music-catalog config/youtube_healing/music_catalog.json \
  --output-root outputs/youtube-healing
```

### Command Options

| Option | Default | Description |
|--------|---------|-------------|
| `--topic` | *(required)* | Turbo video topic |
| `--use-existing-video` | *(generate new)* | Use existing Turbo video instead of generating |
| `--music-catalog` | *(required)* | Path to music catalog JSON |
| `--confirm-source-rights` | False | Confirm rights to use generated or imported source assets |
| `--output-root` | `outputs/youtube-healing` | Output package folder |
| `--shooting-date` | Today | Creation date (YYYY-MM-DD) |
| `--general-location` | `generated` | Location label |
| `--privacy-notes` | *(auto)* | Privacy review notes |
| `--bilingual` | False | Generate Korean + English metadata |

### Output Package

The CLI creates a complete package ready for publishing:

```
outputs/youtube-healing/2026-06-05-숲속새소리/
├── final_video.mp4           # Ready to publish (mixed with music)
├── thumbnail.jpg             # Auto-generated
├── youtube_metadata.md       # Title, description, hashtags
├── media_profile.json        # Video specs
├── music_selection.json      # Selected background music
├── license_log.json          # Music license evidence
├── policy_report.json        # Policy validation results
└── approval_checklist.md     # Manual review checklist
```

### Workflow

1. **Generate**: MoneyPrinterTurbo creates AI video from topic
2. **Import**: Video automatically copied to YouTube Bird
3. **Analyze**: Media profiling and policy checks
4. **Music**: Select from your music catalog
5. **Render**: FFmpeg mixes video + music
6. **Metadata**: Generate YouTube/Instagram info
7. **Package**: Complete folder ready for publishing

### Dashboard Integration

After running CLI, open dashboard to:
- Preview final video and audio mix
- Adjust music volume
- Add subtitles or intro/outro videos
- Publish to YouTube (unlisted/private/public)
- Publish to Instagram Reels

```bash
# Start dashboard (in same or another terminal)
python3 -m tools.youtube_healing.dashboard_server --host 127.0.0.1 --port 8787
```

Navigate to your generated package in **Step 2 (작업 영상)** to complete publishing.

### Example: Batch Generate

```bash
# Generate 5 healing videos
for topic in "숲 명상" "새소리" "강물 소리" "바람 소리" "새들의 아침"; do
  python3 -m tools.youtube_healing.turbo_harness \
    --topic "$topic 힐링" \
    --confirm-source-rights \
    --music-catalog config/youtube_healing/music_catalog.json \
    --bilingual
done
```

---

## Cloud Deployment
