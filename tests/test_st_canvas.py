"""Behavior tests for ``st_canvas`` itself, driven through ``AppTest``.

``AppTest.from_function`` writes the page function's *source* to a temp script,
so these pages cannot close over anything defined here -- each imports what it
needs inside its own body.
"""

from __future__ import annotations

from streamlit.testing.v1 import AppTest

# --- rendering -------------------------------------------------------------------


def _page_default_canvas() -> None:
    from streamlit_drawable_canvas import st_canvas

    st_canvas(key="canvas")


def test_canvas_renders_with_defaults():
    at = AppTest.from_function(_page_default_canvas).run()
    assert not at.exception, at.exception


def _page_every_drawing_mode() -> None:
    import streamlit as st
    from streamlit_drawable_canvas import st_canvas

    for mode in ("freedraw", "transform", "line", "rect", "circle", "point", "polygon"):
        st_canvas(drawing_mode=mode, key=f"canvas_{mode}")
    st.session_state["ok"] = True


def test_every_documented_drawing_mode_renders():
    """The docstring advertises seven modes; none may blow up on construction."""
    at = AppTest.from_function(_page_every_drawing_mode).run()
    assert not at.exception, at.exception
    assert at.session_state["ok"] is True


# --- background_image ------------------------------------------------------------


def _page_with_background_image() -> None:
    from PIL import Image
    from streamlit_drawable_canvas import st_canvas

    st_canvas(
        background_image=Image.new("RGB", (60, 40), "white"),
        height=100,
        width=150,
        key="canvas_bg",
    )


def test_background_image_does_not_raise():
    """Regression: the background path used to pass an int where Streamlit wanted a
    LayoutConfig, raising "'int' object has no attribute 'width'".

    Streamlit's private image_to_url() grew a ``layout_config`` parameter in place
    of the old positional ``width``. Because this module calls that private helper
    positionally, the mismatch surfaced only at runtime and only when a caller
    actually passed ``background_image`` -- which is why it went unnoticed. Downstream
    apps papered over it by catching AttributeError and re-rendering the canvas with
    no background at all.
    """
    at = AppTest.from_function(_page_with_background_image).run()
    assert not at.exception, at.exception


def _page_background_image_with_explicit_key() -> None:
    from PIL import Image
    from streamlit_drawable_canvas import st_canvas

    # The media-file id embeds the key, so a keyed canvas must work too.
    st_canvas(background_image=Image.new("RGB", (10, 10), "red"), key="keyed")


def test_background_image_with_a_key_does_not_raise():
    at = AppTest.from_function(_page_background_image_with_explicit_key).run()
    assert not at.exception, at.exception


# --- initial_drawing -------------------------------------------------------------


def _page_mutating_initial_drawing() -> None:
    import streamlit as st
    from streamlit_drawable_canvas import st_canvas

    caller_drawing = {"version": "4.4.0", "objects": []}
    st_canvas(initial_drawing=caller_drawing, background_color="#abcdef", key="canvas_init")
    st.session_state["caller_drawing"] = caller_drawing


def test_initial_drawing_is_mutated_in_place():
    """Documents a sharp edge rather than endorsing it.

    st_canvas writes ``background`` into the dict it was handed, so a caller that
    reuses one dict across two canvases silently carries the first canvas's
    background colour into the second. Callers should pass a copy. If this is ever
    fixed to copy internally, this test should flip to asserting the caller's dict
    is untouched.
    """
    at = AppTest.from_function(_page_mutating_initial_drawing).run()
    assert not at.exception, at.exception
    assert at.session_state["caller_drawing"]["background"] == "#abcdef"


def _page_default_initial_drawing() -> None:
    import streamlit as st
    from streamlit_drawable_canvas import st_canvas

    st_canvas(key="canvas_none")
    st.session_state["ok"] = True


def test_initial_drawing_defaults_without_error():
    at = AppTest.from_function(_page_default_initial_drawing).run()
    assert not at.exception, at.exception


# --- CanvasResult ----------------------------------------------------------------


def _page_reading_result() -> None:
    import streamlit as st
    from streamlit_drawable_canvas import st_canvas

    result = st_canvas(key="canvas_result")
    st.session_state["image_data"] = result.image_data
    st.session_state["json_data"] = result.json_data


def test_result_exposes_none_fields_before_any_drawing():
    """With no frontend interaction the component value is None, and both result
    fields must read as None so ``if result.image_data is not None`` guards work."""
    at = AppTest.from_function(_page_reading_result).run()
    assert not at.exception, at.exception
    assert at.session_state["image_data"] is None
    assert at.session_state["json_data"] is None


def _page_result_type() -> None:
    import streamlit as st
    from streamlit_drawable_canvas import CanvasResult, st_canvas

    result = st_canvas(key="canvas_type")
    st.session_state["is_instance"] = isinstance(result, CanvasResult)


def test_result_is_an_instance_not_the_class():
    """Regression: the no-interaction branch used to ``return CanvasResult`` -- the
    class object itself. Attribute reads happened to work because the dataclass
    defaults are None, so it went unnoticed, but isinstance checks and any use of
    dataclasses.asdict() on the result were wrong.
    """
    at = AppTest.from_function(_page_result_type).run()
    assert not at.exception, at.exception
    assert at.session_state["is_instance"] is True
