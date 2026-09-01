"""Unit tests for the module's pure helpers.

These touch no Streamlit runtime, so plain pytest is correct here and AppTest
would add nothing.
"""

from __future__ import annotations

import base64
import io

import pytest
from PIL import Image

from streamlit_drawable_canvas import _data_url_to_image, _resize_img


def _png_data_url(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{encoded}"


# --- _resize_img -----------------------------------------------------------------


def test_resize_img_scales_to_requested_box(rgb_image):
    resized = _resize_img(rgb_image, new_height=100, new_width=200)
    assert (resized.width, resized.height) == (200, 100)


def test_resize_img_uses_default_square_box(rgb_image):
    resized = _resize_img(rgb_image)
    assert (resized.width, resized.height) == (700, 700)


def test_resize_img_does_not_mutate_the_input(rgb_image):
    """The caller keeps its own image; st_canvas rebinds rather than mutating."""
    _resize_img(rgb_image, 100, 200)
    assert (rgb_image.width, rgb_image.height) == (60, 40)


@pytest.mark.parametrize("height,width", [(1, 1), (13, 7), (1000, 3)])
def test_resize_img_handles_extreme_aspect_ratios(rgb_image, height, width):
    resized = _resize_img(rgb_image, height, width)
    assert (resized.width, resized.height) == (width, height)


# --- _data_url_to_image ----------------------------------------------------------


def test_data_url_round_trips_an_image(rgb_image):
    restored = _data_url_to_image(_png_data_url(rgb_image))
    assert (restored.width, restored.height) == (rgb_image.width, rgb_image.height)


def test_data_url_to_image_rejects_a_url_without_the_base64_marker():
    """The helper splits on ';base64,'; anything else is a programming error, not data."""
    with pytest.raises(ValueError):
        _data_url_to_image("data:image/png,notbase64")


# --- _image_to_url compatibility shim --------------------------------------------


def test_image_to_url_wraps_width_for_modern_streamlit(rgb_image, monkeypatch):
    """When image_to_url takes ``layout_config``, the width must be wrapped."""
    import streamlit_drawable_canvas as canvas
    from streamlit.elements.lib.layout_utils import LayoutConfig

    captured = {}

    def fake(image, layout_config, clamp, channels, output_format, image_id):
        captured["size"] = layout_config
        return "/media/abc.png"

    monkeypatch.setattr(canvas.st_image, "image_to_url", fake)
    assert canvas._image_to_url(rgb_image, 150, "an-id") == "/media/abc.png"
    assert isinstance(captured["size"], LayoutConfig)
    assert captured["size"].width == 150


def test_image_to_url_passes_a_bare_width_to_older_streamlit(rgb_image, monkeypatch):
    """Older Streamlit took ``width: int`` positionally; that branch must still work."""
    import streamlit_drawable_canvas as canvas

    captured = {}

    def fake(image, width, clamp, channels, output_format, image_id):
        captured["size"] = width
        return "/media/def.png"

    monkeypatch.setattr(canvas.st_image, "image_to_url", fake)
    assert canvas._image_to_url(rgb_image, 150, "an-id") == "/media/def.png"
    assert captured["size"] == 150
