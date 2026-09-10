from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_ROOT = Path(__file__).resolve().parents[1] / "app"


def test_summary_renders_functional_page_links_without_navigation_radio(monkeypatch):
    monkeypatch.chdir(APP_ROOT)
    monkeypatch.syspath_prepend(str(APP_ROOT))

    app = AppTest.from_file("Summary.py").run(timeout=30)

    assert not app.exception
    assert not app.sidebar.radio
    assert [link.label for link in app.sidebar.get("page_link")] == [
        "Overview",
        "Users",
        "Activation",
        "Retention",
        "Revenue",
        "Experiments",
        "Churn Risk",
    ]
