"""Structural inspection of DANE quarterly GDP XLSX workbooks."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from zipfile import BadZipFile

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

EXPECTED_LEVELS = frozenset({12, 25, 61})
EXPECTED_SERIES = frozenset({"ORIGINAL", "AJUSTADA_ESTACIONAL_CALENDARIO"})
EXPECTED_STATUSES = frozenset({"p", "pr"})
EXPECTED_INDICATORS = frozenset(
    {"NIVEL", "CRECIMIENTO_ANUAL", "CRECIMIENTO_TRIMESTRAL", "CRECIMIENTO_ANO_CORRIDO"}
)
_YEAR_PATTERN = re.compile(r"^(20\d{2})(p|pr)?$", re.IGNORECASE)
_YEAR_WITH_UNKNOWN_STATUS_PATTERN = re.compile(r"^20\d{2}[A-Za-z]+$")
_QUARTERS = {"I": 1, "II": 2, "III": 3, "IV": 4}


class WorkbookInspectionError(RuntimeError):
    """Base error for invalid or unreadable PIB workbooks."""


class StructureInspectionError(WorkbookInspectionError):
    """Raised when the workbook structure is incompatible with the contract."""


class PeriodDetectionError(StructureInspectionError):
    """Raised when no valid period coverage can be identified."""


class UnexpectedAggregationLevelError(StructureInspectionError):
    """Raised when a workbook declares an unsupported aggregation level."""


class UnexpectedStatusError(StructureInspectionError):
    """Raised when a period header contains an unsupported publication status."""


class UnsupportedWorkbookError(WorkbookInspectionError):
    """Raised when the input is not a readable XLSX workbook."""


@dataclass(frozen=True)
class SheetMetadata:
    name: str
    max_row: int
    max_column: int
    hidden: bool
    non_empty_cells: int


@dataclass(frozen=True)
class TableMetadata:
    sheet: str
    series: str
    aggregation_level: int
    indicators: tuple[str, ...]
    descriptor_columns_present: bool
    activity_rows_detected: bool
    pib_total_detected: bool


@dataclass(frozen=True)
class InspectionResult:
    source_file: str
    workbook: dict[str, Any]
    sheets: tuple[SheetMetadata, ...]
    detected_tables: tuple[TableMetadata, ...]
    detected_series: tuple[str, ...]
    detected_aggregation_levels: tuple[int, ...]
    detected_periods: tuple[str, ...]
    detected_statuses: tuple[str, ...]
    detected_indicators: tuple[str, ...]
    validation_status: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value)).strip() if value is not None else ""


def _sheet_text(sheet: Any) -> str:
    return " ".join(_text(cell.value) for row in sheet.iter_rows() for cell in row if cell.value is not None)


def _is_structural_table(sheet: Any) -> bool:
    text = _sheet_text(sheet)
    lowered = text.casefold()
    has_series = (
        "datos originales" in lowered or "datos ajustados por efecto estacional y calendario" in lowered
    )
    has_expected_aggregation = any(f"{level} agrupaciones" in lowered for level in EXPECTED_LEVELS)
    has_indicator_block = any(
        phrase in lowered
        for phrase in (
            "miles de millones de pesos",
            "tasa de crecimiento anual",
            "tasa de crecimiento trimestre",
            "tasa de crecimiento trimestral",
            "tasa de crecimiento año corrido",
            "tasa de crecimiento ano corrido",
        )
    )
    sheet_name_match = re.fullmatch(r"cuadro [1-6]", sheet.title, re.IGNORECASE)
    if sheet_name_match and has_series and has_indicator_block:
        return True
    return bool(has_series and has_expected_aggregation and has_indicator_block)


def _detect_series(text: str, sheet_name: str) -> str:
    lowered = text.casefold()
    if "datos ajustados por efecto estacional y calendario" in lowered:
        return "AJUSTADA_ESTACIONAL_CALENDARIO"
    if "datos originales" in lowered:
        return "ORIGINAL"
    raise StructureInspectionError(f"Cannot determine series family for sheet {sheet_name!r}")


def _detect_level(text: str, sheet_name: str) -> int:
    matches = {int(value) for value in re.findall(r"(?<!\d)(12|25|61|\d+)\s+agrupaciones?", text, re.IGNORECASE)}
    unexpected = matches - EXPECTED_LEVELS
    if unexpected:
        raise UnexpectedAggregationLevelError(f"Unexpected aggregation level(s) {sorted(unexpected)} in {sheet_name}")
    if len(matches) != 1:
        raise StructureInspectionError(f"Cannot determine one aggregation level for sheet {sheet_name!r}")
    return matches.pop()


def _detect_indicators(text: str, adjusted: bool) -> tuple[str, ...]:
    del adjusted
    lowered = text.casefold()
    found: set[str] = set()
    if "miles de millones de pesos" in lowered:
        found.add("NIVEL")
    if "tasa de crecimiento anual" in lowered:
        found.add("CRECIMIENTO_ANUAL")
    if "tasa de crecimiento trimestre" in lowered or "tasa de crecimiento trimestral" in lowered:
        found.add("CRECIMIENTO_TRIMESTRAL")
    if "tasa de crecimiento año corrido" in lowered or "tasa de crecimiento ano corrido" in lowered:
        found.add("CRECIMIENTO_ANO_CORRIDO")
    return tuple(sorted(found))


def _parse_periods(sheet: Any) -> tuple[set[str], set[str]]:
    periods: set[str] = set()
    statuses: set[str] = set()
    for quarter_row in range(2, sheet.max_row + 1):
        quarter_cells = {
            cell.column: _QUARTERS[_text(cell.value).upper()]
            for cell in sheet[quarter_row]
            if _text(cell.value).upper() in _QUARTERS
        }
        if not quarter_cells:
            continue
        for year_row in range(max(1, quarter_row - 3), quarter_row):
            effective_year: tuple[int, str | None] | None = None
            found_for_row = False
            for column in range(1, sheet.max_column + 1):
                raw = _text(sheet.cell(year_row, column).value)
                match = _YEAR_PATTERN.fullmatch(raw)
                if match:
                    effective_year = (int(match.group(1)), match.group(2).lower() if match.group(2) else None)
                elif _YEAR_WITH_UNKNOWN_STATUS_PATTERN.fullmatch(raw):
                    raise UnexpectedStatusError(f"Unexpected publication status in {sheet.title}!{get_column_letter(column)}{year_row}: {raw}")
                if column not in quarter_cells or effective_year is None:
                    continue
                year, status = effective_year
                if status:
                    statuses.add(status)
                    if status not in EXPECTED_STATUSES:
                        raise UnexpectedStatusError(f"Unexpected publication status {status!r} in {sheet.title}")
                periods.add(f"{year}-Q{quarter_cells[column]}")
                found_for_row = True
            if found_for_row:
                break
    return periods, statuses


class PIBWorkbookInspector:
    """Inspect workbook structure without extracting economic observations."""

    def inspect(self, path: str | Path) -> InspectionResult:
        source = Path(path)
        if not source.exists():
            raise WorkbookInspectionError(f"Workbook does not exist: {source}")
        if source.suffix.casefold() != ".xlsx":
            raise UnsupportedWorkbookError(f"Expected an .xlsx file: {source}")
        try:
            workbook = load_workbook(source, read_only=False, data_only=False)
        except (BadZipFile, OSError, ValueError) as exc:
            raise UnsupportedWorkbookError(f"Unable to read XLSX workbook {source}: {exc}") from exc

        sheets = tuple(
            SheetMetadata(
                name=sheet.title,
                max_row=sheet.max_row,
                max_column=sheet.max_column,
                hidden=sheet.sheet_state != "visible",
                non_empty_cells=sum(1 for row in sheet.iter_rows() for cell in row if cell.value is not None),
            )
            for sheet in workbook.worksheets
        )
        if not sheets or not any(sheet.non_empty_cells for sheet in sheets):
            raise StructureInspectionError("Workbook contains no non-empty sheets")

        tables: list[TableMetadata] = []
        periods: set[str] = set()
        statuses: set[str] = set()
        indicators: set[str] = set()
        for sheet in workbook.worksheets:
            if not _is_structural_table(sheet):
                continue
            text = _sheet_text(sheet)
            series = _detect_series(text, sheet.title)
            level = _detect_level(text, sheet.title)
            table_periods, table_statuses = _parse_periods(sheet)
            periods.update(table_periods)
            statuses.update(table_statuses)
            table_indicators = _detect_indicators(text, series == "AJUSTADA_ESTACIONAL_CALENDARIO")
            indicators.update(table_indicators)
            tables.append(
                TableMetadata(
                    sheet=sheet.title,
                    series=series,
                    aggregation_level=level,
                    indicators=table_indicators,
                    descriptor_columns_present="concepto" in text.casefold(),
                    activity_rows_detected="producto interno bruto" in text.casefold(),
                    pib_total_detected="producto interno bruto" in text.casefold(),
                )
            )

        combinations = {(table.series, table.aggregation_level) for table in tables}
        expected_combinations = {(series, level) for series in EXPECTED_SERIES for level in EXPECTED_LEVELS}
        missing = expected_combinations - combinations
        if missing:
            raise StructureInspectionError(f"Missing expected table combinations: {sorted(missing)}")
        if not periods:
            raise PeriodDetectionError("No valid quarterly periods detected")
        if not indicators:
            raise StructureInspectionError("No structural indicators detected")

        return InspectionResult(
            source_file=source.name,
            workbook={"sheet_count": len(sheets), "empty_sheet_count": sum(not sheet.non_empty_cells for sheet in sheets)},
            sheets=sheets,
            detected_tables=tuple(sorted(tables, key=lambda table: table.sheet)),
            detected_series=tuple(sorted({table.series for table in tables})),
            detected_aggregation_levels=tuple(sorted({table.aggregation_level for table in tables})),
            detected_periods=tuple(sorted(periods)),
            detected_statuses=tuple(sorted(statuses)),
            detected_indicators=tuple(sorted(indicators)),
            validation_status="OK",
            warnings=(),
            errors=(),
        )


def inspect_workbook(path: str | Path) -> InspectionResult:
    """Inspect a local DANE PIB XLSX path."""
    return PIBWorkbookInspector().inspect(path)