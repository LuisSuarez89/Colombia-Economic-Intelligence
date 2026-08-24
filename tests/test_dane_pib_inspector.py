from pathlib import Path

from openpyxl import Workbook

from colombia_economic_intelligence.sources.dane_pib_inspector import PIBWorkbookInspector


def _workbook(path: Path) -> None:
    workbook = Workbook()
    index = workbook.active
    index.title = "Índice"
    index["A1"] = "Series encadenadas de volumen con año de referencia 2015"
    combinations = [("Datos originales", 12), ("Datos originales", 25), ("Datos originales", 61), ("Datos ajustados por efecto estacional y calendario", 12), ("Datos ajustados por efecto estacional y calendario", 25), ("Datos ajustados por efecto estacional y calendario", 61)]
    for number, (series, aggregation) in enumerate(combinations, 1):
        sheet = workbook.create_sheet(f"Cuadro {number}")
        sheet["A1"] = series
        sheet["A2"] = f"Secciones CIIU Rev. 4 A.C. / {aggregation} agrupaciones"
        for row, title in ((3, "Miles de millones de pesos"), (12, "Tasa de crecimiento anual"), (20, "Tasa de crecimiento año corrido")):
            sheet.cell(row, 1).value = title
            sheet.cell(row + 1, 1).value = "Sección"
            sheet.cell(row + 1, 3).value = 2025
            sheet.merge_cells(start_row=row + 1, start_column=3, end_row=row + 1, end_column=4)
            sheet.cell(row + 2, 3).value = "I"
            sheet.cell(row + 2, 4).value = "II"
            sheet.cell(row + 3, 1).value = "A"
            sheet.cell(row + 3, 2).value = "Agricultura"
        sheet["B7"] = "Valor agregado bruto"
        sheet["B8"] = "Impuestos menos subvenciones sobre los productos"
        sheet["B9"] = "Producto Interno Bruto"
    workbook.save(path)


def test_inspector_expands_merged_years_and_detects_structure(tmp_path: Path) -> None:
    path = tmp_path / "pib.xlsx"
    _workbook(path)
    result = PIBWorkbookInspector.inspect(path)
    assert result.workbook.sheet_count == 7
    assert result.workbook.reference_year == 2015
    assert len(result.tables) == 18
    assert result.periods[0].label == "2025-I"
    assert result.periods[1].label == "2025-II"
    assert result.sheets[1].series == "ORIGINAL"
    assert result.sheets[4].series == "AJUSTADA"
    assert result.sheets[1].aggregation_level == 12
    assert result.activities[1].total_type == "VAB"