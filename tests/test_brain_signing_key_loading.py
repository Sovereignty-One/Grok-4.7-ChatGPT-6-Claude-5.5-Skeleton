from __future__ import annotations

import importlib
import sys

import pytest


MODULE_NAME = "sovereign_persistent_brain.scripts._brain_store"


def _import_brain_store_with_bootstrap_key(monkeypatch):
    monkeypatch.setenv("SG_BRAIN_SIGNING_KEY", "11" * 32)
    sys.modules.pop(MODULE_NAME, None)
    return importlib.import_module(MODULE_NAME)


def test_load_signing_key_prefers_environment(monkeypatch, tmp_path):
    brain_store = _import_brain_store_with_bootstrap_key(monkeypatch)
    monkeypatch.setenv("SG_BRAIN_SIGNING_KEY", "aa" * 32)

    key_file = tmp_path / "brain.key"
    key_file.write_text("bb" * 32, "utf-8")
    monkeypatch.setattr(brain_store, "_SIGNING_KEY_FILE", key_file)

    assert brain_store.load_signing_key() == bytes.fromhex("aa" * 32)
    assert key_file.read_text("utf-8") == "bb" * 32


def test_load_signing_key_uses_configured_file(monkeypatch, tmp_path):
    brain_store = _import_brain_store_with_bootstrap_key(monkeypatch)
    monkeypatch.delenv("SG_BRAIN_SIGNING_KEY", raising=False)

    key_file = tmp_path / "brain.key"
    key_file.write_text("ab" * 32, "utf-8")
    monkeypatch.setattr(brain_store, "_SIGNING_KEY_FILE", key_file)
    monkeypatch.delenv("SG_BRAIN_SIGNING_KEY_FILE", raising=False)

    assert brain_store.load_signing_key() == bytes.fromhex("ab" * 32)


def test_load_signing_key_missing_key_fails_without_regeneration(monkeypatch, tmp_path):
    brain_store = _import_brain_store_with_bootstrap_key(monkeypatch)
    monkeypatch.delenv("SG_BRAIN_SIGNING_KEY", raising=False)

    key_file = tmp_path / "missing.key"
    monkeypatch.setattr(brain_store, "_SIGNING_KEY_FILE", key_file)
    monkeypatch.delenv("SG_BRAIN_SIGNING_KEY_FILE", raising=False)

    with pytest.raises(FileNotFoundError, match="SG_BRAIN_SIGNING_KEY"):
        brain_store.load_signing_key()

    assert not key_file.exists()


def test_load_signing_key_invalid_file_fails_without_overwrite(monkeypatch, tmp_path):
    brain_store = _import_brain_store_with_bootstrap_key(monkeypatch)
    monkeypatch.delenv("SG_BRAIN_SIGNING_KEY", raising=False)

    key_file = tmp_path / "invalid.key"
    key_file.write_text("not-hex", "utf-8")
    monkeypatch.setattr(brain_store, "_SIGNING_KEY_FILE", key_file)
    monkeypatch.delenv("SG_BRAIN_SIGNING_KEY_FILE", raising=False)

    with pytest.raises(RuntimeError, match="invalid hex"):
        brain_store.load_signing_key()

    assert key_file.read_text("utf-8") == "not-hex"
