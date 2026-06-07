# AGENTS.md

## Project: Youtube_bird

Local agentic AI workflow for turning owned forest bird-sound videos into upload-ready YouTube healing video packages.

## Communication

- 답변은 간결하게 작성한다.
- 사용자가 제공한 개인 정보, 연구 아이디어, 영상 파일명, 로컬 경로는 외부 공개용 문구에 포함하지 않는다.
- 법률 조언이 아닌 실무 리스크 체크로 설명한다.

## Core Rules

1. Keep the workflow local-first.
   - Do not upload private media to a server unless explicitly requested.
   - Do not add automatic YouTube publishing in the MVP.
   - Produce upload-ready folders for human review.

2. Protect copyright and license evidence.
   - MVP music source is YouTube Audio Library only.
   - Save track name, artist, source URL, license terms, attribution requirement, and access date.
   - Reject random "no copyright music" YouTube channels.
   - Reject placeholder or weak license evidence.

3. Protect privacy.
   - Do not expose full local file paths in public YouTube metadata.
   - Check for faces, people, license plates, addresses, phone numbers, and Korean privacy terms.
   - Avoid exact sensitive location disclosure.

4. Keep edits surgical.
   - Prefer small Python modules under `tools/youtube_healing/`.
   - Tests live under `tests/youtube_healing/`.
   - Avoid adding frameworks, servers, or build systems.

## Commands

Run all tests:

```bash
python3 -m unittest discover -s tests -v
```

Run focused tests:

```bash
python3 -m unittest tests.youtube_healing.test_upload_prep -v
```

Check ffmpeg tools:

```bash
ffmpeg -version
ffprobe -version
```

## Main Files

- `tools/youtube_healing/models.py`
- `tools/youtube_healing/media_profiler.py`
- `tools/youtube_healing/music_agent.py`
- `tools/youtube_healing/editor.py`
- `tools/youtube_healing/metadata_agent.py`
- `tools/youtube_healing/policy_guard.py`
- `tools/youtube_healing/upload_prep.py`
- `config/youtube_healing/music_catalog.example.json`
- `docs/superpowers/specs/2026-05-28-youtube-healing-video-agentic-automation-design.md`
- `docs/superpowers/plans/2026-05-28-youtube-healing-video-agentic-automation.md`
