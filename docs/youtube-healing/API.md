# YouTube Bird Studio - Web API Reference

The dashboard server provides a REST API for programmatic control of the video workflow.

**Base URL:** `http://127.0.0.1:8787`

**Authentication:** 
- Local mode: No authentication required.
- Cloud mode: Requests must include `?user_id=<user-id>` query parameter or authenticate via `X-Authenticated-User` header.

---

## Health & Status

### GET /api/health

Check server status.

**Response:**
```json
{
  "status": "ok",
  "multi_user": false
}
```

---

## Asset Management

### GET /api/assets

List imported videos, images, and music files for the current user.

**Query Parameters:**
- `user_id` (optional) - User identifier for multi-user mode.

**Response:**
```json
{
  "user_id": "local",
  "videos": [
    {
      "kind": "video",
      "name": "bird-singing.mp4",
      "path": "/path/to/bird-singing.mp4",
      "size_bytes": 1024000
    }
  ],
  "images": [
    {
      "kind": "image",
      "name": "thumbnail.jpg",
      "path": "/path/to/thumbnail.jpg",
      "size_bytes": 50000
    }
  ],
  "music": [
    {
      "kind": "music",
      "name": "background.mp3",
      "path": "/path/to/background.mp3",
      "size_bytes": 500000
    }
  ]
}
```

### POST /api/import/video

Upload a video file.

**Headers:**
- `Content-Type: multipart/form-data`

**Form Data:**
- `file` - Video file (MP4, MOV, M4V)

**Response:**
```json
{
  "kind": "video",
  "name": "bird-singing.mp4",
  "path": "/path/to/bird-singing.mp4",
  "size_bytes": 1024000
}
```

### POST /api/import/image

Upload an image file.

**Headers:**
- `Content-Type: multipart/form-data`

**Form Data:**
- `file` - Image file (JPG, PNG, GIF, WEBP)

**Response:** (Same as video import)

### POST /api/import/music

Upload a music file.

**Headers:**
- `Content-Type: multipart/form-data`

**Form Data:**
- `file` - Audio file (MP3, WAV, M4A, FLAC)

**Response:** (Same as video import)

### POST /api/assets/delete

Delete a specific imported asset.

**JSON Body:**
```json
{
  "kind": "video",
  "name": "bird-singing.mp4"
}
```

**Response:**
```json
{
  "status": "deleted",
  "kind": "video",
  "name": "bird-singing.mp4"
}
```

### POST /api/assets/clear

Delete all imported assets for the current user.

**JSON Body:** `{}`

**Response:**
```json
{
  "status": "cleared",
  "kinds": ["video", "image", "music"]
}
```

---

## Package Management

### GET /api/packages

List all work packages for the current user.

**Query Parameters:**
- `user_id` (optional) - User identifier for multi-user mode.

**Response:**
```json
{
  "user_id": "local",
  "packages": [
    {
      "name": "2026-06-05-bird-video-01",
      "path": "/path/to/2026-06-05-bird-video-01",
      "created_at": "2026-06-05T12:30:45",
      "has_final_video": true,
      "has_subtitled_video": false,
      "has_publish_plan": false,
      "policy_blockers": [],
      "status": "ready_for_review"
    }
  ]
}
```

### POST /api/packages/create

Create a new work package and render the final video with mixed audio.

**JSON Body:**
```json
{
  "video_path": "/path/to/source.mp4",
  "music_path": "/path/to/background.mp3",
  "music_gain_db": -28.0,
  "general_location": "forest",
  "privacy_notes": "no people visible",
  "shooting_date": "2026-06-05",
  "bilingual": false
}
```

**Required Fields:**
- `video_path` - Path to source video
- `music_path` - Path to background music

**Optional Fields:**
- `music_gain_db` - Volume adjustment (default: -28.0 dB)
- `general_location` - Recording location
- `privacy_notes` - Privacy review notes
- `shooting_date` - Recording date (YYYY-MM-DD, default: today)
- `bilingual` - Generate Korean + English metadata (default: false)

**Response:**
```json
{
  "package_name": "2026-06-05-bird-video-01",
  "path": "/path/to/2026-06-05-bird-video-01",
  "status": "success",
  "final_video": "/path/to/2026-06-05-bird-video-01/final_video.mp4",
  "thumbnail": "/path/to/2026-06-05-bird-video-01/thumbnail.jpg",
  "policy_findings": []
}
```

**Error Response:**
```json
{
  "status": "error",
  "message": "Policy blocker: source ownership missing",
  "blocking_findings": [
    {
      "code": "source_ownership_missing",
      "severity": "error",
      "message": "Source video must be owned by user.",
      "blocking": true
    }
  ]
}
```

### GET /api/package-file

Retrieve a file from a package (metadata, report, final video, etc.).

**Query Parameters:**
- `package_name` - Package directory name
- `filename` - File to retrieve (e.g., `final_video.mp4`, `youtube_metadata.md`)
- `user_id` (optional) - User identifier for multi-user mode.

**Response:** Binary file data or text content, with appropriate `Content-Type`.

---

## Music Volume Control

### POST /api/music-volume/preview

Create a preview video showing music volume at a specific dB adjustment.

**JSON Body:**
```json
{
  "package_name": "2026-06-05-bird-video-01",
  "music_gain_db": -24.0
}
```

**Response:**
```json
{
  "preview_video": "/path/to/2026-06-05-bird-video-01/preview_-24db.mp4",
  "message": "Preview created. Listen and approve if satisfied."
}
```

### POST /api/music-volume/approve

Approve the final music volume setting for a package.

**JSON Body:**
```json
{
  "package_name": "2026-06-05-bird-video-01"
}
```

**Response:**
```json
{
  "status": "approved",
  "package_name": "2026-06-05-bird-video-01",
  "approval_file": "/path/to/2026-06-05-bird-video-01/music_volume_approval.json"
}
```

---

## Subtitles & Enhancement

### POST /api/subtitles/render

Add subtitles or visual overlays to a video.

**JSON Body:**
```json
{
  "package_name": "2026-06-05-bird-video-01",
  "method": "intro_outro",
  "intro_path": "/path/to/intro.mp4",
  "outro_path": "/path/to/outro.mp4"
}
```

**Methods:**

**1. Intro/Outro Fade**
```json
{
  "package_name": "2026-06-05-bird-video-01",
  "method": "intro_outro",
  "intro_path": "/path/to/intro.mp4",
  "outro_path": "/path/to/outro.mp4"
}
```

**2. Lower-Third Caption**
```json
{
  "package_name": "2026-06-05-bird-video-01",
  "method": "lower_third",
  "text": "Music: Example Track",
  "start_seconds": 5,
  "duration_seconds": 10
}
```

**3. Timed Captions**
```json
{
  "package_name": "2026-06-05-bird-video-01",
  "method": "timed_captions",
  "captions": [
    {"start": 0, "end": 3, "text": "Title"},
    {"start": 5, "end": 10, "text": "Music Attribution"},
    {"start": 30, "end": 37, "text": "Thank you!"}
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "package_name": "2026-06-05-bird-video-01",
  "subtitled_video": "/path/to/2026-06-05-bird-video-01/subtitled_video.mp4",
  "method": "intro_outro"
}
```

---

## Publishing

### POST /api/music-volume/approve

(See Music Volume Control above - required before publishing)

### POST /api/instagram/upload

Upload the final video to Instagram Reels.

**Prerequisites:**
- Instagram token must be configured (via `/api/instagram/auth-url` → `/api/instagram/callback`)
- `music_volume_approval.json` must exist in the package
- Video must be publicly accessible via HTTPS URL

**JSON Body:**
```json
{
  "package_name": "2026-06-05-bird-video-01",
  "title": "Healing Bird Sounds",
  "description": "Relaxing forest bird sounds with background music."
}
```

**Response:**
```json
{
  "status": "uploaded",
  "package_name": "2026-06-05-bird-video-01",
  "instagram_url": "https://www.instagram.com/reel/...",
  "report_file": "/path/to/2026-06-05-bird-video-01/instagram_upload_report.json"
}
```

### GET /api/instagram/status

Check Instagram authentication status.

**Query Parameters:**
- `user_id` (optional) - User identifier for multi-user mode.

**Response:**
```json
{
  "authenticated": true,
  "username": "your_instagram_username",
  "user_id": "17841402717..."
}
```

**or if not authenticated:**
```json
{
  "authenticated": false
}
```

### GET /api/instagram/auth-url

Get the Instagram OAuth authorization URL.

**Query Parameters:**
- `user_id` (optional) - User identifier for multi-user mode.

**Response:**
```json
{
  "auth_url": "https://www.instagram.com/oauth/authorize?client_id=...",
  "state": "user_id.random_nonce",
  "redirect_uri": "http://127.0.0.1:8787/api/instagram/callback"
}
```

**Next Step:** Direct user to `auth_url`. After authorization, Instagram will redirect to the `redirect_uri` with a code parameter.

### GET /api/instagram/callback

Instagram OAuth callback handler (automatic, no manual call needed).

Handles the OAuth code exchange and token storage.

---

## MoneyPrinter Turbo Integration

### GET /api/turbo/status

Check MoneyPrinter Turbo availability and list available videos.

**Response:**
```json
{
  "installed": true,
  "root": "/path/to/MoneyPrinterTurbo",
  "videos": [
    {
      "name": "topic_1_final.mp4",
      "path": "/path/to/MoneyPrinterTurbo/storage/tasks/task-id/final-1.mp4",
      "size_bytes": 50000000
    }
  ]
}
```

### GET /api/turbo/engine-status

Check if MoneyPrinter Turbo engine is running and ready.

**Response:**
```json
{
  "running": false,
  "command_template": "python main.py",
  "root": "/path/to/MoneyPrinterTurbo"
}
```

### POST /api/turbo/run

Execute MoneyPrinter Turbo to generate a new video from a topic.

**JSON Body:**
```json
{
  "topic": "peaceful forest sounds"
}
```

**Response:**
```json
{
  "status": "running",
  "topic": "peaceful forest sounds",
  "process_id": 12345
}
```

### POST /api/turbo/import

Import a finished MoneyPrinter Turbo video into the local assets.

**JSON Body:**
```json
{
  "turbo_video_name": "topic_1_final.mp4"
}
```

**Response:**
```json
{
  "status": "imported",
  "kind": "video",
  "name": "topic_1_final.mp4",
  "path": "/path/to/data/users/local/inputs/video/topic_1_final.mp4",
  "size_bytes": 50000000
}
```

---

## Error Handling

All endpoints may return error responses in this format:

```json
{
  "status": "error",
  "message": "Detailed error description",
  "code": "error_code"
}
```

**Common Status Codes:**

| Code | Meaning |
|------|---------|
| 200  | OK |
| 400  | Bad request (missing fields, invalid format) |
| 401  | Unauthorized (authentication required) |
| 404  | Not found (package, file, or endpoint) |
| 500  | Server error (unexpected exception) |

---

## Multi-User Mode

In multi-user mode, add the `user_id` query parameter to requests:

```
GET /api/assets?user_id=alice
POST /api/packages/create?user_id=alice
```

Each user's assets and packages are isolated under `data/users/<user_id>/`.

---

## Examples

### Example 1: Create and Upload a Package

```bash
# 1. Import video
curl -X POST http://127.0.0.1:8787/api/import/video \
  -F "file=@/path/to/bird-video.mp4"

# 2. Import music
curl -X POST http://127.0.0.1:8787/api/import/music \
  -F "file=@/path/to/background.mp3"

# 3. Create package
curl -X POST http://127.0.0.1:8787/api/packages/create \
  -H "Content-Type: application/json" \
  -d '{
    "video_path": "data/users/local/inputs/video/bird-video.mp4",
    "music_path": "data/users/local/inputs/music/background.mp3",
    "general_location": "forest",
    "privacy_notes": "no people"
  }'

# 4. Approve music volume
curl -X POST http://127.0.0.1:8787/api/music-volume/approve \
  -H "Content-Type: application/json" \
  -d '{"package_name": "2026-06-05-bird-video-01"}'

# 5. Upload to Instagram
curl -X POST http://127.0.0.1:8787/api/instagram/upload \
  -H "Content-Type: application/json" \
  -d '{
    "package_name": "2026-06-05-bird-video-01",
    "title": "Healing Bird Sounds"
  }'
```

### Example 2: Add Subtitles

```bash
curl -X POST http://127.0.0.1:8787/api/subtitles/render \
  -H "Content-Type: application/json" \
  -d '{
    "package_name": "2026-06-05-bird-video-01",
    "method": "lower_third",
    "text": "Music: Elgar - Salut d'\''Amour",
    "start_seconds": 5,
    "duration_seconds": 15
  }'
```

### Example 3: Multi-User Package Creation

```bash
curl -X POST http://127.0.0.1:8787/api/packages/create?user_id=alice \
  -H "Content-Type: application/json" \
  -d '{
    "video_path": "data/users/alice/inputs/video/video.mp4",
    "music_path": "data/users/alice/inputs/music/music.mp3"
  }'
```
