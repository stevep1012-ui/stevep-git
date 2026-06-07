import unittest

from tools.youtube_healing.auth_context import AuthError, resolve_user_id


class AuthContextTests(unittest.TestCase):
    def test_local_mode_uses_query_user_id(self):
        user_id = resolve_user_id(
            query="user_id=mobile-demo",
            headers={},
            public_cloud=False,
            auth_user_header="X-Authenticated-User",
        )

        self.assertEqual(user_id, "mobile-demo")

    def test_public_cloud_requires_authenticated_header(self):
        with self.assertRaises(AuthError):
            resolve_user_id(
                query="user_id=spoofed",
                headers={},
                public_cloud=True,
                auth_user_header="X-Authenticated-User",
            )

    def test_public_cloud_uses_header_and_ignores_query_user_id(self):
        user_id = resolve_user_id(
            query="user_id=spoofed",
            headers={"X-Authenticated-User": "person@example.com"},
            public_cloud=True,
            auth_user_header="X-Authenticated-User",
        )

        self.assertEqual(user_id, "person-example.com")

    def test_public_cloud_strips_google_iap_prefix(self):
        user_id = resolve_user_id(
            query="",
            headers={"X-Goog-Authenticated-User-Email": "accounts.google.com:person@example.com"},
            public_cloud=True,
            auth_user_header="X-Goog-Authenticated-User-Email",
        )

        self.assertEqual(user_id, "person-example.com")


if __name__ == "__main__":
    unittest.main()
