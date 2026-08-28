import json
from evolution.logger import redact_data, _redact_string


class TestRedaction:
    def test_api_key_value(self):
        assert _redact_string("sk-abc123xyz456") == "***"

    def test_github_pat(self):
        assert _redact_string("github_pat_11B5ODYO1234") == "***"

    def test_bearer_token(self):
        assert _redact_string("Bearer eyJhbGciOiJIUzI1NiJ9") == "***"

    def test_uuid_not_redacted(self):
        uuid_str = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        assert _redact_string(uuid_str) == uuid_str

    def test_dict_redaction(self):
        data = {"api_key": "sk-secret123", "name": "test", "content": "hello"}
        result = redact_data(data)
        assert result["api_key"] == "***"
        assert result["name"] == "test"

    def test_nested_redaction(self):
        data = {"config": {"token": "ghp_abc123", "port": 8080}}
        result = redact_data(data)
        assert result["config"]["token"] == "***"
        assert result["config"]["port"] == 8080

    def test_list_redaction(self):
        data = [{"key": "sk-test"}, {"key": "normal"}]
        result = redact_data(data)
        assert result[0]["key"] == "***"
        assert result[1]["key"] == "normal"

    def test_url_with_token(self):
        assert _redact_string("https://api.example.com?token=secret123") == "***"
