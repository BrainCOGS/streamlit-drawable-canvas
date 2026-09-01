"""Shared fixtures for the Python test suite.

The component's frontend does not need to be built for these tests.
``components.declare_component(path=...)`` records the directory but does not
stat it until the server serves an asset, so ``import streamlit_drawable_canvas``
succeeds against an unbuilt checkout and CI needs no Node toolchain.

Anything that touches Streamlit's runtime (session state, widget values, the
component's return value) must go through ``AppTest``. A bare interpreter has no
script-run context, so those code paths either no-op or report the wrong thing.
"""

from __future__ import annotations

import pytest
from PIL import Image


@pytest.fixture
def rgb_image() -> Image.Image:
    """A small non-square image, so resize tests can tell width from height."""
    return Image.new("RGB", (60, 40), "white")
