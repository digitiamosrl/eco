from fastapi.testclient import TestClient

from app.main import app
from app.uploads import find_upload

client = TestClient(app)

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16


def _store_image(name: str = "abc.png") -> bytes:
    from app.config import settings

    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    (settings.upload_dir / name).write_bytes(PNG)
    return PNG


def test_uploaded_image_is_served() -> None:
    _store_image()
    response = client.get("/files/abc.png")
    assert response.status_code == 200
    assert response.content == PNG
    assert response.headers["content-type"] == "image/png"


def test_missing_file_returns_404() -> None:
    response = client.get("/files/non-esiste.png")
    assert response.status_code == 404
    assert response.json() == {"detail": "File non trovato"}


def test_path_traversal_is_rejected() -> None:
    _store_image()
    assert client.get("/files/..%2Fconfig.py").status_code == 404
    assert client.get("/files/..").status_code == 404
    assert client.get("/files/%2e%2e%2fconfig.py").status_code == 404


def test_find_upload_only_returns_direct_children_of_upload_dir() -> None:
    _store_image()
    assert find_upload("abc.png") is not None
    for bad in ["", ".", "..", "../abc.png", "sub/abc.png", "a\\b.png"]:
        assert find_upload(bad) is None
