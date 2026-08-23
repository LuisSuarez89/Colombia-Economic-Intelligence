from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook

from colombia_economic_intelligence.sources.dane_pib_inspector import (
    PIBWorkbookInspector,
    UnexpectedAggregationLevelError,
    UnexpectedStatusError,
    UnsupportedWorkbookError,
    WorkbookInspectionError,
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
        sheet["B4"] = "Miles de millones de pesos"
        sheet["B5"] = "Tasa de crecimiento trimestral" if adjusted else "Tasa de crecimiento anual"
        sheet["B6"] = "Tasa de crecimiento año corrido"
        sheet["B7"] = "Código Concepto Producto Interno Bruto"
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


def test_inspection_is_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "repeatable.xlsx"
    create_workbook(path)
    inspector = PIBWorkbookInspector()

    assert inspector.inspect(path).to_dict() == inspector.inspect(path).to_dict()