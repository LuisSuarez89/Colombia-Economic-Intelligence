"""Resolve and download DANE quarterly GDP production XLSX sources."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
import os
import re
import tempfile
from urllib.parse import unquote, urljoin, urlparse

import requests

DANE_CURRENT_URL = "https://www.dane.gov.co/index.php/estadisticas-por-tema/cuentas-nacionales/cuentas-nacionales-trimestrales/pib-informacion-tecnica"
DANE_HISTORICAL_URL = "https://www.dane.gov.co/index.php/estadisticas-por-tema/cuentas-nacionales/cuentas-nacionales-trimestrales/historicos-producto-interno-bruto-pib"
DANE_DOMAIN = "www.dane.gov.co"


class DanePibResolverError(RuntimeError):
    """Base error for DANE PIB source resolution failures."""


class AmbiguousDanePibSourceError(DanePibResolverError):
    """Raised when more than one valid constant-price production candidate exists."""


class MissingDanePibSourceError(DanePibResolverError):
    """Raised when no valid constant-price production candidate can be found."""


class DanePibValidationError(DanePibResolverError, ValueError):
    """Raised when a candidate URL does not satisfy source constraints."""


@dataclass(frozen=True)
class LinkCandidate:
    """A link discovered in the DANE HTML and its surrounding text context."""

    url: str
    text: str
    context: str


@dataclass(frozen=True)
class SourceManifest:
    """Metadata for a downloaded DANE PIB XLSX file."""

    source: str
    operation: str
    enfoque: str
    precios: str
    url: str
    filename: str
    trimestre: str | None
    fecha_publicacion: str | None
    download_timestamp: str
    file_size_bytes: int
    sha256: str

    def to_dict(self) -> dict[str, str | int | None]:
        return asdict(self)


@dataclass(frozen=True)
class DownloadedFile:
    """Temporary downloaded file details."""

    path: Path
    url: str
    filename: str
    file_size_bytes: int
    sha256: str


class _AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._anchors: list[dict[str, str]] = []
        self._current: dict[str, str] | None = None
        self._trail: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            attr_map = {key.lower(): value or "" for key, value in attrs}
            self._current = {"href": attr_map.get("href", ""), "text": "", "before": " ".join(self._trail[-24:])}

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._current is not None:
            self._anchors.append(self._current)
            if self._current["text"]:
                self._trail.extend(self._current["text"].split())
            self._current = None

    def handle_data(self, data: str) -> None:
        text = normalize_text(data)
        if not text:
            return
        if self._current is not None:
            self._current["text"] = normalize_text(f"{self._current['text']} {text}")
        else:
            self._trail.extend(text.split())
            self._trail = self._trail[-80:]


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _classify_constant_production(candidate: LinkCandidate) -> bool:
    context_haystack = normalize_text(candidate.context).lower()
    target_haystack = normalize_text(f"{candidate.text} {unquote(candidate.url)}").lower()
    full_haystack = normalize_text(f"{context_haystack} {target_haystack}").lower()
    has_production_block = (
        "anexos estadísticos pib producción" in full_haystack
        or "anexos estadisticos pib produccion" in full_haystack
        or "produccion" in full_haystack
        or "producción" in full_haystack
    )
    has_constant = "precios constantes" in target_haystack or "constantes" in target_haystack
    rejected = any(term in target_haystack for term in ("precios corrientes", "corrientes", "gasto", "ingreso"))
    return has_production_block and has_constant and not rejected


def extract_link_candidates(html: str, base_url: str = DANE_CURRENT_URL) -> list[LinkCandidate]:
    parser = _AnchorParser()
    parser.feed(html)
    candidates: list[LinkCandidate] = []
    for anchor in parser._anchors:
        href = anchor["href"].strip()
        if not href:
            continue
        url = urljoin(base_url, href)
        context = normalize_text(f"{anchor.get('before', '')} {anchor.get('text', '')}")
        candidates.append(LinkCandidate(url=url, text=normalize_text(anchor.get("text", "")), context=context))
    return candidates


def validate_dane_xlsx_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise DanePibValidationError(f"DANE PIB URL must use HTTPS: {url}")
    if parsed.netloc.lower() != DANE_DOMAIN:
        raise DanePibValidationError(f"DANE PIB URL must belong to {DANE_DOMAIN}: {url}")
    if not parsed.path.lower().endswith(".xlsx"):
        raise DanePibValidationError(f"DANE PIB URL must point to an XLSX file: {url}")


def resolve_constant_price_production_url(html: str, base_url: str = DANE_CURRENT_URL) -> LinkCandidate:
    candidates = []
    diagnostics = []
    for candidate in extract_link_candidates(html, base_url):
        try:
            validate_dane_xlsx_url(candidate.url)
        except DanePibValidationError as exc:
            diagnostics.append({"url": candidate.url, "reason": str(exc)})
            continue
        if _classify_constant_production(candidate):
            candidates.append(candidate)
        else:
            diagnostics.append({"url": candidate.url, "reason": "not constant-price production or explicitly rejected"})
    if not candidates:
        raise MissingDanePibSourceError(f"No DANE PIB production constant-price XLSX candidate found. Diagnostics: {diagnostics}")
    unique = {candidate.url: candidate for candidate in candidates}
    if len(unique) > 1:
        raise AmbiguousDanePibSourceError(f"Multiple DANE PIB production constant-price candidates found: {list(unique)}")
    return next(iter(unique.values()))


def fetch_html(url: str = DANE_CURRENT_URL, timeout: float = 30.0) -> str:
    response = requests.get(url, timeout=timeout, allow_redirects=True)
    response.raise_for_status()
    return response.text


def calculate_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = sha256()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _filename_from_url(url: str) -> str:
    name = Path(unquote(urlparse(url).path)).name
    return name or "dane-pib.xlsx"


def download_xlsx(url: str, timeout: float = 60.0, max_redirects: int = 5, min_size_bytes: int = 1, max_size_bytes: int = 100 * 1024 * 1024) -> DownloadedFile:
    validate_dane_xlsx_url(url)
    session = requests.Session()
    session.max_redirects = max_redirects
    tmp_path: Path | None = None
    try:
        with session.get(url, timeout=timeout, allow_redirects=True, stream=True) as response:
            response.raise_for_status()
            final_url = response.url
            validate_dane_xlsx_url(final_url)
            content_type = response.headers.get("content-type", "").lower()
            if content_type and not any(allowed in content_type for allowed in ("spreadsheet", "excel", "octet-stream", "zip")):
                raise DanePibValidationError(f"Unexpected XLSX content type: {content_type}")
            fd, raw_path = tempfile.mkstemp(prefix="dane-pib-", suffix=".xlsx")
            tmp_path = Path(raw_path)
            size = 0
            with os.fdopen(fd, "wb") as file_obj:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    size += len(chunk)
                    if size > max_size_bytes:
                        raise DanePibValidationError(f"Downloaded file exceeds maximum size: {size} > {max_size_bytes}")
                    file_obj.write(chunk)
            if size < min_size_bytes:
                raise DanePibValidationError(f"Downloaded file is too small: {size} < {min_size_bytes}")
            return DownloadedFile(path=tmp_path, url=final_url, filename=_filename_from_url(final_url), file_size_bytes=size, sha256=calculate_sha256(tmp_path))
    except Exception:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)
        raise


def _infer_quarter(filename_or_url: str) -> str | None:
    match = re.search(r"(20\d{2})[-_ ]?([1-4])", filename_or_url)
    if match:
        return f"{match.group(1)}-Q{match.group(2)}"
    return None


def build_manifest(downloaded: DownloadedFile, download_timestamp: datetime | None = None) -> SourceManifest:
    timestamp = download_timestamp or datetime.now(timezone.utc)
    return SourceManifest(
        source="DANE",
        operation="download_pib_produccion_precios_constantes_xlsx",
        enfoque="producción",
        precios="constantes",
        url=downloaded.url,
        filename=downloaded.filename,
        trimestre=_infer_quarter(downloaded.filename),
        fecha_publicacion=None,
        download_timestamp=timestamp.astimezone(timezone.utc).isoformat(),
        file_size_bytes=downloaded.file_size_bytes,
        sha256=downloaded.sha256,
    )


def resolve_download_and_manifest(page_url: str = DANE_CURRENT_URL, timeout: float = 60.0) -> tuple[DownloadedFile, SourceManifest]:
    html = fetch_html(page_url, timeout=timeout)
    candidate = resolve_constant_price_production_url(html, base_url=page_url)
    downloaded = download_xlsx(candidate.url, timeout=timeout)
    return downloaded, build_manifest(downloaded)
