"""Import di un artifact (link pubblico o file HTML): Playwright lo apre e ne segue i pulsanti.

Per ogni percorso riparte dalla prima schermata, preme l'i-esimo elemento cliccabile e poi, a
ogni passo, il primo non ancora premuto che cambia la pagina. Al massimo 3 percorsi.
"""

import hashlib
import logging

from fastapi import HTTPException
from playwright.async_api import Page, async_playwright

from app.prototypes.raw import RawPrototype, RawScreen, RawStart

logger = logging.getLogger(__name__)

MAX_PATHS = 3
MAX_SCREENS = 6
TIMEOUT_MS = 15_000
VIEWPORT = {"width": 1280, "height": 800}
CLICKABLE = "button:visible, a[href]:visible, [role=button]:visible"
IMPORT_FAILED = "Import dell'artifact non riuscito. Riprova tra poco."


async def _fingerprint(page: Page) -> str:
    text = await page.evaluate("document.body.innerText")
    return hashlib.sha1(text.encode()).hexdigest()  # noqa: S324 (confronto, non sicurezza)


async def _screen(page: Page, number: int) -> RawScreen:
    heading = page.locator("h1, h2").first
    name = (await heading.inner_text()).strip() if await heading.count() else ""
    return RawScreen(name or f"Schermata {number}", await page.screenshot())


async def _labels(page: Page) -> list[str]:
    clickable = page.locator(CLICKABLE)
    return [(await clickable.nth(i).inner_text()).strip() for i in range(await clickable.count())]


async def _press(page: Page, label: str) -> bool:
    """Preme il pulsante con quel testo; True se la pagina è cambiata."""
    before = await _fingerprint(page)
    target = page.locator(CLICKABLE).filter(has_text=label).first
    try:
        await target.click(timeout=3_000)
        await page.wait_for_timeout(400)
    except Exception:  # noqa: BLE001 (un pulsante non cliccabile si salta, non blocca l'import)
        return False
    return await _fingerprint(page) != before


async def _follow(page: Page, load, first_label: str | None) -> tuple[RawScreen, ...]:
    await load()
    screens = [await _screen(page, 1)]
    pressed: set[str] = set()
    todo = [first_label] if first_label else []
    while len(screens) < MAX_SCREENS:
        candidates = todo or [lbl for lbl in await _labels(page) if lbl and lbl not in pressed]
        todo = []
        for label in candidates:
            pressed.add(label)
            if await _press(page, label):
                screens.append(await _screen(page, len(screens) + 1))
                break
        else:
            break
    return tuple(screens)


async def _distinct_paths(page: Page, load) -> list[tuple[RawScreen, ...]]:
    await load()
    first_labels = [lbl for lbl in await _labels(page) if lbl][:MAX_PATHS]
    paths: list[tuple[RawScreen, ...]] = []
    for label in first_labels or [None]:
        path = await _follow(page, load, label)
        if len(path) > 1 or not paths:
            paths.append(path)
    return paths


async def import_artifact(*, url: str | None = None, html: str | None = None) -> RawPrototype:
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            try:
                page = await browser.new_page(viewport=VIEWPORT)
                page.set_default_timeout(TIMEOUT_MS)

                async def load() -> None:
                    if url is not None:
                        await page.goto(url, wait_until="networkidle")
                    else:
                        await page.set_content(html or "", wait_until="networkidle")

                paths = await _distinct_paths(page, load)
                title = (await page.title()).strip() or "Artifact"
            finally:
                await browser.close()
    except Exception as exc:
        logger.exception("Cattura dell'artifact fallita")
        raise HTTPException(status_code=502, detail=IMPORT_FAILED) from exc
    starts = tuple(RawStart(f"Percorso {i}", screens) for i, screens in enumerate(paths, start=1))
    return RawPrototype(name=title, starts=starts)
