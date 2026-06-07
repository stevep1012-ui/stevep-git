import tempfile
import unittest
from pathlib import Path

from tools.youtube_healing.tenant_store import build_user_paths, sanitize_user_id


class TenantStoreTests(unittest.TestCase):
    def test_sanitize_user_id_keeps_safe_mobile_user_ids(self):
        self.assertEqual(sanitize_user_id("steve.mobile-01"), "steve.mobile-01")
        self.assertEqual(sanitize_user_id("  user@example.com  "), "user-example.com")

    def test_sanitize_user_id_rejects_empty_or_traversal_values(self):
        with self.assertRaises(ValueError):
            sanitize_user_id("")
        with self.assertRaises(ValueError):
            sanitize_user_id("../other")

    def test_build_user_paths_isolates_inputs_outputs_and_tokens(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_user_paths(Path(tmp), "mobile user")

            self.assertEqual(paths.user_id, "mobile-user")
            self.assertEqual(paths.input_root, Path(tmp) / "mobile-user" / "inputs")
            self.assertEqual(paths.output_root, Path(tmp) / "mobile-user" / "outputs" / "youtube-healing")
            self.assertEqual(paths.config_root, Path(tmp) / "mobile-user" / "config")


if __name__ == "__main__":
    unittest.main()
