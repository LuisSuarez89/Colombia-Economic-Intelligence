from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pytest
from openpyxl import Workbook

from colombia_economic_intelligence.sources.dane_pib_extractor import (
    DuplicateExtractionError,
    ExtractionConfiguration,
    ExtractionInput,
    ExtractionStructureError,
    InvalidInspectionError,
    PIBExtractor,
    UnexpectedCellValueError,
)


@dataclass
class Period:
    year: int = 2026
    quarter: int = 2
    status: str | None = "pr"
    column: str = "B"
    label: str = "2026-II-pr"
    year_header: str = "2026pr"
    quarter_header: str = "II"


@dataclass
class Activity:
    row_number: int = 5
    classification_level: str = "CIIU_12"
    classification_code: str | None = "045 - 047"
    concept: str = "Agricultura"
    is_total: bool = False
    total_type: str | None = None


@dataclass
class Table:
    table_id: str = "Cuadro 1-T1"
    indicator: str | None = "NIVEL"
    periods: list[Period] = field(default_factory=lambda: [Period()])
    activities: list[Activity] = field(default_factory=lambda: [Activity()])
    region_id: str = "region-1"
    unit: str | None = "Miles de millones de pesos"
    price_basis: str | None = "precios constantes"


@dataclass
class Sheet:
    name: str = "Cuadro 1"
    sheet_type: str = "CUADRO"
    cuadro_number: int = 1
    series: str = "ORIGINAL"
    aggregation_level: int = 12
    detected_tables: list[Table] = field(default_factory=lambda: [Table()])


@dataclass
class Inspection:
    sheets: list[Sheet] = field(default_factory=lambda: [Sheet()])
    tables: list[Table] = field(default_factory=lambda: [Table()])
    is_valid: bool = True


def _workbook(path: Path, value: object = 123.45) -> None:
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = "Cuadro 1"
    sheet["B5"] = cast(Any, value)
    workbook.save(path)


def _input(path: Path, inspection: Inspection | None = None) -> ExtractionInput:
    resolved = inspection or Inspection()
    return ExtractionInput(path, cast(Any, resolved))


def test_extracts_value_and_preserves_lineage(tmp_path: Path) -> None:
    path = tmp_path / "pib.xlsx"
    _workbook(path)

    result = PIBExtractor.extract(_input(path))

    record = result.records[0]
    assert record.value == Decimal("123.45")
    assert record.source_sheet == "Cuadro 1"
    assert (record.source_row, record.source_column) == (5, "B")
    assert record.activity_code == "045 - 047"
    assert record.unit == "Miles de millones de pesos"
    assert record.period_original == "2026pr-II"
    assert result.metadata.records_extracted == 1


@pytest.mark.parametrize(
    ("series", "indicator", "aggregation"),
    [
        ("ORIGINAL", "NIVEL", 12),
        ("ORIGINAL", "CRECIMIENTO_ANUAL", 25),
        ("ORIGINAL", "CRECIMIENTO_ANO_CORRIDO", 61),
        ("AJUSTADA", "CRECIMIENTO_TRIMESTRAL", 12),
    ],
)
def test_consumes_series_indicator_and_aggregation_from_inspection(
    tmp_path: Path, series: str, indicator: str, aggregation: int
) -> None:
    path = tmp_path / "pib.xlsx"
    _workbook(path)
    inspection = Inspection()
    inspection.sheets[0].series = series
    inspection.sheets[0].aggregation_level = aggregation
    inspection.sheets[0].detected_tables[0].indicator = indicator
    inspection.tables = inspection.sheets[0].detected_tables

    record = PIBExtractor.extract(_input(path, inspection)).records[0]

    assert (record.series_type, record.indicator, record.aggregation_level) == (series, indicator, aggregation)


def test_preserves_zero_and_discards_empty_value(tmp_path: Path) -> None:
    path = tmp_path / "pib.xlsx"
    _workbook(path, 0)
    result = PIBExtractor.extract(_input(path))
    assert result.records[0].value == 0

    _workbook(path, None)
    result = PIBExtractor.extract(_input(path))
    assert result.records == ()
    assert result.metadata.null_values == 1
    assert result.metadata.records_discarded == 1


def test_preserves_p_status_and_future_period_without_hardcoding(tmp_path: Path) -> None:
    path = tmp_path / "pib.xlsx"
    _workbook(path)
    inspection = Inspection()
    inspection.sheets[0].series = "AJUSTADA"
    inspection.sheets[0].detected_tables[0].indicator = "CRECIMIENTO_ANO_CORRIDO"
    inspection.tables = inspection.sheets[0].detected_tables
    inspection.tables[0].periods[0] = Period(year=2031, quarter=4, status="p", column="B", label="2031-IV-p", year_header="2031p", quarter_header="IV")
    inspection.sheets[0].detected_tables = inspection.tables

    record = PIBExtractor.extract(_input(path, inspection)).records[0]

    assert (record.period, record.year, record.quarter, record.status) == ("2031-IV-p", 2031, 4, "p")


def test_rejects_invalid_inspection_and_missing_table_context(tmp_path: Path) -> None:
    path = tmp_path / "pib.xlsx"
    _workbook(path)
    invalid = Inspection(is_valid=False)
    with pytest.raises(InvalidInspectionError):
        PIBExtractor.extract(_input(path, invalid))

    empty = Inspection(sheets=[Sheet(detected_tables=[])], tables=[])
    with pytest.raises(ExtractionStructureError):
        PIBExtractor.extract(_input(path, empty))


def test_rejects_unexpected_text_and_duplicate_keys(tmp_path: Path) -> None:
    path = tmp_path / "pib.xlsx"
    _workbook(path, "N.D.")
    strict = ExtractionInput(
        path,
        cast(Any, Inspection()),
        configuration=ExtractionConfiguration(discard_unexpected_text=False),
    )
    with pytest.raises(UnexpectedCellValueError):
        PIBExtractor.extract(strict)

    inspection = Inspection()
    inspection.tables[0].activities = [Activity(), Activity()]
    inspection.sheets[0].detected_tables = inspection.tables
    _workbook(path, 10)
    with pytest.raises(DuplicateExtractionError):
        PIBExtractor.extract(_input(path, inspection))


def test_output_is_deterministic_and_metadata_is_separate(tmp_path: Path) -> None:
    path = tmp_path / "pib.xlsx"
    _workbook(path, 10)
    first = PIBExtractor.extract(_input(path))
    second = PIBExtractor.extract(_input(path))

    assert first.records == second.records
    assert first.records[0].raw_value == 10
    assert first.metadata.started_at.tzinfo is not None
    assert first.metadata.started_at != second.metadata.started_at