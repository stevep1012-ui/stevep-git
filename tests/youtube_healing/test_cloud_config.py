import os
import unittest
from unittest.mock import patch

from tools.youtube_healing.cloud_config import CloudConfigError, load_cloud_config


class CloudConfigTests(unittest.TestCase):
    def test_private_mode_does_not_require_public_settings(self):
        with patch.dict(os.environ, {}, clear=True):
            config = load_cloud_config(public_cloud=False)

        self.assertFalse(config.public_cloud)
        self.assertEqual(config.auth_mode, "local")

    def test_public_cloud_requires_real_auth_mode(self):
        with patch.dict(
            os.environ,
            {
                "APP_BASE_URL": "https://example.com",
                "SESSION_SECRET": "x" * 32,
                "AUTH_MODE": "local",
            },
            clear=True,
        ):
            with self.assertRaises(CloudConfigError):
                load_cloud_config(public_cloud=True)

    def test_public_cloud_requires_https_base_url(self):
        with patch.dict(
            os.environ,
            {
                "APP_BASE_URL": "http://example.com",
                "SESSION_SECRET": "x" * 32,
                "AUTH_MODE": "google",
            },
            clear=True,
        ):
            with self.assertRaises(CloudConfigError):
                load_cloud_config(public_cloud=True)

    def test_public_cloud_accepts_minimum_secure_settings(self):
        with patch.dict(
            os.environ,
            {
                "APP_BASE_URL": "https://example.com",
                "SESSION_SECRET": "x" * 32,
                "AUTH_MODE": "google",
            },
            clear=True,
        ):
            config = load_cloud_config(public_cloud=True)

        self.assertTrue(config.public_cloud)
        self.assertEqual(config.app_base_url, "https://example.com")
        self.assertEqual(config.auth_mode, "google")
        self.assertEqual(config.auth_user_header, "X-Authenticated-User")

    def test_public_cloud_allows_custom_auth_user_header(self):
        with patch.dict(
            os.environ,
            {
                "APP_BASE_URL": "https://example.com",
                "SESSION_SECRET": "x" * 32,
                "AUTH_MODE": "google",
                "AUTH_USER_HEADER": "X-Goog-Authenticated-User-Email",
            },
            clear=True,
        ):
            config = load_cloud_config(public_cloud=True)

        self.assertEqual(config.auth_user_header, "X-Goog-Authenticated-User-Email")


if __name__ == "__main__":
    unittest.main()
