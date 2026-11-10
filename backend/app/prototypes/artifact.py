"""Import di un artifact (link pubblico o file HTML): Playwright lo apre e ne segue i pulsanti.

Per ogni percorso riparte dalla prima schermata, preme l'i-esimo elemento cliccabile e poi, a
ogni passo, il primo non ancora premuto che cambia la pagina. Al massimo 3 percorsi.

La pagina è codice non fidato: il browser può raggiungere solo gli host dell'elenco qui sotto,
così un artifact non può fotografare servizi interni (localhost, rete privata, metadata cloud).
"""

import asyncio
import hashlib
import logging
from urllib.parse import urlparse

from fastapi import HTTPException
from playwright.async_api import Page, Request, Route, async_playwright

from app.prototypes.raw import RawPrototype, RawScreen, RawStart

logger = logging.getLogger(__name__)

MAX_PATHS = 3
MAX_SCREENS = 6
MAX_CANDIDATES = 15
TIMEOUT_MS = 15_000
IMPORT_TIMEOUT_S = 90
VIEWPORT = {"width": 1280, "height": 800}
CLICKABLE = "button:visible, a[href]:visible, [role=button]:visible"
IMPORT_FAILED = "Import dell'artifact non riuscito. Riprova tra poco."
# Host (e sottodomini) che una pagina può caricare: Claude e le CDN degli artifact.
ALLOWED_HOSTS = (
    "claude.ai",
    "claudeusercontent.com",
    "cdnjs.cloudflare.com",
    "cdn.jsdelivr.net",
    "unpkg.com",
    "cdn.tailwindcss.com",
    "code.jquery.com",
    "fonts.googleapis.com",
    "fonts.gstatic.com",
)
_LOCAL_SCHEMES = ("about:", "data:", "blob:")


def is_allowed(url: str) -> bool:
    if url.startswith(_LOCAL_SCHEMES):
        return True
    parsed = urlparse(url)
    host = parsed.hostname or ""
    return parsed.scheme == "https" and any(
        host == allowed or host.endswith(f".{allowed}") for allowed in ALLOWED_HOSTS
    )


async def _guard(route: Route, request: Request) -> None:
    if is_allowed(request.url):
        await route.continue_()
    else:
        logger.warning("Richiesta bloccata dall'artifact: %s", request.url)
        await route.abort()


async def _fingerprint(page: Page) -> str:
    text = await page.evaluate("document.body.innerText")
    return hashlib.sha1(text.encode()).hexdigest()  # noqa: S324 (confronto, non sicurezza)


async def _screen(page: Page, number: int) -> RawScreen:
    heading = page.locator("h1, h2").first
    name = (await heading.inner_text()).strip() if await heading.count() else ""
    return RawScreen(name or f"Schermata {number}", await page.screenshot())


async def _labels(page: Page) -> list[str]:
    clickable = page.locator(CLICKABLE)
    count = min(await clickable.count(), MAX_CANDIDATES)
    return [(await clickable.nth(i).inner_text()).strip() for i in range(count)]


async def _press(page: Page, index: int) -> bool:
    """Preme l'elemento in quella posizione; True se la pagina è cambiata."""
    before = await _fingerprint(page)
    try:
        await page.locator(CLICKABLE).nth(index).click(timeout=3_000)
        await page.wait_for_timeout(400)
    except Exception:  # noqa: BLE001 (un pulsante non cliccabile si salta, non blocca l'import)
        return False
    return await _fingerprint(page) != before


async def _follow(page: Page, load, first_index: int | None) -> tuple[RawScreen, ...]:
    await load()
    screens = [await _screen(page, 1)]
    pressed: set[tuple[str, str]] = set()
    todo = [] if first_index is None else [first_index]
    while len(screens) < MAX_SCREENS:
        here = await _fingerprint(page)
        labels = await _labels(page)
        candidates = todo or [
            i for i, lbl in enumerate(labels) if lbl and (here, lbl) not in pressed
        ]
        todo = []
        for index in candidates:
            pressed.add((here, labels[index]))
            if await _press(page, index):
                screens.append(await _screen(page, len(screens) + 1))
                break
        else:
            break
    return tuple(screens)


async def _distinct_paths(page: Page, load) -> list[tuple[RawScreen, ...]]:
    await load()
    first = [i for i, lbl in enumerate(await _labels(page)) if lbl][:MAX_PATHS]
    paths: list[tuple[RawScreen, ...]] = []
    for index in first or [None]:
        path = await _follow(page, load, index)
        if len(path) > 1 or not paths:
            paths.append(path)
    return paths


async def _capture(url: str | None, html: str | None) -> RawPrototype:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        try:
            page = await browser.new_page(viewport=VIEWPORT)
            page.set_default_timeout(TIMEOUT_MS)
            await page.route("**/*", _guard)

            async def load() -> None:
                if url is not None:
                    await page.goto(url, wait_until="networkidle")
                else:
                    await page.set_content(html or "", wait_until="networkidle")

            await load()
            title = (await page.title()).strip() or "Artifact"
            paths = await _distinct_paths(page, load)
        finally:
            await browser.close()
    starts = tuple(RawStart(f"Percorso {i}", screens) for i, screens in enumerate(paths, start=1))
    return RawPrototype(name=title, starts=starts)


async def import_artifact(*, url: str | None = None, html: str | None = None) -> RawPrototype:
    try:
        async with asyncio.timeout(IMPORT_TIMEOUT_S):
            return await _capture(url, html)
    except Exception as exc:
        logger.exception("Cattura dell'artifact fallita")
        raise HTTPException(status_code=502, detail=IMPORT_FAILED) from exc
