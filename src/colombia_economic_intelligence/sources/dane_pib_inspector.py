"""Structural inspection of DANE quarterly GDP production workbooks."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any, Iterable

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

EXPECTED_SHEET_COUNT = 7
EXPECTED_AGGREGATIONS = (12, 25, 61)
TOTAL_TYPES = {
    "valor agregado bruto": "VAB",
    "impuestos menos subvenciones sobre los productos": "IMPUESTOS_MENOS_SUBVENCIONES",
    "producto interno bruto": "PIB",
}
QUARTERS = {"I": 1, "II": 2, "III": 3, "IV": 4}
INDICATOR_TITLES = {
    "CRECIMIENTO_ANUAL": ("tasa de crecimiento anual",),
    "CRECIMIENTO_TRIMESTRAL": ("tasa de crecimiento trimestral",),
    "CRECIMIENTO_ANO_CORRIDO": ("tasa de crecimiento año corrido", "tasa de crecimiento ano corrido"),
}
EXPECTED_INDICATORS = {
    "ORIGINAL": ("NIVEL", "CRECIMIENTO_ANUAL", "CRECIMIENTO_ANO_CORRIDO"),
    "AJUSTADA": ("NIVEL", "CRECIMIENTO_TRIMESTRAL", "CRECIMIENTO_ANO_CORRIDO"),
}
EXPECTED_START = {
    "NIVEL": (2005, 1),
    "CRECIMIENTO_ANUAL": (2006, 1),
    "CRECIMIENTO_ANO_CORRIDO": (2006, 1),
    "CRECIMIENTO_TRIMESTRAL": (2005, 2),
}


@dataclass(frozen=True)
class ValidationResult:
    code: str
    severity: str
    message: str
    expected: Any = None
    actual: Any = None


@dataclass(frozen=True)
class Period:
    year: int
    quarter: int
    status: str | None
    column: str
    label: str
    year_header: str | None = None
    quarter_header: str | None = None


@dataclass(frozen=True)
class ActivityRow:
    row_number: int
    classification_level: str
    classification_code: str | None
    concept: str
    is_total: bool
    total_type: str | None


@dataclass
class TableInspection:
    table_id: str
    indicator: str | None
    title: str
    header_row: int | None
    period_row: int | None
    data_start_row: int | None
    data_end_row: int | None
    first_period_column: str | None
    last_period_column: str | None
    period_count: int
    activity_row_count: int
    validation_status: str = "VALID"
    periods: list[Period] = field(default_factory=list)
    activities: list[ActivityRow] = field(default_factory=list)


@dataclass
class SheetInspection:
    name: str
    sheet_type: str
    cuadro_number: int | None
    series: str | None
    aggregation_level: int | None
    expected_tables: int
    detected_tables: list[TableInspection]
    header_structure: dict[str, Any] | None
    validation_status: str = "VALID"


@dataclass(frozen=True)
class WorkbookMetadata:
    filename: str | None
    sheet_count: int | None
    expected_sheet_count: int
    source: str | None
    publication_date: str | None
    reference_year: int | None
    detected_series: tuple[str, ...] | None


@dataclass
class InspectionResult:
    workbook: WorkbookMetadata
    sheets: list[SheetInspection]
    tables: list[TableInspection]
    periods: list[Period]
    activities: list[ActivityRow]
    validations: list[ValidationResult]
    warnings: list[ValidationResult]

    @property
    def is_valid(self) -> bool:
        return not any(item.severity == "ERROR" for item in self.validations)


def _text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value)).strip() if value is not None else ""


def _normalized(value: Any) -> str:
    return _text(value).casefold()


def _row_texts(sheet: Any, row: int) -> list[str]:
    return [_text(sheet.cell(row, column).value) for column in range(1, sheet.max_column + 1)]


def _find_aggregation(texts: Iterable[str]) -> int | None:
    joined = " ".join(texts).casefold()
    for level in reversed(EXPECTED_AGGREGATIONS):
        if re.search(rf"\b{level}\s+agrupaciones\b", joined):
            return level
    return None


def _find_series(texts: Iterable[str]) -> str | None:
    joined = " ".join(texts).casefold()
    if "ajustad" in joined and "efecto estacional" in joined and "calendario" in joined:
        return "AJUSTADA"
    if "datos originales" in joined or "originales" in joined:
        return "ORIGINAL"
    return None


def _parse_year(value: Any) -> tuple[int, str | None] | None:
    match = re.fullmatch(r"(20\d{2})(pr|p)?", _text(value).casefold())
    return (int(match.group(1)), match.group(2)) if match else None


def _merged_cache(sheet: Any) -> dict[tuple[int, int], Any]:
    cache: dict[tuple[int, int], Any] = {}
    for merged in sheet.merged_cells.ranges:
        value = sheet.cell(merged.min_row, merged.min_col).value
        for row in range(merged.min_row, merged.max_row + 1):
            for column in range(merged.min_col, merged.max_col + 1):
                cache[(row, column)] = value
    return cache


def _indicator(texts: Iterable[str]) -> str | None:
    joined = " ".join(_normalized(text) for text in texts)
    for indicator, titles in INDICATOR_TITLES.items():
        if any(title in joined for title in titles):
            return indicator
    return None


def _find_period_header(sheet: Any, title_row: int, merged: dict[tuple[int, int], Any]) -> tuple[int, int, list[Period], list[int], list[int]] | None:
    for header_row in range(title_row + 1, min(sheet.max_row, title_row + 12) + 1):
        for period_row in range(header_row + 1, min(sheet.max_row, header_row + 2) + 1):
            periods: list[Period] = []
            invalid_status: list[int] = []
            invalid_quarters: list[int] = []
            for column in range(1, sheet.max_column + 1):
                year_value = merged.get((header_row, column), sheet.cell(header_row, column).value)
                quarter_header = _text(sheet.cell(period_row, column).value).upper()
                parsed_year = _parse_year(year_value)
                if parsed_year and quarter_header in QUARTERS:
                    year, status = parsed_year
                    label = f"{year}-{quarter_header}" + (f"-{status}" if status else "")
                    periods.append(Period(year, QUARTERS[quarter_header], status, get_column_letter(column), label, _text(year_value), quarter_header))
                elif re.fullmatch(r"20\d{2}[A-Za-z]+", _text(year_value)) and quarter_header in QUARTERS:
                    invalid_status.append(column)
                elif re.fullmatch(r"20\d{2}(?:p|pr)?", _text(year_value), re.IGNORECASE) and quarter_header and quarter_header not in QUARTERS:
                    invalid_quarters.append(column)
            if periods or invalid_status or invalid_quarters:
                return header_row, period_row, periods, invalid_status, invalid_quarters
    return None


def _activities(sheet: Any, start: int, end: int, first_period_column: int, aggregation: int) -> list[ActivityRow]:
    found: list[ActivityRow] = []
    for row in range(start, end + 1):
        values = [_text(sheet.cell(row, column).value) for column in range(1, first_period_column)]
        values = [value for value in values if value]
        if not values:
            continue
        concept = values[-1]
        if concept.casefold().startswith(("fuente:", "actualizado", "pprovisional", "prpreliminar")):
            continue
        code = values[-2] if len(values) > 1 else None
        total_type = next((kind for name, kind in TOTAL_TYPES.items() if name in concept.casefold()), None)
        found.append(ActivityRow(row, f"CIIU_{aggregation}", code, concept, total_type is not None, total_type))
    return found


class PIBWorkbookInspector:
    @classmethod
    def inspect(cls, path: str | Path) -> InspectionResult:
        workbook_path = Path(path)
        workbook = load_workbook(workbook_path, data_only=False, read_only=False)
        validations: list[ValidationResult] = []
        warnings: list[ValidationResult] = []
        sheets: list[SheetInspection] = []
        for sheet in workbook.worksheets:
            all_text = [_text(value) for row in sheet.iter_rows(values_only=True) for value in row if _text(value)]
            normalized_name = _normalized(sheet.title)
            if normalized_name in {"índice", "indice"}:
                sheets.append(SheetInspection(sheet.title, "INDEX", None, None, None, 0, [], None))
                continue
            series = _find_series(all_text)
            aggregation = _find_aggregation(all_text)
            cuadro_match = re.search(r"\bcuadro\s+([1-6])\b", normalized_name)
            cuadro_number = int(cuadro_match.group(1)) if cuadro_match else None
            expected_series = "ORIGINAL" if cuadro_number in (1, 2, 3) else "AJUSTADA" if cuadro_number in (4, 5, 6) else None
            expected_aggregation = {1: 12, 2: 25, 3: 61}.get(((cuadro_number - 1) % 3 + 1) if cuadro_number else 0)
            if cuadro_number and (series != expected_series or aggregation != expected_aggregation):
                validations.append(ValidationResult("UNEXPECTED_STRUCTURE", "ERROR", f"{sheet.title} contradice su combinación declarada", (expected_series, expected_aggregation), (series, aggregation)))
            title_rows: list[tuple[int, str, str]] = []
            for row in range(1, sheet.max_row + 1):
                row_texts = _row_texts(sheet, row)
                indicator = _indicator(row_texts)
                if indicator or (row < sheet.max_row - 1 and any(_parse_year(value) for value in _row_texts(sheet, row + 1)) and any(_text(sheet.cell(row + 2, column).value).upper() in QUARTERS for column in range(1, sheet.max_column + 1))):
                    title_rows.append((row, " ".join(value for value in row_texts if value), indicator))
            tables: list[TableInspection] = []
            merged = _merged_cache(sheet)
            for index, (title_row, title, indicator) in enumerate(title_rows[:3], start=1):
                header_info = _find_period_header(sheet, title_row, merged)
                if not header_info:
                    tables.append(TableInspection(f"Cuadro {cuadro_number or sheet.title}-T{index}", indicator, title, None, None, None, None, None, None, 0, 0, "ERROR"))
                    validations.append(ValidationResult("UNEXPECTED_STRUCTURE", "ERROR", f"No se pudo interpretar la cabecera de {sheet.title} tabla {index}"))
                    continue
                header_row, period_row, periods, invalid_status, invalid_quarters = header_info
                expected_indicator = EXPECTED_INDICATORS.get(series or "", ())[index - 1] if index <= len(EXPECTED_INDICATORS.get(series or "", ())) else None
                resolved_indicator = expected_indicator if index == 1 and indicator is None and "miles de millones de pesos" in title.casefold() else indicator
                first_col = next(column for column in range(1, sheet.max_column + 1) if get_column_letter(column) == periods[0].column)
                next_title = title_rows[index][0] if index < len(title_rows) else sheet.max_row + 1
                activity_rows = _activities(sheet, period_row + 1, next_title - 1, first_col, aggregation or 0)
                table = TableInspection(f"Cuadro {cuadro_number or sheet.title}-T{index}", resolved_indicator, title, header_row, period_row, activity_rows[0].row_number if activity_rows else None, activity_rows[-1].row_number if activity_rows else None, periods[0].column, periods[-1].column, len(periods), len(activity_rows), "VALID", periods, activity_rows)
                tables.append(table)
                expected_indicator = EXPECTED_INDICATORS.get(series or "", ())[index - 1] if index <= len(EXPECTED_INDICATORS.get(series or "", ())) else None
                if resolved_indicator is None or resolved_indicator != expected_indicator:
                    validations.append(ValidationResult("UNEXPECTED_INDICATOR", "ERROR", f"Indicador incompatible en {sheet.title}", expected_indicator, indicator))
                if invalid_status:
                    validations.append(ValidationResult("UNKNOWN_STATUS", "ERROR", f"Estado temporal desconocido en {sheet.title}"))
                if invalid_quarters:
                    validations.append(ValidationResult("INVALID_PERIOD", "ERROR", f"Trimestre inválido en {sheet.title}"))
                if not periods:
                    validations.append(ValidationResult("UNEXPECTED_STRUCTURE", "ERROR", f"No hay períodos interpretables en {sheet.title} tabla {index}"))
                    tables.append(TableInspection(f"Cuadro {cuadro_number or sheet.title}-T{index}", resolved_indicator, title, header_row, period_row, None, None, None, None, 0, 0, "INVALID"))
                    continue
                expected_start = EXPECTED_START.get(resolved_indicator)
                if expected_start and (periods[0].year, periods[0].quarter) != expected_start:
                    validations.append(ValidationResult("INVALID_PERIOD", "ERROR", f"Horizonte inicial inválido en {sheet.title} tabla {index}", expected_start, (periods[0].year, periods[0].quarter)))
                for previous, current in zip(periods, periods[1:]):
                    expected_next = (previous.year + (previous.quarter == 4), 1 if previous.quarter == 4 else previous.quarter + 1)
                    if (current.year, current.quarter) != expected_next:
                        validations.append(ValidationResult("INVALID_PERIOD", "ERROR", f"Períodos no secuenciales en {sheet.title} tabla {index}"))
            if len(tables) != 3:
                validations.append(ValidationResult("EXPECTED_TABLE_COUNT", "ERROR", f"{sheet.title} debe tener tres tablas", 3, len(tables)))
                if len(tables) < 3:
                    validations.append(ValidationResult("MISSING_TABLE", "ERROR", f"{sheet.title} tiene tablas faltantes", 3, len(tables)))
            sheets.append(SheetInspection(sheet.title, "CUADRO", cuadro_number, series, aggregation, 3, tables, {"merged_ranges": tuple(str(item) for item in sheet.merged_cells.ranges)}))
        metadata_text = "\n".join(_text(value) for sheet in workbook.worksheets for row in sheet.iter_rows(values_only=True) for value in row if _text(value))
        reference_match = re.search(r"año de referencia\s+(20\d{2})", metadata_text, re.IGNORECASE)
        date_match = re.search(r"actualizado el\s+([^\n]+)", metadata_text, re.IGNORECASE)
        source_match = re.search(r"fuente:\s*([^\n]+)", metadata_text, re.IGNORECASE)
        detected_series = tuple(sorted({sheet.series for sheet in sheets if sheet.series})) or None
        result = InspectionResult(WorkbookMetadata(workbook_path.name, len(workbook.sheetnames), EXPECTED_SHEET_COUNT, source_match.group(1).strip() if source_match else None, date_match.group(1).strip() if date_match else None, int(reference_match.group(1)) if reference_match else None, detected_series), sheets, [table for sheet in sheets for table in sheet.detected_tables], [period for sheet in sheets for table in sheet.detected_tables for period in table.periods], [activity for sheet in sheets for table in sheet.detected_tables for activity in table.activities], validations, warnings)
        for value, message in ((result.workbook.source, "No se encontró la fuente"), (result.workbook.publication_date, "No se encontró la fecha de publicación"), (result.workbook.reference_year, "No se encontró el año de referencia"), (result.workbook.detected_series, "No se detectaron series")):
            if value is None:
                result.warnings.append(ValidationResult("UNEXPECTED_STRUCTURE", "WARNING", message))
        if len(workbook.sheetnames) != EXPECTED_SHEET_COUNT:
            result.validations.append(ValidationResult("EXPECTED_SHEET_COUNT", "ERROR", "Cantidad de hojas inesperada", EXPECTED_SHEET_COUNT, len(workbook.sheetnames)))
        if not any(sheet.sheet_type == "INDEX" for sheet in sheets):
            result.validations.append(ValidationResult("UNEXPECTED_STRUCTURE", "ERROR", "Falta la hoja Índice"))
        expected_combinations = {
            ("ORIGINAL", 12), ("ORIGINAL", 25), ("ORIGINAL", 61),
            ("AJUSTADA", 12), ("AJUSTADA", 25), ("AJUSTADA", 61),
        }
        detected_combinations = {(sheet.series, sheet.aggregation_level) for sheet in sheets if sheet.sheet_type == "CUADRO"}
        missing_combinations = sorted(expected_combinations - detected_combinations, key=str)
        if missing_combinations:
            result.validations.append(ValidationResult("UNEXPECTED_STRUCTURE", "ERROR", "Faltan combinaciones serie/agregación", sorted(expected_combinations), missing_combinations))
        return result