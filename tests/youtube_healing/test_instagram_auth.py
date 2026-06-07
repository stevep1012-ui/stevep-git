import json
import tempfile
import unittest
from pathlib import Path

from tools.youtube_healing.instagram_auth import (
    build_instagram_login_url,
    exchange_code_for_instagram_token,
    instagram_token_status,
    save_instagram_token,
)


class InstagramAuthTests(unittest.TestCase):
    def test_build_instagram_login_url_contains_user_state_and_scopes(self):
        url, state = build_instagram_login_url(
            config_root=Path("/tmp/user/config"),
            user_id="mobile-user",
            app_id="app123",
            redirect_uri="http://127.0.0.1:8787/api/instagram/callback",
            nonce="nonce123",
        )

        self.assertIn("client_id=app123", url)
        self.assertIn("instagram_basic", url)
        self.assertIn("instagram_content_publish", url)
        self.assertIn("state=mobile-user.nonce123", url)
        self.assertEqual(state, "mobile-user.nonce123")

    def test_exchange_code_saves_user_token_and_instagram_user_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_root = Path(tmp)
            calls = []

            def fake_get(url):
                calls.append(url)
                if "oauth/access_token" in url:
                    return {"access_token": "short-token"}
                return {
                    "data": [
                        {
                            "instagram_business_account": {
                                "id": "1789",
                                "username": "forest.birds",
                            }
                        }
                    ]
                }

            token = exchange_code_for_instagram_token(
                config_root=config_root,
                code="code123",
                app_id="app123",
                app_secret="secret456",
                redirect_uri="http://127.0.0.1:8787/api/instagram/callback",
                http_get=fake_get,
            )

            self.assertEqual(token["access_token"], "short-token")
            self.assertEqual(token["instagram_user_id"], "1789")
            self.assertTrue((config_root / "instagram_token.json").exists())
            self.assertTrue(any("me/accounts" in call for call in calls))

    def test_instagram_token_status_reports_connected_without_secret_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_root = Path(tmp)
            save_instagram_token(
                config_root,
                {
                    "access_token": "secret-token",
                    "instagram_user_id": "1789",
                    "instagram_username": "forest.birds",
                },
            )

            status = instagram_token_status(config_root)

            self.assertTrue(status["connected"])
            self.assertEqual(status["instagram_user_id"], "1789")
            self.assertEqual(status["instagram_username"], "forest.birds")
            self.assertNotIn("secret-token", json.dumps(status))


if __name__ == "__main__":
    unittest.main()
