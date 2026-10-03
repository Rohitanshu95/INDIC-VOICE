"""Unit tests for device selection."""

import os
from indicvoice.utils.device import get_device, get_device_and_dtype


def test_get_device_explicit():
    assert get_device("cpu") == "cpu"


def test_get_device_env_override(monkeypatch):
    monkeypatch.setenv("INDICVOICE_DEVICE", "cpu")
    assert get_device("auto") == "cpu"


def test_get_device_and_dtype():
    device, dtype = get_device_and_dtype("cpu")
    assert device == "cpu"
