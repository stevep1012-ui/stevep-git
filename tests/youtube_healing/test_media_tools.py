import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.youtube_healing.media_tools import media_tool_env


class MediaToolsTests(unittest.TestCase):
    def test_media_tool_env_adds_installed_ffmpeg_directory_when_path_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            bin_dir = Path(tmp)
            (bin_dir / "ffmpeg").write_bytes(b"")
            (bin_dir / "ffprobe").write_bytes(b"")

            with (
                patch("tools.youtube_healing.media_tools.shutil.which", return_value=None),
                patch(
                    "tools.youtube_healing.media_tools.COMMON_MEDIA_BIN_DIRS",
                    (bin_dir,),
                ),
                patch.dict(os.environ, {"PATH": "/usr/bin"}, clear=True),
            ):
                env = media_tool_env()

        self.assertEqual(env["PATH"].split(os.pathsep)[0], str(bin_dir))


if __name__ == "__main__":
    unittest.main()
