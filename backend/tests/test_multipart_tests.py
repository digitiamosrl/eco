from fastapi.testclient import TestClient

from app.api.tests import run_test
from app.config import MAX_IMAGE_BYTES, settings
from app.main import app
from app.uploads import group_variant_fields

client = TestClient(app)

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 32
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 32


def _form(*variants: dict[str, str]) -> dict[str, tuple[None, str]]:
    """Campi di testo in multipart: senza file, httpx manderebbe urlencoded."""
    data = {"kind": "post"}
    for index, variant in enumerate(variants):
        data[f"variants[{index}][label]"] = variant["label"]
        data[f"variants[{index}][text]"] = variant["text"]
    return {key: (None, value) for key, value in data.items()}


def _uploads_dir_files() -> list[str]:
    directory = settings.upload_dir
    return sorted(p.name for p in directory.iterdir()) if directory.exists() else []


def test_group_variant_fields_groups_by_index_and_ignores_other_keys() -> None:
    items = [
        ("kind", "post"),
        ("variants[1][label]", "B"),
        ("variants[0][label]", "A"),
        ("variants[0][text]", "Testo A"),
        ("variants[1][text]", "Testo B"),
        ("variants[10][label]", "K"),
    ]
    assert group_variant_fields(items) == [
        {"label": "A", "text": "Testo A"},
        {"label": "B", "text": "Testo B"},
        {"label": "K"},
    ]


def test_multipart_post_without_images_is_created(validate) -> None:
    response = client.post(
        "/tests", files=_form({"label": "A", "text": "Uno"}, {"label": "B", "text": "Due"})
    )
    assert response.status_code == 201
    created = response.json()
    assert [s["id"] for s in created["stimuli"]] == ["variante-a", "variante-b"]
    assert all("image_url" not in s for s in created["stimuli"])
    validate("test.schema.json", created)


def test_multipart_post_with_image_stores_it_under_a_server_name(validate) -> None:
    fields = _form({"label": "A", "text": "Uno"}, {"label": "B", "text": "Due"})
    response = client.post(
        "/tests",
        files={**fields, "variants[0][image]": ("../../mia foto.png", PNG, "image/png")},
    )
    assert response.status_code == 201
    created = response.json()
    image_url = created["stimuli"][0]["image_url"]
    assert image_url.startswith("/files/") and image_url.endswith(".png")
    name = image_url.removeprefix("/files/")
    assert "/" not in name and "mia" not in name
    assert name in _uploads_dir_files()
    assert "image_url" not in created["stimuli"][1]
    validate("test.schema.json", created)


def test_jpeg_and_webp_are_accepted_by_content(validate) -> None:
    fields = _form({"label": "A", "text": "Uno"}, {"label": "B", "text": "Due"})
    response = client.post(
        "/tests",
        files={
            **fields,
            "variants[0][image]": ("a.txt", JPEG, "text/plain"),
            "variants[1][image]": ("b.png", WEBP, "image/png"),
        },
    )
    assert response.status_code == 201
    urls = [s["image_url"] for s in response.json()["stimuli"]]
    assert urls[0].endswith(".jpg") and urls[1].endswith(".webp")


def test_non_image_content_returns_422_in_italian() -> None:
    fields = _form({"label": "A", "text": "Uno"}, {"label": "B", "text": "Due"})
    response = client.post(
        "/tests",
        files={**fields, "variants[0][image]": ("a.png", b"<html>no</html>", "image/png")},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Formato immagine non valido: usa PNG, JPEG o WebP"}
    assert _uploads_dir_files() == []


def test_image_over_limit_returns_422() -> None:
    big = PNG + b"\x00" * MAX_IMAGE_BYTES
    fields = _form({"label": "A", "text": "Uno"}, {"label": "B", "text": "Due"})
    response = client.post(
        "/tests",
        files={**fields, "variants[0][image]": ("big.png", big, "image/png")},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "L'immagine supera 5 MB"}


def test_one_variant_returns_422() -> None:
    response = client.post("/tests", files=_form({"label": "A", "text": "Uno"}))
    assert response.status_code == 422
    assert response.json() == {"detail": "Richiesta non valida: variants"}


def test_duplicate_labels_return_422() -> None:
    response = client.post(
        "/tests", files=_form({"label": "A", "text": "Uno"}, {"label": "a", "text": "Due"})
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Richiesta non valida: variants"}


def test_empty_text_returns_422() -> None:
    response = client.post(
        "/tests", files=_form({"label": "A", "text": ""}, {"label": "B", "text": "Due"})
    )
    assert response.status_code == 422
    assert response.json()["detail"].startswith("Richiesta non valida")


def test_rejected_second_test_removes_its_images(no_background) -> None:
    assert (
        client.post(
            "/tests", files=_form({"label": "A", "text": "U"}, {"label": "B", "text": "D"})
        ).status_code
        == 201
    )
    fields = _form({"label": "A", "text": "U"}, {"label": "B", "text": "D"})
    response = client.post(
        "/tests",
        files={**fields, "variants[0][image]": ("a.png", PNG, "image/png")},
    )
    assert response.status_code == 409
    assert _uploads_dir_files() == []


def test_multipart_post_reaches_done(no_background) -> None:
    fields = _form({"label": "A", "text": "U"}, {"label": "B", "text": "D"})
    created = client.post(
        "/tests",
        files={**fields, "variants[0][image]": ("a.png", PNG, "image/png")},
    ).json()
    run_test(created["id"])
    assert client.get(f"/tests/{created['id']}").json()["status"] == "done"
