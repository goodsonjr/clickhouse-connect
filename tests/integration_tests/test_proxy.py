from pathlib import Path

import pytest
from urllib3 import ProxyManager

from tests.integration_tests.conftest import TestConfig


def clear_proxy_vars(monkeypatch):
    for var in ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "NO_PROXY", "no_proxy"):
        monkeypatch.delenv(var, raising=False)


def test_proxies(client_factory, call, monkeypatch, test_config: TestConfig):
    if not test_config.proxy_address:
        pytest.skip("Proxy address not configured")
    clear_proxy_vars(monkeypatch)
    if test_config.port in (8123, 10723):
        client = client_factory(
            host=test_config.host,
            port=test_config.port,
            username=test_config.username,
            password=test_config.password,
            http_proxy=test_config.proxy_address,
        )
        assert "2" in call(client.command, "SELECT version()")
        assert call(client.ping) is True

        monkeypatch.setenv("HTTP_PROXY", f"http://{test_config.proxy_address}")
        client = client_factory(
            host=test_config.host,
            port=test_config.port,
            username=test_config.username,
            password=test_config.password,
        )
        if hasattr(client, "http"):
            # Sync client uses urllib3
            assert isinstance(client.http, ProxyManager)
        else:
            # Async client uses aiohttp
            assert hasattr(client, "_proxy_url") and client._proxy_url is not None
        assert "2" in call(client.command, "SELECT version()")
        assert call(client.ping) is True

        monkeypatch.setenv("no_proxy", f"{test_config.host}:{test_config.port}")
        client = client_factory(
            host=test_config.host,
            port=test_config.port,
            username=test_config.username,
            password=test_config.password,
        )
        # Check proxy is NOT configured
        if hasattr(client, "http"):
            # Sync client uses urllib3
            assert not isinstance(client.http, ProxyManager)
        else:
            # Async client uses aiohttp
            assert not hasattr(client, "_proxy_url") or client._proxy_url is None
        assert "2" in call(client.command, "SELECT version()")
        assert call(client.ping) is True
    else:
        cert_file = f"{Path(__file__).parent}/proxy_ca_cert.crt"
        client = client_factory(
            host=test_config.host,
            port=test_config.port,
            username=test_config.username,
            password=test_config.password,
            ca_cert=cert_file,
            https_proxy=test_config.proxy_address,
        )
        assert "2" in call(client.command, "SELECT version()")
        assert call(client.ping) is True

        monkeypatch.setenv("HTTPS_PROXY", f"{test_config.proxy_address}")
        client = client_factory(
            host=test_config.host,
            port=test_config.port,
            username=test_config.username,
            password=test_config.password,
            ca_cert=cert_file,
        )
        if hasattr(client, "http"):
            # Sync client uses urllib3
            assert isinstance(client.http, ProxyManager)
        else:
            # Async client uses aiohttp
            assert hasattr(client, "_proxy_url") and client._proxy_url is not None
        assert "2" in call(client.command, "SELECT version()")
        assert call(client.ping) is True


def test_ignore_proxies(client_factory, call, monkeypatch, test_config: TestConfig):
    clear_proxy_vars(monkeypatch)
    if test_config.port in (8123, 10723):
        monkeypatch.setenv("HTTP_PROXY", "https://127.0.0.1:1")
        client = client_factory(
            host=test_config.host,
            port=test_config.port,
            username=test_config.username,
            password=test_config.password,
            use_env_proxy=False,
        )
        assert "2" in call(client.command, "SELECT version()")
        assert call(client.ping) is True

        if hasattr(client, "http"):
            # Sync client uses urllib3
            assert not isinstance(client.http, ProxyManager)
        else:
            # Async client uses aiohttp
            assert hasattr(client, "_proxy_url") and client._proxy_url is None
        assert "2" in call(client.command, "SELECT version()")
        assert call(client.ping) is True

    else:
        monkeypatch.setenv("HTTPS_PROXY", "https://127.0.0.1:1")
        client = client_factory(
            host=test_config.host,
            port=test_config.port,
            username=test_config.username,
            password=test_config.password,
            use_env_proxy=False,
        )
        assert "2" in call(client.command, "SELECT version()")
        assert call(client.ping) is True

        if hasattr(client, "http"):
            # Sync client uses urllib3
            assert not isinstance(client.http, ProxyManager)
        else:
            # Async client uses aiohttp
            assert hasattr(client, "_proxy_url") and client._proxy_url is None
        assert "2" in call(client.command, "SELECT version()")
        assert call(client.ping) is True
