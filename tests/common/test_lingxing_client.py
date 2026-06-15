from __future__ import annotations

import unittest
from unittest.mock import patch

from src.common.lingxing_client import LingxingClient, LingxingConfig


class LingxingClientTest(unittest.TestCase):
    def test_request_refreshes_token_when_api_reports_expired_access_token(self) -> None:
        client = LingxingClient(
            LingxingConfig(
                base_url="https://example.test",
                app_id="1234567890abcdef",
                app_secret="secret",
                access_token="old-token",
                max_retries=1,
            )
        )
        responses = [
            {"code": "2001003", "msg": " access token is missing or expire.", "data": None},
            {"code": "0", "data": {"access_token": "new-token"}},
            {"code": "0", "data": {"ok": True}},
        ]

        with patch.object(client, "_urlopen_json", side_effect=responses) as urlopen_json:
            data = client.post("/erp/test", {"hello": "world"})

        self.assertEqual(data, {"code": "0", "data": {"ok": True}})
        self.assertEqual(client._access_token, "new-token")
        self.assertEqual(urlopen_json.call_count, 3)


if __name__ == "__main__":
    unittest.main()
