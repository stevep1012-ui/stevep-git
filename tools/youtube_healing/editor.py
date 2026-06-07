from __future__ import annotations

import subprocess
from pathlib import Path

from .media_tools import media_tool_env
from .models import EditReport, MusicSelection


def build_ffmpeg_command(
    source_video: Path,
    music_selection: MusicSelection,
    output_video: Path,
    duration_seconds: float,
    music_gain_db: float | None = None,
) -> list[str]:
    fade_out_start = max(duration_seconds - 1.5, 0.0)
    gain_db = music_selection.target_gain_db if music_gain_db is None else music_gain_db
    music_volume = f"volume={gain_db:g}dB"
    filter_complex = (
        f"[1:a]{music_volume},atrim=0:{duration_seconds},asetpts=PTS-STARTPTS[music];"
        f"[0:a]afade=t=in:st=0:d=0.8,afade=t=out:st={fade_out_start:.2f}:d=1.2[bird];"
        "[bird][music]amix=inputs=2:duration=first:dropout_transition=0[aout]"
    )
    return [
        "ffmpeg",
        "-y",
        "-stream_loop",
        "-1",
        "-i",
        str(source_video),
        "-stream_loop",
        "-1",
        "-i",
        music_selection.track.local_path,
        "-filter_complex",
        filter_complex,
        "-map",
        "0:v:0",
        "-map",
        "[aout]",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-t",
        f"{duration_seconds:g}",
        "-shortest",
        str(output_video),
    ]


def build_thumbnail_command(
    source_video: Path,
    thumbnail_path: Path,
    timestamp_seconds: int,
) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-ss",
        str(timestamp_seconds),
        "-i",
        str(source_video),
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(thumbnail_path),
    ]


def build_image_ffmpeg_command(
    source_image: Path,
    music_selection: MusicSelection,
    output_video: Path,
    duration_seconds: float,
    music_gain_db: float | None = None,
) -> list[str]:
    gain_db = music_selection.target_gain_db if music_gain_db is None else music_gain_db
    music_volume = f"volume={gain_db:g}dB"
    filter_complex = (
        f"[1:a]{music_volume},atrim=0:{duration_seconds},asetpts=PTS-STARTPTS[aout]"
    )
    return [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-t",
        str(duration_seconds),
        "-i",
        str(source_image),
        "-stream_loop",
        "-1",
        "-i",
        music_selection.track.local_path,
        "-filter_complex",
        filter_complex,
        "-map",
        "0:v:0",
        "-map",
        "[aout]",
        "-vf",
        "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-shortest",
        str(output_video),
    ]


def build_sequence_ffmpeg_command(
    media_items: list[dict],
    music_selections: list[MusicSelection],
    output_video: Path,
    duration_seconds: float,
    music_gain_db: float | None = None,
) -> list[str]:
    if not media_items:
        raise ValueError("media_items is required.")
    if not music_selections:
        raise ValueError("music_selections is required.")

    media_segment = duration_seconds / len(media_items)
    music_segment = duration_seconds / len(music_selections)
    command = ["ffmpeg", "-y"]
    media_inputs = []
    input_index = 0
    for item in media_items:
        kind = item["kind"]
        path = Path(item["path"])
        if kind == "image":
            command.extend(["-loop", "1", "-t", f"{media_segment:g}", "-i", str(path)])
            image_index = input_index
            input_index += 1
            command.extend([
                "-f",
                "lavfi",
                "-t",
                f"{media_segment:g}",
                "-i",
                "anullsrc=channel_layout=stereo:sample_rate=44100",
            ])
            media_inputs.append({"kind": kind, "video_index": image_index, "audio_index": input_index})
            input_index += 1
        elif kind == "video":
            command.extend(["-stream_loop", "-1", "-t", f"{media_segment:g}", "-i", str(path)])
            media_inputs.append({"kind": kind, "video_index": input_index, "audio_index": input_index})
            input_index += 1
        else:
            raise ValueError("media item kind must be video or image")

    music_inputs = []
    for selection in music_selections:
        command.extend(["-stream_loop", "-1", "-t", f"{music_segment:g}", "-i", selection.track.local_path])
        music_inputs.append(input_index)
        input_index += 1

    filters = []
    concat_parts = []
    for index, item in enumerate(media_inputs):
        filters.append(
            f"[{item['video_index']}:v:0]trim=0:{media_segment:g},setpts=PTS-STARTPTS,"
            "scale=1080:1920:force_original_aspect_ratio=decrease,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1"
            f"[v{index}]"
        )
        filters.append(f"[{item['audio_index']}:a:0]atrim=0:{media_segment:g},asetpts=PTS-STARTPTS[a{index}]")
        concat_parts.append(f"[v{index}][a{index}]")
    filters.append(f"{''.join(concat_parts)}concat=n={len(media_inputs)}:v=1:a=1[basev][bird]")

    gain_db = music_selections[0].target_gain_db if music_gain_db is None else music_gain_db
    music_volume = f"volume={gain_db:g}dB"
    if len(music_inputs) == 1:
        filters.append(
            f"[{music_inputs[0]}:a:0]{music_volume},atrim=0:{duration_seconds:g},asetpts=PTS-STARTPTS[music]"
        )
    else:
        music_parts = []
        for index, music_input in enumerate(music_inputs):
            filters.append(f"[{music_input}:a:0]atrim=0:{music_segment:g},asetpts=PTS-STARTPTS[m{index}]")
            music_parts.append(f"[m{index}]")
        filters.append(f"{''.join(music_parts)}concat=n={len(music_inputs)}:v=0:a=1[musiccat]")
        filters.append(f"[musiccat]{music_volume},atrim=0:{duration_seconds:g},asetpts=PTS-STARTPTS[music]")
    filters.append("[bird][music]amix=inputs=2:duration=first:dropout_transition=0[aout]")

    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[basev]",
            "-map",
            "[aout]",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-t",
            f"{duration_seconds:g}",
            "-shortest",
            str(output_video),
        ]
    )
    return command


def _select_thumbnail_timestamp(duration_seconds: float) -> int:
    return int(min(5, max(duration_seconds / 2, 0)))


def render_video(
    source_video: Path,
    music_selection: MusicSelection,
    output_video: Path,
    thumbnail_path: Path,
    duration_seconds: float,
    music_gain_db: float | None = None,
) -> EditReport:
    output_video.parent.mkdir(parents=True, exist_ok=True)
    thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_command = build_ffmpeg_command(
        source_video=source_video,
        music_selection=music_selection,
        output_video=output_video,
        duration_seconds=duration_seconds,
        music_gain_db=music_gain_db,
    )
    subprocess.run(ffmpeg_command, check=True, env=media_tool_env())
    thumbnail_command = build_thumbnail_command(
        source_video=output_video,
        thumbnail_path=thumbnail_path,
        timestamp_seconds=_select_thumbnail_timestamp(duration_seconds),
    )
    subprocess.run(thumbnail_command, check=True, env=media_tool_env())
    return EditReport(
        output_path=str(output_video),
        thumbnail_path=str(thumbnail_path),
        ffmpeg_command=ffmpeg_command,
    )


def render_image_video(
    source_image: Path,
    music_selection: MusicSelection,
    output_video: Path,
    thumbnail_path: Path,
    duration_seconds: float,
    music_gain_db: float | None = None,
) -> EditReport:
    output_video.parent.mkdir(parents=True, exist_ok=True)
    thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_command = build_image_ffmpeg_command(
        source_image=source_image,
        music_selection=music_selection,
        output_video=output_video,
        duration_seconds=duration_seconds,
        music_gain_db=music_gain_db,
    )
    subprocess.run(ffmpeg_command, check=True, env=media_tool_env())
    thumbnail_command = build_thumbnail_command(
        source_video=output_video,
        thumbnail_path=thumbnail_path,
        timestamp_seconds=_select_thumbnail_timestamp(duration_seconds),
    )
    subprocess.run(thumbnail_command, check=True, env=media_tool_env())
    return EditReport(
        output_path=str(output_video),
        thumbnail_path=str(thumbnail_path),
        ffmpeg_command=ffmpeg_command,
    )


def render_sequence_video(
    media_items: list[dict],
    music_selections: list[MusicSelection],
    output_video: Path,
    thumbnail_path: Path,
    duration_seconds: float,
    music_gain_db: float | None = None,
) -> EditReport:
    output_video.parent.mkdir(parents=True, exist_ok=True)
    thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_command = build_sequence_ffmpeg_command(
        media_items=media_items,
        music_selections=music_selections,
        output_video=output_video,
        duration_seconds=duration_seconds,
        music_gain_db=music_gain_db,
    )
    subprocess.run(ffmpeg_command, check=True, env=media_tool_env())
    thumbnail_command = build_thumbnail_command(
        source_video=output_video,
        thumbnail_path=thumbnail_path,
        timestamp_seconds=_select_thumbnail_timestamp(duration_seconds),
    )
    subprocess.run(thumbnail_command, check=True, env=media_tool_env())
    return EditReport(
        output_path=str(output_video),
        thumbnail_path=str(thumbnail_path),
        ffmpeg_command=ffmpeg_command,
    )
