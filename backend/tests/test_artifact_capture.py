import pytest

from app.prototypes.artifact import import_artifact

pytestmark = pytest.mark.anyio

# Tre schermate in una pagina sola, come fa un artifact: ogni pulsante ne mostra un'altra.
HTML = """
<title>Demo</title>
<div id="app"><h1>Home</h1><button onclick="go('Dettaglio','Conferma')">Avanti</button>
<button onclick="go('Info',null)">Info</button></div>
<script>
function go(title, next) {
  document.getElementById('app').innerHTML =
    '<h1>' + title + '</h1>' +
    (next ? '<button onclick="go(\\'' + next + '\\',null)">Vai</button>' : '');
}
</script>
"""


async def test_artifact_paths_follow_buttons_in_a_real_browser() -> None:
    try:
        raw = await import_artifact(html=HTML)
    except Exception as exc:  # noqa: BLE001
        if "Executable doesn't exist" in str(exc.__cause__):
            pytest.skip("Chromium non installato: playwright install chromium")
        raise
    assert raw.name == "Demo"
    names = [[s.name for s in start.screens] for start in raw.starts]
    assert names == [["Home", "Dettaglio", "Conferma"], ["Home", "Info"]]
    assert all(s.png.startswith(b"\x89PNG") for start in raw.starts for s in start.screens)


# Gli artifact di Claude Design salvano lo stato in localStorage: serve un'origine vera,
# con set_content la pagina è about:blank e lo script si ferma con SecurityError.
STORAGE_HTML = """
<title>Con stato</title>
<div id="app"></div>
<script>
localStorage.setItem('visto', '1');
document.getElementById('app').innerHTML = '<h1>Home salvata</h1>';
</script>
"""


async def test_artifact_can_use_local_storage() -> None:
    try:
        raw = await import_artifact(html=STORAGE_HTML)
    except Exception as exc:  # noqa: BLE001
        if "Executable doesn't exist" in str(exc.__cause__):
            pytest.skip("Chromium non installato: playwright install chromium")
        raise
    assert [s.name for s in raw.starts[0].screens] == ["Home salvata"]
