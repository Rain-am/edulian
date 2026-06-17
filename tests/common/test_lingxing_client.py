from __future__ import annotations

from http.client import IncompleteRead
import unittest
from unittest.mock import patch

from src.common.lingxing_client import LingxingClient, LingxingClientError, LingxingConfig


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

    def test_request_retries_incomplete_read(self) -> None:
        client = LingxingClient(
            LingxingConfig(
                base_url="https://example.test",
                app_id="1234567890abcdef",
                app_secret="secret",
                access_token="token",
                max_retries=2,
            )
        )

        with patch.object(
            client,
            "_urlopen_json",
            side_effect=[IncompleteRead(b"{", 10), {"code": "0", "data": {"ok": True}}],
        ) as urlopen_json, patch("src.common.lingxing_client.time.sleep"):
            data = client.post("/erp/test", {"hello": "world"})

        self.assertEqual(data, {"code": "0", "data": {"ok": True}})
        self.assertEqual(urlopen_json.call_count, 2)

    def test_request_does_not_retry_ip_whitelist_errors(self) -> None:
        client = LingxingClient(
            LingxingConfig(
                base_url="https://example.test",
                app_id="1234567890abcdef",
                app_secret="secret",
                access_token="token",
                max_retries=3,
            )
        )

        with patch.object(
            client,
            "_urlopen_json",
            return_value={"code": "3001002", "msg": "ip not permit, please add ip to white list first."},
        ) as urlopen_json, patch("src.common.lingxing_client.time.sleep") as sleep:
            with self.assertRaises(LingxingClientError):
                client.post("/erp/test", {"hello": "world"})

        self.assertEqual(urlopen_json.call_count, 1)
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
