"""Unit tests for Phoenix collector URL + auth helpers."""
from __future__ import annotations

from observability.phoenix_config import (
    describe_phoenix_target,
    is_phoenix_cloud_endpoint,
    normalize_phoenix_collector_endpoint,
    phoenix_otlp_headers,
)


def test_normalize_local_base_url():
    assert (
        normalize_phoenix_collector_endpoint("http://127.0.0.1:6006")
        == "http://127.0.0.1:6006/v1/traces"
    )


def test_normalize_already_full_url():
    url = "http://127.0.0.1:6006/v1/traces"
    assert normalize_phoenix_collector_endpoint(url) == url


def test_normalize_phoenix_cloud_space_url():
    assert (
        normalize_phoenix_collector_endpoint("https://app.phoenix.arize.com/s/my-space")
        == "https://app.phoenix.arize.com/s/my-space/v1/traces"
    )


def test_phoenix_otlp_headers_with_api_key():
    assert phoenix_otlp_headers("secret-key") == {
        "Authorization": "Bearer secret-key"
    }


def test_phoenix_otlp_headers_empty_without_key():
    assert phoenix_otlp_headers("") == {}


def test_is_phoenix_cloud_endpoint():
    assert not is_phoenix_cloud_endpoint("http://127.0.0.1:6006/v1/traces")
    assert is_phoenix_cloud_endpoint("https://app.phoenix.arize.com/s/demo")


def test_describe_phoenix_target():
    assert describe_phoenix_target("http://127.0.0.1:6006", "") == "local Phoenix"
    assert (
        describe_phoenix_target("https://app.phoenix.arize.com/s/x", "key")
        == "Phoenix Cloud"
    )
