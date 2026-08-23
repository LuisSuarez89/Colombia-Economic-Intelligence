from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook

from colombia_economic_intelligence.sources.dane_pib_inspector import (
    PIBWorkbookInspector,
    UnexpectedAggregationLevelError,
    UnexpectedStatusError,
    UnsupportedWorkbookError,
    WorkbookInspectionError,
    _detect_indicators,
    _parse_periods,
)


def create_workbook(path: Path) -> None:
    workbook = Workbook()
    workbook.active.title = "Índice"
    workbook.active["A1"] = "Producto Interno Bruto"
    for number in range(1, 7):
        sheet = workbook.create_sheet(f"Cuadro {number}")
        adjusted = number >= 4
        level = (12, 25, 61)[(number - 1) % 3]
        sheet["B2"] = (
            "Datos ajustados por efecto estacional y calendario"
            if adjusted
            else "Datos originales"
        )
        sheet["B3"] = f"Secciones CIIU Rev. 4 A.C. {level} agrupaciones"
        sheet["B4"] = "Series encadenadas de volumen con año de referencia 2015"
        sheet["B5"] = "Miles de millones de pesos"
        sheet["B6"] = "Tasa de crecimiento trimestral" if adjusted else "Tasa de crecimiento anual"
        sheet["B7"] = "Tasa de crecimiento año corrido"
        sheet["B8"] = "Código Concepto Producto Interno Bruto"
        sheet["F10"] = "2025p"
        sheet["G10"] = "2026pr"
        sheet["F11"] = "IV"
        sheet["G11"] = "I"
        sheet["H11"] = "II"
    workbook.save(path)


def test_missing_file_fails(tmp_path: Path) -> None:
    with pytest.raises(WorkbookInspectionError):
        PIBWorkbookInspector().inspect(tmp_path / "missing.xlsx")


def test_non_xlsx_fails(tmp_path: Path) -> None:
    path = tmp_path / "workbook.csv"
    path.write_text("not an xlsx", encoding="utf-8")

    with pytest.raises(UnsupportedWorkbookError):
        PIBWorkbookInspector().inspect(path)


def test_empty_xlsx_fails(tmp_path: Path) -> None:
    path = tmp_path / "empty.xlsx"
    Workbook().save(path)

    with pytest.raises(WorkbookInspectionError):
        PIBWorkbookInspector().inspect(path)


def test_inspects_known_structure_and_metadata(tmp_path: Path) -> None:
    path = tmp_path / "pib.xlsx"
    create_workbook(path)

    result = PIBWorkbookInspector().inspect(path)

    assert result.source_file == "pib.xlsx"
    assert result.workbook["sheet_count"] == 7
    assert result.detected_series == ("AJUSTADA_ESTACIONAL_CALENDARIO", "ORIGINAL")
    assert result.detected_aggregation_levels == (12, 25, 61)
    assert result.detected_periods == ("2025-Q4", "2026-Q1", "2026-Q2")
    assert result.detected_statuses == ("p", "pr")
    assert "NIVEL" in result.detected_indicators
    assert "CRECIMIENTO_ANUAL" in result.detected_indicators
    assert "CRECIMIENTO_TRIMESTRAL" in result.detected_indicators
    assert "CRECIMIENTO_ANO_CORRIDO" in result.detected_indicators
    assert result.validation_status == "OK"


def test_unexpected_aggregation_level_fails(tmp_path: Path) -> None:
    path = tmp_path / "unexpected-level.xlsx"
    create_workbook(path)
    workbook = load_workbook(path)
    workbook["Cuadro 6"]["B3"] = "Divisiones CIIU 99 agrupaciones"
    workbook.save(path)

    with pytest.raises(UnexpectedAggregationLevelError):
        PIBWorkbookInspector().inspect(path)


def test_unexpected_status_fails(tmp_path: Path) -> None:
    path = tmp_path / "unexpected-status.xlsx"
    create_workbook(path)
    workbook = load_workbook(path)
    workbook["Cuadro 1"]["G10"] = "2026x"
    workbook.save(path)

    with pytest.raises(UnexpectedStatusError):
        PIBWorkbookInspector().inspect(path)


def test_detects_table_by_structural_evidence_even_with_modified_sheet_name(tmp_path: Path) -> None:
    path = tmp_path / "renamed-sheet.xlsx"
    workbook = Workbook()
    workbook.active.title = "Índice"
    workbook.active["A1"] = "Producto Interno Bruto"
    for number in range(1, 7):
        sheet = workbook.create_sheet(f"Hoja {number}")
        adjusted = number >= 4
        level = (12, 25, 61)[(number - 1) % 3]
        sheet["B2"] = (
            "Datos ajustados por efecto estacional y calendario"
            if adjusted
            else "Datos originales"
        )
        sheet["B3"] = f"Secciones CIIU Rev. 4 A.C. {level} agrupaciones"
        sheet["B4"] = "Series encadenadas de volumen con año de referencia 2015"
        sheet["B5"] = "Miles de millones de pesos"
        sheet["B6"] = "Tasa de crecimiento trimestral" if adjusted else "Tasa de crecimiento anual"
        sheet["B7"] = "Tasa de crecimiento año corrido"
        sheet["F10"] = "2025p"
        sheet["G10"] = "2026pr"
        sheet["F11"] = "IV"
        sheet["G11"] = "I"
        sheet["H11"] = "II"
    workbook.save(path)

    result = PIBWorkbookInspector().inspect(path)

    assert len(result.detected_tables) == 6
    assert all(table.sheet.startswith("Hoja ") for table in result.detected_tables)


def test_detect_indicators_from_documented_structural_labels() -> None:
    text = (
        "Datos originales. "
        "Series encadenadas de volumen con año de referencia 2015. "
        "Miles de millones de pesos. "
        "Tasa de crecimiento anual. "
        "Tasa de crecimiento trimestre. "
        "Tasa de crecimiento año corrido."
    )

    indicators = _detect_indicators(text, adjusted=False)

    assert set(indicators) == {
        "NIVEL",
        "CRECIMIENTO_ANUAL",
        "CRECIMIENTO_TRIMESTRAL",
        "CRECIMIENTO_ANO_CORRIDO",
    }


def test_unit_phrase_without_structural_context_is_not_auto_level() -> None:
    text = "Miles de millones de pesos."

    assert _detect_indicators(text, adjusted=False) == ()


def test_non_relevant_note_does_not_infer_indicator() -> None:
    text = "Nota: Tasa de crecimiento anual aparece en una sección de texto no estructural."

    assert _detect_indicators(text, adjusted=False) == ()


def test_parse_periods_tracks_years_statuses_and_quarters() -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Cuadro 1"
    sheet["A10"] = "2025p"
    sheet["A11"] = "IV"
    sheet["D10"] = "2026pr"
    sheet["D11"] = "I"
    sheet["E11"] = "II"
    sheet["F10"] = "2026pr"
    sheet["F11"] = "III"

    periods, statuses = _parse_periods(sheet)

    assert periods == {"2025-Q4", "2026-Q1", "2026-Q2", "2026-Q3"}
    assert statuses == {"p", "pr"}


def test_inspection_is_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "repeatable.xlsx"
    create_workbook(path)
    inspector = PIBWorkbookInspector()

    assert inspector.inspect(path).to_dict() == inspector.inspect(path).to_dict()