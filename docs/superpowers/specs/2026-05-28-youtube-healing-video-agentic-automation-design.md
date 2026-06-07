# YouTube Healing Video Agentic Automation Design

## Goal
Create an agentic AI workflow that turns owned forest bird-sound videos into upload-ready YouTube healing videos.

The first target is a human-approved workflow: agents prepare the final video package, but the user reviews and approves before upload.

## Seed Asset
The first uploaded sample is an owned bird-sound forest video.

Detected media profile:
- Format: MP4
- Video: HEVC
- Resolution: 1080x1920 vertical
- Duration: about 37 seconds
- Audio: AAC
- Initial fit: YouTube Shorts-style healing clip

## MVP Scope
The first version prepares an upload-ready package from one input video.

Included:
- Import an owned source video.
- Analyze duration, resolution, orientation, codec, and audio presence.
- Select and insert quiet background music automatically.
- Keep original bird sound as the primary audio.
- Apply simple editing: fade in, fade out, light audio balancing, light color normalization when needed, and thumbnail frame extraction.
- Generate YouTube title, description, hashtags, and attribution text.
- Produce copyright, privacy, and quality checks.
- Create an output folder ready for manual approval and upload.

Excluded from the first version:
- Fully automatic publishing without approval.
- Server upload of private media files.
- Paid stock music subscriptions.
- Broad multi-platform publishing.
- Complex AI video generation.
- Monetization optimization beyond basic metadata.

## Recommended Content Format
Start with Shorts-style authentic nature clips.

Rationale:
- The seed asset is already vertical 9:16.
- 37 seconds fits Shorts.
- Owned footage and owned bird sound reduce copyright risk.
- Authentic original nature footage is a stronger channel signal than generic stock footage.

Long-form 10-30 minute videos can be a second phase after the Shorts workflow is stable.

## Agent Roles

### Asset Intake Agent
Registers source files and ownership facts.

Responsibilities:
- Track source file path.
- Record whether the footage and sound are owned by the user.
- Record shooting date, general location, and privacy notes when provided.
- Mark whether people, license plates, private property, or sensitive locations are visible.

Output:
- `asset_manifest.json`

### Media Profiler Agent
Analyzes technical media properties.

Responsibilities:
- Detect duration, resolution, orientation, codec, frame rate, and audio stream.
- Decide whether the video is best for Shorts, standard video, or long-form transformation.
- Flag unsupported codecs or missing audio.

Output:
- `media_profile.json`

### Music Fit & Rights Agent
Selects and mixes legal background music.

Responsibilities:
- Prefer YouTube Audio Library for the MVP.
- Reject random "no copyright music" YouTube channel sources.
- Choose calm, non-vocal, low-beat music.
- Save track name, artist, source URL, license terms, attribution requirement, and access date.
- Mix music at low volume so bird sound remains primary.
- Default starting mix: music around -28 dB relative to the main sound bed, adjusted after preview.

Output:
- `music_selection.json`
- `license_log.json`
- Mixed audio track for the editor

### Auto Editor Agent
Creates the final edited video.

Responsibilities:
- Preserve vertical 1080x1920 output for Shorts.
- Add short fade in and fade out.
- Balance original bird sound and background music.
- Avoid heavy visual effects.
- Extract a thumbnail frame.
- Export final MP4.

Output:
- `final_video.mp4`
- `thumbnail.jpg`
- `edit_report.json`

### Metadata Writer Agent
Creates YouTube-ready text.

Responsibilities:
- Generate Korean title candidates and English title candidates when the user enables bilingual metadata.
- Generate description text.
- Add hashtags.
- Add attribution text when required by the music source.
- Avoid medical or guaranteed benefit claims.

Output:
- `youtube_metadata.md`

### Policy Guard Agent
Checks legal, platform, and brand risk before upload.

Responsibilities:
- Check source ownership status.
- Check music license proof.
- Check visible privacy risk.
- Check location sensitivity.
- Check repeated-content risk.
- Check misleading wellness or health claims.
- Block upload preparation if required legal evidence is missing.

Output:
- `approval_checklist.md`
- `policy_report.json`

### Upload Prep Agent
Collects final files for review.

Responsibilities:
- Create one dated output folder per video.
- Copy final video, thumbnail, metadata, license log, and approval checklist.
- Mark package status as `ready_for_review`.
- Do not upload automatically in the MVP.

Output folder example:
- `outputs/youtube-healing/YYYY-MM-DD-video-title/`

## Ontology
The workflow uses a small ontology so agents share the same vocabulary.

Core entities:
- `SourceAsset`: original video or audio file.
- `MediaProfile`: technical properties of a source asset.
- `Soundscape`: bird sound, wind, rain, stream, forest ambience, or silence.
- `MusicTrack`: background music candidate.
- `LicenseEvidence`: proof that a music track or visual source can be used.
- `EditRecipe`: render settings and transformations.
- `VideoPackage`: upload-ready output bundle.
- `PublishingStatus`: draft, ready_for_review, approved, uploaded, rejected.
- `PolicyFinding`: copyright, privacy, location, repetition, or metadata risk.

Important relationships:
- `SourceAsset` has one `MediaProfile`.
- `SourceAsset` may contain one or more `Soundscape` elements.
- `VideoPackage` derives from one or more `SourceAsset` records.
- `VideoPackage` uses zero or one `MusicTrack` in the MVP.
- `MusicTrack` must have `LicenseEvidence`.
- `PolicyFinding` belongs to a `VideoPackage`.
- `VideoPackage` cannot become `approved` while blocking `PolicyFinding` exists.

## Harness Flow
The harness coordinates agents in a fixed order.

1. Asset Intake Agent registers the source.
2. Media Profiler Agent analyzes the file.
3. Music Fit & Rights Agent selects legal background music and creates the music log.
4. Auto Editor Agent renders preview and final video.
5. Metadata Writer Agent creates YouTube text.
6. Policy Guard Agent checks the full package.
7. Upload Prep Agent creates the review folder.
8. User reviews and approves manually.

The harness should stop when a blocking issue appears.

Blocking examples:
- Missing music license proof.
- Unclear ownership of source footage.
- Visible private person without consent.
- Sensitive location exposure.
- Unsupported source format that cannot be rendered.

## Legal and Platform Considerations
This is not legal advice. It is a practical risk checklist.

Copyright:
- Use owned video and owned bird audio when possible.
- For music, start with YouTube Audio Library only.
- Save license proof for every music track.
- Avoid "free music" claims from ordinary YouTube channels unless license terms are explicit and reusable.

Privacy:
- Check whether people, faces, house numbers, license plates, or private property are visible.
- Blur or reject clips that expose private information.

Location:
- Avoid revealing sensitive exact locations.
- Use general labels such as "forest morning" instead of precise GPS-style location text.

YouTube quality:
- Avoid uploading many near-identical clips.
- Keep metadata specific to the actual video.
- Do not claim guaranteed healing, medical benefits, sleep cure, anxiety cure, or therapy effects.
- Use safer wording such as "relaxing", "calm", "nature ambience", and "bird sound".

## Output Package
Each processed video creates a review package:

- `final_video.mp4`
- `thumbnail.jpg`
- `youtube_metadata.md`
- `asset_manifest.json`
- `media_profile.json`
- `music_selection.json`
- `license_log.json`
- `edit_report.json`
- `policy_report.json`
- `approval_checklist.md`

## Success Criteria
The MVP is successful when:
- A source bird-sound video is converted into a Shorts-ready MP4.
- Background music is inserted at low volume without overpowering bird sound.
- The selected music has saved license evidence.
- A thumbnail is generated.
- YouTube metadata is generated.
- Policy checklist clearly says whether the package is ready for review.
- No automatic upload happens before human approval.

## Verification Plan
Use one owned sample video.

Checks:
- Media profiler detects 1080x1920 vertical video and duration.
- Music selection writes license evidence.
- Final video keeps the source orientation.
- Final audio contains original bird sound and quiet background music.
- Metadata file contains title, description, hashtags, and attribution if required.
- Policy report blocks the package if license proof is absent.
- Output folder contains all required files.

## Later Phases

Phase 2:
- Support long-form 10-30 minute ambient videos.
- Support multiple clips stitched into one video.
- Add light scene classification.
- Add A/B title candidates.

Phase 3:
- Add YouTube API upload after explicit user approval.
- Add schedule calendar.
- Add channel analytics feedback loop.
- Recommend future content based on watch time and retention.
