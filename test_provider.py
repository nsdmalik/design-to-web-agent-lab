import json
import os
import unittest
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError, URLError
from workflow import AnthropicProvider, ValidationError


class ProviderTests(unittest.TestCase):
    def call(self, response):
        context = MagicMock()
        context.__enter__.return_value.read.return_value = json.dumps(response).encode()
        with (
            patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-only-placeholder"}),
            patch("urllib.request.urlopen", return_value=context) as send,
        ):
            result = AnthropicProvider("example-model")(
                "plan", {"brief": {"goal": "Test"}}
            )
            request = send.call_args.args[0]
            body = json.loads(request.data)
            self.assertEqual(request.full_url, "https://api.anthropic.com/v1/messages")
            self.assertEqual(body["model"], "example-model")
            self.assertEqual(body["messages"][0]["role"], "user")
            self.assertEqual(request.get_header("Anthropic-version"), "2023-06-01")
            self.assertEqual(send.call_args.kwargs["timeout"], 90)
            return result

    def test_complete_response(self):
        self.assertEqual(
            self.call(
                {"stop_reason": "end_turn", "content": [{"type": "text", "text": "{}"}]}
            ),
            "{}",
        )

    def test_truncated_response(self):
        with self.assertRaises(ValidationError):
            self.call({"stop_reason": "max_tokens", "content": []})

    def test_provider_errors_are_redacted(self):
        for error in [
            HTTPError("https://api.anthropic.com", 429, "private-response", {}, None),
            URLError("private-detail"),
        ]:
            with (
                patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-only-placeholder"}),
                patch("urllib.request.urlopen", side_effect=error) as send,
            ):
                with self.assertRaises(ValidationError) as result:
                    AnthropicProvider("example-model")("plan", {})
                self.assertNotIn("private", str(result.exception))
                self.assertEqual(send.call_count, 1)

    def test_credentials_required(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValidationError):
                AnthropicProvider("example-model")
