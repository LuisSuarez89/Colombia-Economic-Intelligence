from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from colombia_economic_intelligence.sources.dane_pib_resolver import (
    AmbiguousDanePibSourceError,
    DanePibValidationError,
    DownloadedFile,
    MissingDanePibSourceError,
    build_manifest,
    calculate_sha256,
    resolve_constant_price_production_url,
    validate_dane_xlsx_url,
)

VALID_URL = "https://www.dane.gov.co/files/operaciones/PIB/anex-PIB-produccion-constantes-2024-4.xlsx"
CURRENT_URL = "https://www.dane.gov.co/index.php/estadisticas-por-tema/cuentas-nacionales/cuentas-nacionales-trimestrales/pib-informacion-tecnica"


def html_with_links(*links: tuple[str, str]) -> str:
    anchors = "\n".join(f'<a href="{href}">{text}</a>' for href, text in links)
    return f"""
    <html><body>
      <h2>Anexos estadísticos PIB producción</h2>
      {anchors}
    </body></html>
    """


def test_validate_accepts_https_dane_xlsx_url() -> None:
    validate_dane_xlsx_url(VALID_URL)


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/files/pib.xlsx",
        "https://sub.dane.gov.co/files/pib.xlsx",
    ],
)
def test_validate_rejects_external_domains(url: str) -> None:
    with pytest.raises(DanePibValidationError):
        validate_dane_xlsx_url(url)


def test_validate_rejects_http_url() -> None:
    with pytest.raises(DanePibValidationError):
        validate_dane_xlsx_url(VALID_URL.replace("https://", "http://"))


def test_validate_rejects_non_xlsx_file() -> None:
    with pytest.raises(DanePibValidationError):
        validate_dane_xlsx_url("https://www.dane.gov.co/files/operaciones/PIB/documento.pdf")


def test_resolves_constant_price_production_link_from_fixture() -> None:
    html = Path("tests/fixtures/dane_pib_current_fixture.html").read_text(encoding="utf-8")

    candidate = resolve_constant_price_production_url(html, CURRENT_URL)

    assert candidate.url == VALID_URL
    assert "PIB a precios constantes" in candidate.text


def test_rejects_current_price_link() -> None:
    html = html_with_links(("https://www.dane.gov.co/files/pib-corrientes.xlsx", "PIB a precios corrientes"))

    with pytest.raises(MissingDanePibSourceError):
        resolve_constant_price_production_url(html, CURRENT_URL)


@pytest.mark.parametrize("label", ["PIB a precios constantes enfoque gasto", "PIB a precios constantes enfoque ingreso"])
def test_rejects_expense_and_income_approaches(label: str) -> None:
    html = html_with_links(("https://www.dane.gov.co/files/pib-constantes-gasto.xlsx", label))

    with pytest.raises(MissingDanePibSourceError):
        resolve_constant_price_production_url(html, CURRENT_URL)


def test_calculates_reproducible_sha256(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.xlsx"
    file_path.write_bytes(b"dane-pib-test")

    assert calculate_sha256(file_path) == "e80aceac3e9a0d95f86890a8719dd730ae56ea6d23ab4de86ee55a4f4b49ce34"


def test_raises_on_multiple_candidates() -> None:
    html = html_with_links(
        (VALID_URL, "PIB a precios constantes"),
        ("https://www.dane.gov.co/files/operaciones/PIB/anex-PIB-produccion-constantes-2025-1.xlsx", "PIB a precios constantes"),
    )

    with pytest.raises(AmbiguousDanePibSourceError):
        resolve_constant_price_production_url(html, CURRENT_URL)


def test_raises_when_expected_link_is_absent() -> None:
    html = html_with_links(("https://www.dane.gov.co/files/operaciones/PIB/metodologia.xlsx", "Metodología"))

    with pytest.raises(MissingDanePibSourceError):
        resolve_constant_price_production_url(html, CURRENT_URL)


def test_build_manifest_uses_known_metadata_without_inventing_publication_date() -> None:
    downloaded = DownloadedFile(
        path=Path("/tmp/file.xlsx"),
        url=VALID_URL,
        filename="anex-PIB-produccion-constantes-2024-4.xlsx",
        file_size_bytes=123,
        sha256="abc",
    )

    manifest = build_manifest(downloaded, datetime(2026, 8, 21, tzinfo=timezone.utc)).to_dict()

    assert manifest["source"] == "DANE"
    assert manifest["enfoque"] == "producción"
    assert manifest["precios"] == "constantes"
    assert manifest["trimestre"] == "2024-Q4"
    assert manifest["fecha_publicacion"] is None
    assert manifest["sha256"] == "abc"
