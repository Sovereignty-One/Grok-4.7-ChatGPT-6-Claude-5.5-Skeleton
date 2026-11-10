"""Tests for the explicit three-mode local control-plane policy."""
from __future__ import annotations

import mode_policy


def test_linux_default_is_hybrid(monkeypatch):
    monkeypatch.delenv("SG_MODE", raising=False)
    monkeypatch.setattr(mode_policy.platform, "system", lambda: "Linux")
    assert mode_policy.current_mode() == "hybrid"


def test_offline_disables_external_and_redis(monkeypatch):
    monkeypatch.setenv("SG_MODE", "offline")
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    assert mode_policy.allows_external_network() is False
    assert mode_policy.allows_redis() is False


def test_hybrid_keeps_self_hosted_boundary(monkeypatch):
    monkeypatch.setenv("SG_MODE", "hybrid")
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    payload = mode_policy.mode_payload()
    assert payload["execution_boundary"] == "self-hosted-linux"
    assert payload["network"]["external"] is False
    assert payload["network"]["redis"] is True
    assert payload["pqc_boundary"] is True


def test_online_requires_explicit_mode(monkeypatch):
    monkeypatch.setenv("SG_MODE", "online")
    assert mode_policy.current_mode() == "online"
    assert mode_policy.allows_external_network() is True


def test_invalid_mode_falls_back_to_linux_default(monkeypatch):
    monkeypatch.setenv("SG_MODE", "not-a-mode")
    monkeypatch.setattr(mode_policy.platform, "system", lambda: "Linux")
    assert mode_policy.current_mode() == "hybrid"
