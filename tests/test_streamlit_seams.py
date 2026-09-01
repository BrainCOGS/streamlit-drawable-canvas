"""Pins the private Streamlit APIs this component reaches into.

``st_canvas`` depends on three things Streamlit does not consider public:

* ``streamlit.components.v1.declare_component`` -- the only public-ish one.
* ``streamlit.elements.lib.image_utils.image_to_url`` -- has already moved module
  once and changed signature once.
* ``streamlit._config.get_option`` -- private accessor for ``server.baseUrlPath``.

Each has broken this component on a Streamlit upgrade before. These tests exist so
the next break is reported *here*, naming the seam, instead of surfacing as an
opaque AttributeError inside a downstream app's canvas.

If one fails after a Streamlit bump, that is the signal to update ``__init__.py``
-- not to delete the test.
"""

from __future__ import annotations

import inspect

import pytest


def test_image_to_url_is_importable_from_its_expected_module():
    """Moved to streamlit.elements.lib.image_utils in a past refactor."""
    from streamlit.elements.lib.image_utils import image_to_url

    assert callable(image_to_url)


def test_image_to_url_still_takes_the_six_parameters_we_pass():
    """The call is positional, so both the order and the count matter."""
    from streamlit.elements.lib.image_utils import image_to_url

    params = list(inspect.signature(image_to_url).parameters)
    assert params == [
        "image",
        "layout_config",
        "clamp",
        "channels",
        "output_format",
        "image_id",
    ]


def test_image_to_url_second_parameter_is_a_layout_config_not_a_width():
    """The break that motivated this suite.

    This parameter used to be ``width: int``. It is now a ``LayoutConfig``, and
    passing the old int raises "'int' object has no attribute 'width'" from deep
    inside Streamlit. ``_image_to_url`` adapts to whichever form is present.
    """
    from streamlit.elements.lib.image_utils import image_to_url

    second = list(inspect.signature(image_to_url).parameters.values())[1]
    assert second.name == "layout_config"


def test_layout_config_accepts_an_integer_width():
    """We hand it the canvas width in pixels; Streamlit must still accept an int."""
    from streamlit.elements.lib.layout_utils import LayoutConfig

    assert LayoutConfig(width=150).width == 150


def test_base_url_path_option_is_readable():
    """Prefixed onto the background image URL when the app is served under a path."""
    import streamlit as st

    assert isinstance(st._config.get_option("server.baseUrlPath"), str)


def test_declare_component_is_available():
    import streamlit.components.v1 as components

    assert callable(components.declare_component)


@pytest.mark.parametrize("attribute", ["image_data", "json_data"])
def test_canvas_result_declares_both_public_fields(attribute):
    """Downstream code reads these two names off the result; keep them stable."""
    import dataclasses

    from streamlit_drawable_canvas import CanvasResult

    assert attribute in {f.name for f in dataclasses.fields(CanvasResult)}
