# Especificacion tecnica de implementacion del PIBExtractor

**Version:** 1.0
**Estado:** diseno tecnico; no implementado
**Fecha:** 2026-08-25
**Rama prevista:** `docs/pib-extractor-implementation-spec`

## 1. Objetivo

Definir como implementar posteriormente el contrato funcional de
`PIBExtractor` descrito en [pib-extractor-spec.md](pib-extractor-spec.md), sin
rediseñar sus responsabilidades al momento de escribir el codigo.

La implementacion debe recibir un XLSX y el `InspectionResult` producido por
`PIBWorkbookInspector`, leer solamente las celdas delimitadas por la
inspeccion y entregar:

```text
ExtractedGDPRecord[] + ExtractionMetadata
```

Este documento decide la estructura tecnica, interfaces, flujo, validaciones,
pruebas y secuencia de implementacion. No implementa ninguna de ellas.

## 2. Contexto del repositorio

La organizacion actual es:

```text
src/
  colombia_economic_intelligence/
    sources/
      dane_pib_inspector.py
      dane_pib_resolver.py

tests/
  test_dane_pib_inspector.py
  test_dane_pib_resolver.py
```

No existe aun un modulo o paquete de extractor, una jerarquia comun de
excepciones de ingestion, una abstraccion de logging, una configuracion de
pipeline ni modelos independientes de `ExtractedGDPRecord` o
`ExtractionMetadata`.

El Inspector actual define en `dane_pib_inspector.py` los dataclasses:

- `ValidationResult`;
- `Period`;
- `ActivityRow`;
- `TableInspection`;
- `TableRegion`;
- `SheetInspection`;
- `WorkbookMetadata`;
- `InspectionResult`.

El resolver define `SourceManifest` en `dane_pib_resolver.py`. El extractor
no debe duplicar ninguno de esos objetos ni crear una segunda representacion
paralela de la inspeccion.

La configuracion actual solo declara `pytest.ini`; no se encontro
`pyproject.toml`, `setup.cfg`, `mypy.ini`, `ruff.toml`, `tox.ini` ni una
configuracion separada de formatter, linter o type checker. `requirements.txt`
ya contiene `openpyxl`, `pandas`, `numpy`, `pandera`, `pyarrow` y `pytest`.
No se agregaran dependencias en este trabajo.

## 3. Fuentes y documentos equivalentes

Se analizaron:

1. `pib-workbook-inspector-spec.md`;
2. `pib-extractor-spec.md`;
3. `pib-data-model.md`, que es el contrato equivalente a la ruta solicitada
   `pib-data-contract.md`, inexistente en el repositorio;
4. `pib-transformer-spec.md`;
5. `dane-pib-xlsx-real-structure.md`;
6. `dane-pib-xlsx-structure.md` como investigacion equivalente de estructura;
7. la implementacion actual del Inspector y del resolver.

No existe `docs/research/dane-pib-trimestral-source-strategy.md`. No se
inventa su contenido. La estrategia de descarga sigue siendo responsabilidad
del resolver y su `SourceManifest`.

Los documentos existentes son coherentes en la frontera principal:

```text
Inspector -> estructura validada
Extractor -> valores y evidencia de celda
Transformer -> normalizacion y reglas de negocio
Modelo estrella -> entidades analiticas
```

## 4. Principios arquitectonicos

1. **El Inspector es la autoridad estructural.** El extractor consume sus
   resultados y no redetecta hojas, cuadros, regiones, indicadores, periodos,
   merges, actividades, agregaciones o series.
2. **Extraer, no interpretar.** El valor publicado, texto, unidad, codigo y
   estado se conservan; no se calculan tasas ni se crean dimensiones.
3. **Fail fast.** Una inspeccion invalida o una inconsistencia critica no
   produce una salida parcialmente valida.
4. **Trazabilidad por registro.** Cada valor conserva hoja, fila y columna,
   ademas del cuadro, region, periodo, indicador y hash.
5. **Determinismo.** El mismo archivo, inspeccion y configuracion producen los
   mismos registros y orden logico.
6. **Compatibilidad futura.** Las coordenadas del XLSX real son evidencia de
   regresion, nunca constantes de implementacion.
7. **Superficie pequena.** Se prefiere un modulo de extractor con modelos
   cercanos y helpers privados antes que una red de modulos prematuros.

## 5. Arquitectura de modulos

La estructura propuesta para la implementacion es:

```text
src/colombia_economic_intelligence/sources/
  dane_pib_inspector.py       # existente; no se modifica
  dane_pib_resolver.py        # existente; no se modifica
  dane_pib_extractor.py       # unico modulo nuevo
```

### `dane_pib_extractor.py`

Responsabilidades:

- definir los modelos de entrada y salida propios del extractor;
- orquestar validacion previa y recorrido;
- abrir el workbook con la misma libreria compatible con el Inspector;
- resolver la hoja y el contexto de cada tabla a partir de la inspeccion;
- leer la interseccion de cada fila economica y periodo;
- construir registros, ubicacion y metrica;
- detectar duplicados e inconsistencias de lectura;
- cerrar el workbook incluso ante error.

Dependencias permitidas:

- biblioteca estandar: `dataclasses`, `datetime`, `decimal`, `hashlib`,
  `pathlib`, `typing` y logging;
- `openpyxl` para abrir y acceder a celdas;
- clases publicas existentes de `dane_pib_inspector.py`;
- `SourceManifest` de `dane_pib_resolver.py`.

El modulo no importara al Transformer, pandas como requisito de ejecucion,
Power BI, red, resolver de URLs ni almacenamiento.

### Modulos que se evitan

- `normalize.py`: pertenece al Transformer.
- `dimensions.py` y `fact.py`: pertenecen al Transformer/modelo estrella.
- `workbook.py`: duplicaria la responsabilidad de acceso del Inspector sin
  evidencia de necesidad.
- `errors.py`: no existe una jerarquia comun; las excepciones del extractor
  pueden permanecer en su modulo hasta que otro componente justifique una
  abstraccion compartida.
- `logging.py` y `metrics.py`: no hay abstracciones compartidas que reutilizar.

## 6. Componentes tecnicos

### 6.1 `PIBExtractor`

Orquestador sin estado entre ejecuciones. No conservara workbook, registros ni
metrica como estado global o de clase. Su operacion publica sera conceptual:

```text
extract(input: ExtractionInput) -> ExtractionResult
```

Puede implementarse como instancia o metodo de clase, pero una misma
instancia no debe hacer que una ejecucion afecte a otra.

### 6.2 `ExtractionInput`

Modelo tipado que agrupa:

- `workbook_path: Path`;
- `inspection: InspectionResult`;
- `source_manifest: SourceManifest | None`;
- `configuration: ExtractionConfiguration`.

El modelo debe transportar la identidad del archivo, no solo sus bytes o una
ruta desconectada de la inspeccion.

### 6.3 `ExtractionConfiguration`

Configuracion explicita y pequena. Debe incluir solamente opciones de
implementacion justificadas, por ejemplo:

- `extractor_version`;
- politica de celdas vacias y textos inesperados;
- si se calcula el hash cuando no lo trae el manifest;
- modo de logging.

No incluira ultimo periodo, numero de filas, nombre de hoja, columna inicial
ni coordenadas del archivo de referencia. Los catalogos controlados se
centralizaran como constantes del contrato solo si no existe una fuente comun
posterior.

### 6.4 `ExtractedGDPRecord`

Modelo inmutable o efectivamente inmutable, preferiblemente dataclass
`frozen`, con los campos del contrato funcional: identidad de fuente, hoja,
cuadro, tabla/region, serie, agregacion, indicador, periodo, fila economica,
actividad/concepto, total, unidad, base de precios, valor y ubicacion.

Los nombres de los campos deben ser los de
`pib-extractor-spec.md`. El mapping desde el Inspector es:

| Inspector | Registro extraido |
|---|---|
| `WorkbookMetadata.filename` | `source_file` |
| manifest `sha256` | `source_sha256` |
| `SheetInspection.name` | `source_sheet` |
| `SheetInspection.cuadro_number` | `cuadro` |
| `TableInspection.table_id` | `table_id` |
| contexto de tabla resuelto | `table_region` |
| `SheetInspection.series` | `series_type` |
| `SheetInspection.aggregation_level` | `aggregation_level` |
| `TableInspection.indicator` / `TableRegion.indicator` | `indicator` |
| `Period.label` | `period` |
| `Period.year`, `quarter`, `status` | campos equivalentes |
| `Period.year_header` + `quarter_header` | `period_original` |
| `ActivityRow.classification_level` | `classification_level` |
| `ActivityRow.classification_code` | `activity_code` |
| `ActivityRow.concept` | `activity_name` |
| `ActivityRow.is_total`, `total_type` | `entity_kind`, `total_type` |
| texto de bloque/metadata inspeccionada | `unit`, `price_basis` |
| `ActivityRow.row_number` y `Period.column` | `source_row`, `source_column` |
| valor de la celda | `value` y `raw_value` |

`ActivityRow.concept` es el nombre funcional de `activity_name`; no se debe
inventar una segunda columna `concept` salvo que el contrato se amplie
explicitamente. Si la implementacion necesita conservar ambos aliases, debe
hacerlo en metadata, no producir dos fuentes de verdad.

### 6.5 `SourceLocation`

Se recomienda un objeto interno pequeno porque agrupa una coordenada siempre
presente:

```text
sheet_name + row_number + column_letter
```

Puede exponerse como parte del registro o aplanarse a
`source_sheet`, `source_row` y `source_column`. No sustituye los campos
contractuales ni usa un indice de lista como trazabilidad.

### 6.6 `ExtractionMetadata`

Modelo separado de los registros. Incluira:

- identidad y hash del archivo;
- version del extractor y configuracion;
- resumen del Inspector;
- inicio y fin de ejecucion;
- `tables_processed`;
- `records_extracted`;
- `records_discarded`;
- `null_values`;
- `duplicates`;
- `errors`;
- `warnings`;
- cobertura por cuadro, region, serie, agregacion e indicador.

Los timestamps solo viven aqui.

### 6.7 `ExtractionResult`

Contenedor conceptual que devuelve:

```text
records: Sequence[ExtractedGDPRecord]
metadata: ExtractionMetadata
```

La secuencia se expone ya ordenada. No debe ser una ruta a un archivo ni un
DataFrame como contrato publico primario.

### 6.8 `ValueReader`

No se propone como clase publica. Un helper privado o una funcion pequena
solo se justificara para centralizar la lectura de una celda, conservar
`raw_value`, distinguir tipos y emitir el diagnostico de coordenadas. No debe
normalizar conceptos, calcular tasas ni inferir indicadores.

## 7. Interfaces y contratos

### `PIBExtractor.extract`

**Parametros:** un `ExtractionInput` completo.

**Precondiciones:**

- `workbook_path` existe, es legible y es un XLSX valido;
- `inspection` no es nulo;
- `inspection.is_valid is True`;
- el nombre/identidad del workbook coincide cuando pueda comprobarse;
- el hash coincide con `source_manifest.sha256` cuando exista;
- cada tabla declarada tiene hoja, region, filas y periodos utilizables;
- las relaciones `TableRegion`/`TableInspection` son univocas.

**Postcondiciones de exito:**

- todos los registros pertenecen a filas y periodos de la inspeccion;
- cada registro tiene ubicacion de celda;
- el orden es determinista;
- no hay claves intermedias duplicadas;
- la metadata reporta conteos y warnings/errores de la ejecucion;
- no se modifica el workbook ni se crea salida persistida.

**Errores:**

- `InvalidInspectionError` para inspeccion ausente o invalida;
- `WorkbookMismatchError` para hash o identidad incompatibles;
- `ExtractionStructureError` para region/tabla/fila/periodo no resoluble;
- `UnexpectedCellValueError` para valor requerido ilegible;
- `DuplicateExtractionError` para clave intermedia repetida.

Estas excepciones son nombres conceptuales. Antes de implementarlas debe
comprobarse si aparece una jerarquia comun; no se crearan excepciones por cada
campo.

## 8. Reconciliacion de `TableRegion` y `TableInspection`

El Inspector actual devuelve ambos objetos, pero no un `region_id` compartido:

- `TableRegion.first_period_column` es un entero;
- `TableInspection.first_period_column` es una letra;
- `TableInspection.table_id` es estable dentro del cuadro;
- ambos exponen `header_row`, `period_row` y periodos.

El extractor necesita una funcion interna de resolucion que construya un
contexto de tabla mediante una coincidencia univoca de:

```text
source_sheet
+ header_row
+ period_row
+ ordered periods/columns
+ indicator
```

La funcion debe fallar si hay cero o varias coincidencias. No se permitira
asociar por posicion de lista cuando existan discrepancias, ni volver a
inspeccionar celdas para “adivinar” la relacion.

**Decision abierta de contrato:** el Inspector podria exponer en el futuro un
identificador comun de region o la columna temporal como tipo uniforme. Eso
simplificaria el adaptador, pero no es necesario modificarlo para implementar
el primer extractor. Mientras tanto, el adaptador debe ser privado, pequeno y
cubierto por tests.

## 9. Validacion previa y fail-fast

El flujo previo al acceso de datos sera:

1. validar la forma de `ExtractionInput`;
2. verificar existencia, extension y legibilidad del archivo;
3. abrir el XLSX con `openpyxl` y convertir errores de apertura en error
   bloqueante;
4. verificar la presencia y validez del `InspectionResult`;
5. comparar `WorkbookMetadata.filename` y manifest con el archivo cuando la
   informacion permita hacerlo;
6. calcular SHA-256 solo si la configuracion lo solicita o el manifest lo
   exige, y compararlo cuando exista;
7. resolver las hojas indicadas por la inspeccion por nombre literal;
8. resolver un contexto unico para cada `TableInspection`/`TableRegion`;
9. comprobar que cada `ActivityRow.row_number` y cada `Period.column` apunten
   a una celda accesible;
10. comenzar el recorrido solo cuando todas las precondiciones criticas
    pasen.

No se debe abrir un segundo workbook, inferir una inspeccion nueva ni continuar
con regiones validas si una precondicion estructural global falla.

## 10. Algoritmo de extraccion

El algoritmo conceptual es:

```text
validar input y precondiciones
abrir workbook
para cada SheetInspection CUADRO en orden de inspeccion:
    para cada TableInspection en orden de lista:
        resolver TableRegion correspondiente
        para cada ActivityRow en orden de row_number:
            para cada Period en orden de columna:
                localizar worksheet[activity_row.row_number][period.column]
                leer y clasificar la celda
                construir ExtractedGDPRecord
                actualizar metricas
                verificar clave natural
cerrar workbook
ordenar/confirmar salida determinista
devolver registros y metadata
```

La salida usa el orden natural del Inspector, reforzado por
`cuadro_number`, indice de tabla, `row_number` y posicion de columna. No se
usaran `set` ni orden de descubrimiento del diccionario para producir datos.

El Extractor no recorre la hoja completa para buscar headers o actividad. Su
unico acceso economico es la interseccion declarada por una fila y un periodo.

## 11. Acceso al workbook

`openpyxl` es la dependencia actual y la eleccion compatible porque el
Inspector tambien utiliza `load_workbook(..., data_only=False,
read_only=False)` y trabaja con acceso por coordenadas y celdas combinadas.

La implementacion debe:

- cargar una sola instancia por ejecucion;
- usar `data_only=False` para conservar la representacion de celda disponible
  para auditoria;
- leer por `worksheet.cell(row, column)` o coordenada equivalente;
- no mutar hojas, celdas, merges ni propiedades;
- cerrar el workbook en una ruta de salida normal o excepcional.

No se recomienda `read_only=True` para la primera version: el Inspector ya
produce coordenadas sobre un workbook cargado en modo normal y el volumen
observado es pequeno. Un cambio a streaming exigiria verificar que las
coordenadas y la apertura compartan comportamiento y no aporta beneficio
probado hoy.

La integracion debe ejecutar Inspector y Extractor sobre el mismo path. No se
pasara una matriz copiada ni se volveran a calcular los merges.

## 12. Value handling

El lector de valor actuara solo sobre la celda de datos localizada:

| Celda | Tratamiento tecnico |
|---|---|
| `int` o `float` de Excel | conservar como numero exacto disponible; convertir al tipo numerico elegido sin redondear |
| `Decimal` | conservar su valor y precision |
| `None` o cadena vacia | no convertir a cero; registrar ausencia segun politica y no emitir observacion numerica valida |
| cero explicito | emitir `value=0` y no contar como nulo |
| string numerico | no parsear por defecto; solo aceptar con regla de formato aprobada |
| `-`, `--`, `...`, `N.D.`, `ND`, `NA` o simbolo | conservar `raw_value`, registrar warning y aplicar politica configurada; no inventar null |
| texto de nota/encabezado | error estructural si aparece dentro de una celda esperada de valor |
| formula no evaluada | error o politica explicita; nunca sustituir silenciosamente |

El Extractor no convierte unidades, porcentajes, separadores locales ni
indicadores. La interpretacion economica queda para el Transformer.

### Precision numerica

La recomendacion es usar `Decimal` para `value` en la frontera del Extractor:

- el workbook contiene valores economicos publicados cuya precision no debe
  alterarse por operaciones binarias;
- `Decimal(str(cell.value))` evita añadir redondeo binario al transportar un
  `float` de `openpyxl`;
- el Extractor no hace calculos, por lo que el coste es pequeno;
- el Data Contract define el destino como `DECIMAL`;
- Power BI y Parquet pueden recibir despues una conversion controlada en la
  capa de transformacion.

`raw_value` conserva el valor y tipo originales para poder revisar esta
conversion. Esta decision no significa calcular ni redondear valores. Si una
prueba demuestra que el formato real requiere preservar una representacion
binaria distinta, debe actualizarse el contrato antes de cambiarla.

## 13. `ExtractedGDPRecord`

El registro debe contener, como minimo:

```text
source_file
source_sha256
source_sheet
cuadro
table_id
table_region
series_type
aggregation_level
indicator
period
period_original
year
quarter
status
classification_level
activity_code
activity_name
entity_kind
total_type
value
unit
price_basis
source_row
source_column
raw_value
```

Reglas de construccion:

- `indicator` viene de `TableRegion.indicator`/`TableInspection.indicator`,
  no de texto del workbook;
- `series_type` viene de `SheetInspection.series`;
- `aggregation_level` viene de `SheetInspection.aggregation_level`;
- `period`, `year`, `quarter` y `status` vienen de `Period`;
- identificadores, nombres y totales vienen de `ActivityRow`;
- `source_row` viene de `ActivityRow.row_number`;
- `source_column` viene de `Period.column`;
- unidad y base se toman de metadata estructural ya disponible, sin
  convertirlas;
- si un campo opcional no existe en el Inspector, queda `None` y se reporta
  solo si la politica lo considera relevante.

No se anadiran IDs surrogate, `fecha_id`, `actividad_id`, `indicador_id`,
`fuente_id` ni columnas de `fact_pib`.

## 14. Period handling

El Extractor trata `Period` como dato ya resuelto. No debe:

- interpretar `2026pr`;
- combinar año y trimestre nuevamente;
- resolver celdas combinadas;
- derivar el ultimo periodo por nombre de archivo;
- asumir que los periodos empiezan en 2005 o terminan en 2026.

Solo debe copiar:

```text
Period.column -> source_column
Period.label -> period
año/trimestre/status -> campos estructurados
Period.year_header + quarter_header -> period_original
```

La ausencia de `p`/`pr` se preserva como `None`. Los periodos observados de
referencia son 2005-I, 2006-I o 2005-II segun indicador y llegan hasta el
periodo entregado por el Inspector; no son constantes de codigo.

## 15. Activities y totals

Las filas se toman de `TableInspection.activities`. El extractor no escanea
columnas descriptoras buscando filas nuevas.

Debe conservar como texto:

- `classification_level`;
- `classification_code` como `activity_code`;
- `concept` como `activity_name`;
- rangos y listas sin expansion.

`is_total` y `total_type` se transportan desde el Inspector. Para los totales
conocidos:

```text
Valor agregado bruto -> VAB
Impuestos menos subvenciones sobre los productos -> IMPUESTOS_MENOS_SUBVENCIONES
Producto Interno Bruto -> PIB
```

El Extractor no convierte esos registros en actividades, no suma filas y no
crea una tabla de totales. `entity_kind` puede indicar actividad/total como
metadata intermedia; la clasificacion definitiva pertenece al Transformer.

## 16. Series, indicadores y agregaciones

Se consumen directamente estos campos:

- `SheetInspection.series`: `ORIGINAL` o `AJUSTADA`;
- `SheetInspection.aggregation_level`: `12`, `25` o `61`;
- `TableRegion.indicator`/`TableInspection.indicator`:
  `NIVEL`, `CRECIMIENTO_ANUAL`, `CRECIMIENTO_TRIMESTRAL` o
  `CRECIMIENTO_ANO_CORRIDO`.

No se aceptara una inferencia alternativa basada en el nombre de la hoja,
conteo de filas, unidad, titulo repetido o valor numerico. La conversion de
`AJUSTADA` a `AJUSTADA_ESTACIONAL_CALENDARIO` se realiza al proyectar al Data
Contract, no dentro del extractor, aunque la etiqueta original debe quedar
en el contexto de origen.

## 17. Units y price basis

`unit` y `price_basis` son metadata de origen. Se conservaran, sin:

- convertir miles de millones a pesos;
- convertir tasas a fracciones;
- mezclar precios constantes y corrientes;
- sustituir `Series encadenadas de volumen con año de referencia 2015` por un
  nombre interno inventado.

Si la inspeccion no expone aun una unidad o base como campo estructurado, el
primer extractor debe mantener la informacion disponible en el resumen de
metadata o dejar el campo nullable. No debe buscar texto global para
reclasificar una region.

## 18. Missing values

La distincion obligatoria es:

```text
None / "" -> ausencia de valor
0         -> valor publicado valido
```

El comportamiento inicial recomendado es no crear un `ExtractedGDPRecord`
valido para una celda temporal vacia; incrementar `null_values`,
`records_discarded` y un warning con ubicacion. Esto evita que una ausencia
se convierta en cero o en una observacion aparentemente completa.

Para strings especiales, la configuracion debe permitir una politica explicita
entre descartar con warning y detener por valor incompatible. El comportamiento
no se puede universalizar porque el XLSX real analizado no contiene esos
marcadores. Nunca se debe traducir un texto no demostrado directamente a
`None` sin conservar `raw_value`.

## 19. Duplicates

La clave de extraccion debe ser tecnica y estable dentro de una ejecucion:

```text
source identity (sha256 si existe, si no source_file)
+ source_sheet
+ table_id/table_region
+ series_type
+ aggregation_level
+ indicator
+ period
+ classification_level
+ activity_code
+ activity_name
```

`source_row` y `source_column` diagnostican la colision; no reemplazan la
identidad. Una clave repetida es error bloqueante, no una oportunidad para
`drop_duplicates()`.

Esta clave no sustituye la clave del modelo estrella. El Transformer aplicara
la natural del Data Contract con dimensiones y fuente. Los archivos con
hashes distintos pueden contener revisiones del mismo periodo y deben poder
coexistir.

## 20. Error handling

No existe una jerarquia de errores compartida. La primera implementacion
mantendra una pequena jerarquia local, con `ExtractionError` como base y las
categorias que aportan diagnostico real:

| Error conceptual | Bloqueante cuando |
|---|---|
| `InvalidInspectionError` | falta la inspeccion o contiene errores |
| `WorkbookMismatchError` | hash/nombre no corresponde al archivo |
| `ExtractionStructureError` | falta hoja, tabla, region, fila o periodo declarado |
| `UnexpectedCellValueError` | una celda requerida es ilegible o incompatible |
| `DuplicateExtractionError` | se repite la clave tecnica |

Errores de acceso a archivo o `openpyxl` se envuelven en `ExtractionError`
con causa y path, sin ocultar la excepcion original.

Warnings no bloqueantes:

- celda vacia en zona de datos;
- texto aislado que la politica permita descartar;
- metadata opcional ausente;
- diferencia de conteo no estructural.

Toda incidencia debe incluir etapa, hoja, cuadro, tabla/region, fila, columna,
periodo e indicador cuando esten disponibles. No se agregaran veinte clases
para distinguir variantes sin impacto operativo.

## 21. Logging

No se registrara una linea por celda. Se usara logging estructurado en cuatro
momentos:

1. **Inicio:** archivo, hash si existe, version y timestamp.
2. **Validacion:** cantidad de hojas/tablas/regiones de la inspeccion y
   resultado de precondiciones.
3. **Resumen:** registros aceptados, descartados, nulos, warnings, errores,
   duplicados y cobertura.
4. **Fin/fallo:** duracion, estado y causa resumida.

La ubicacion completa de cada valor vive en `ExtractedGDPRecord`; el log solo
puede incluir una muestra o el contexto de un error. Hasta que el repositorio
defina una convencion comun, se usara el modulo estandar `logging` sin crear
un logger compartido nuevo.

## 22. Metrics y `ExtractionMetadata`

Los contadores se actualizan en una sola estructura por ejecucion y se
congelan al terminar. Como minimo:

```text
tables_processed
regions_processed
records_extracted
records_discarded
null_values
duplicates
errors
warnings
```

Tambien se conservaran conjuntos ordenados o conteos por cuadro, indicador,
serie, agregacion y periodo, sin usar conjuntos no ordenados en la salida.

Para el XLSX real se espera poder comprobar 7 hojas, 6 cuadros y 18 regiones
mediante el Inspector. No se fija un numero de registros: depende de las
filas economicas, periodos presentes y la politica de vacios.

## 23. Idempotency y determinismo

Para:

```text
mismos bytes XLSX
+ misma InspectionResult
+ misma configuracion
```

la secuencia de registros y todos sus campos logicos deben coincidir.

Garantias:

- no timestamps ni UUIDs en registros;
- no lectura dependiente de estado global;
- no `set` para ordenar datos;
- no seleccion arbitraria ante duplicados;
- periodos en orden del Inspector;
- filas ordenadas por su numero fisico;
- cuadros y tablas en su orden inspeccionado;
- metadata temporal separada de los registros.

Un cambio de hash, inspeccion o configuracion puede producir otra salida y
queda explicitamente identificado en metadata.

## 24. Performance y memoria

El volumen observado del PIB es pequeno frente a la complejidad de preservar
sus merges y coordenadas. Se elige cargar el workbook completo una vez y
acceder por coordenadas, porque:

- coincide con el Inspector actual;
- permite validacion y lectura consistente;
- evita implementar streaming complejo sin una necesidad medida;
- mantiene el algoritmo facil de probar.

No se usara pandas dentro del nucleo: aunque esta instalado, no aporta valor
para leer unas pocas celdas estructuralmente direccionadas y puede perder
metadata/precision al convertir prematuramente. Tampoco se construira un
DataFrame como interfaz obligatoria.

Si futuras publicaciones vuelven insuficiente la memoria, se medira primero
el caso real y se revisara conjuntamente el contrato de Inspector y acceso.

## 25. Dependencias

No se agregan dependencias en este PR ni durante la implementacion inicial.

| Necesidad | Dependencia elegida | Motivo |
|---|---|---|
| leer XLSX | `openpyxl` existente | ya es la libreria del Inspector |
| modelos | `dataclasses` estandar | ya es el patron del Inspector |
| precision | `decimal` estandar | compatible con `DECIMAL` del contrato |
| hash | `hashlib` estandar | compatible con `SourceManifest.sha256` |
| paths | `pathlib` estandar | compatible con interfaces existentes |
| tests | `pytest` existente | suite actual |

`pandas`, `pandera`, `numpy` y `pyarrow` permanecen para capas posteriores o
necesidades ya existentes; no se incorporan al extractor por disponibilidad
accidental.

## 26. Testing architecture

No se crean tests en este trabajo. La implementacion debera agregar tests
cercanos al modulo nuevo, siguiendo `pytest.ini` (`pythonpath = src`,
`testpaths = tests`) y sin modificar los tests existentes salvo una necesidad
futura explicitamente aprobada.

Se recomienda un `tests/test_dane_pib_extractor.py` y fixtures XLSX pequenos
creados en `tmp_path` para aislar cada caso. El XLSX real no se versiona.

### Unit tests

1. input ausente, archivo corrupto o workbook ilegible;
2. `InspectionResult` ausente o invalido;
3. hash y nombre incompatibles;
4. relacion ambigua o inexistente entre region y tabla;
5. una region y una fila economica;
6. un periodo con columna real;
7. lectura int, float y precision Decimal;
8. `None` y string vacio;
9. cero explicito;
10. guion/texto inesperado segun politica;
11. actividad, codigo complejo y total;
12. estados `None`, `p` y `pr` ya resueltos;
13. series `ORIGINAL` y `AJUSTADA`;
14. agregaciones 12, 25 y 61;
15. los cuatro indicadores;
16. coordenadas y hash de trazabilidad;
17. duplicado de clave tecnica;
18. determinismo de registros y orden;
19. cierre del workbook ante error.

Los tests deben construir inspecciones controladas o usar el Inspector real;
no deben hacer que el extractor vuelva a descubrir la estructura.

## 27. Integration testing

Cuando este disponible, ejecutar la cadena real:

```text
PIBWorkbookInspector.inspect(local_data/anex-ProduccionConstantes-IItrim2026.xlsx)
    -> PIBExtractor.extract(...)
```

Verificar como minimo:

- 7 hojas;
- 6 cuadros;
- 18 `TableRegion`/contextos de tabla;
- indicadores correctos por familia;
- periodos recibidos del Inspector, incluido `p`/`pr`;
- presencia de actividades y VAB/impuestos/PIB;
- valores cero preservados;
- trazabilidad hasta hoja/fila/columna;
- cero duplicados;
- salida determinista en dos ejecuciones.

No se inventa un total esperado de registros sin calcularlo a partir del
archivo real y la politica de vacios. Si el archivo no existe, la prueba debe
marcarse como omitida, no fabricar un fixture con el mismo nombre ni agregar
el XLSX a Git.

## 28. Regression tests

Las regresiones deben demostrar que el extractor solo depende del contrato
entregado por el Inspector. En particular, deben modificar fixtures para
cambiar:

- filas de inicio y fin;
- cantidad de periodos;
- ultimo periodo;
- nombres fisicos no contractuales cuando la inspeccion siga siendo valida;
- posiciones de columnas descriptoras;
- merges ya resueltos por el Inspector.

El extractor debe seguir las coordenadas y metadata de la inspeccion. No se
permiten aserciones que obliguen al codigo a conocer filas `12`, `13`, `15`,
columnas concretas, `Cuadro 1` como unico caso o el periodo `2026-II-pr`.

## 29. Contrato con el Transformer

La interfaz entre capas es:

```text
ExtractionResult.records: Sequence[ExtractedGDPRecord]
ExtractionResult.metadata: ExtractionMetadata
```

El Transformer recibe registros largos y es responsable de:

- normalizar nombres y tipos finales;
- convertir periodo a `dim_fecha`;
- construir dimensiones y claves;
- mapear `AJUSTADA` al valor contractual final;
- clasificar actividades y totales;
- construir `fact_pib`;
- validar integridad referencial;
- materializar Parquet/processed.

El Extractor no devuelve tablas finales ni aplica la natural key final del
modelo estrella como reemplazo de su clave tecnica.

## 30. Contrato con el modelo estrella

La proyeccion posterior es:

| ExtractedGDPRecord | Modelo estrella |
|---|---|
| `year`, `quarter`, `period` | `dim_fecha` |
| codigo, nombre, nivel, total | `dim_actividad` |
| indicador y unidad | `dim_indicador` |
| manifest, fuente y hash | `dim_fuente` |
| serie, estado y valor | `fact_pib` |

El Data Contract vigente (`pib-data-model.md`) exige `DECIMAL`, fuente con
SHA-256, niveles 12/25/61, indicadores controlados, series y estados
controlados. El extractor conserva la evidencia necesaria, pero no genera
`fecha_id`, IDs surrogate, tablas ni foreign keys.

## 31. Versioning

La metadata de una ejecucion debe conservar:

- `extractor_version` del modulo/contrato implementado;
- `configuration_version`;
- version o identificador disponible del `InspectionResult`;
- `source_sha256`;
- filename, URL, operacion y timestamp del `SourceManifest` cuando exista;
- fecha de publicacion y año base del workbook/Inspector cuando existan.

La version del archivo se identifica por SHA-256 de sus bytes. El nombre no
puede reemplazar el hash. Revisiones con hashes distintos no se sobreescriben
silenciosamente; su almacenamiento y consulta pertenecen a capas posteriores.

No se agregaran timestamps, UUIDs ni contadores de ejecucion a
`ExtractedGDPRecord`.

## 32. Seguridad y robustez

La implementacion debe manejar de forma acotada:

- path inexistente o no legible;
- XLSX corrupto o que no sea un contenedor valido;
- workbook de otro archivo;
- hash incorrecto;
- hoja declarada ausente;
- inspeccion invalida;
- coordenadas fuera de rango;
- celda con formula/texto inesperado;
- archivo grande fuera de las expectativas.

No se anadiran autenticacion, red, sandbox ni controles de seguridad sin un
requisito real. El extractor no descarga URLs y no modifica archivos.

## 33. Decisiones abiertas

### DataFrame vs objetos tipados

- **Problema:** no existe una interfaz publica comun.
- **Alternativas:** dataclasses + secuencia; DataFrame como API; ambas capas.
- **Impacto:** tipos, trazabilidad, serializacion y acoplamiento a pandas.
- **Recomendacion:** dataclasses inmutables + `Sequence` como API; conversion a
  DataFrame solo en una frontera posterior si se demuestra necesaria.
- **Falta:** confirmar la interfaz que adoptara el Transformer.

### `Decimal` vs `float`

- **Problema:** `openpyxl` puede entregar `int`/`float`, mientras el contrato
  final usa `DECIMAL`.
- **Alternativas:** conservar float; convertir a Decimal; normalizar despues.
- **Impacto:** precision y compatibilidad con consumidores.
- **Recomendacion:** `Decimal` en el registro, `raw_value` para auditoria, sin
  redondeo.
- **Falta:** verificar con ejemplos reales todas las precisiones y el writer
  final de Parquet.

### Ubicacion definitiva del modulo

- **Problema:** el repositorio organiza por fuente, no por pipeline.
- **Alternativas:** `sources/dane_pib_extractor.py`; paquete `pib/extractor/`;
  paquete compartido de ingestion.
- **Impacto:** imports, ownership y futura reutilizacion.
- **Recomendacion:** un modulo en `sources` para la primera implementacion,
  coherente con el Inspector y resolver.
- **Falta:** saber si otros dominios adoptaran una arquitectura transversal.

### Persistencia del resultado

- **Problema:** no esta definido un artefacto intermedio persistido.
- **Alternativas:** memoria; CSV; Parquet; DataFrame.
- **Impacto:** reproducibilidad, tipos y frontera Extractor/Transformer.
- **Recomendacion:** memoria en el Extractor; persistencia en Transformer/Loader.
- **Falta:** contrato operativo de almacenamiento.

### Region compartida Inspector/Extractor

- **Problema:** actualmente `TableRegion` y `TableInspection` no comparten ID
  explicito y tienen tipos distintos para la primera columna.
- **Alternativas:** adaptador privado; modificar Inspector; nuevo modelo comun.
- **Impacto:** robustez del vinculo sin duplicar deteccion.
- **Recomendacion:** adaptador privado validado; revisar un ID comun en una
  futura version del Inspector si aparece una necesidad real.
- **Falta:** decidir si se desea ampliar el contrato publico del Inspector.

### API exacta y excepciones

- **Problema:** no existe patron de servicios ni jerarquia de errores.
- **Alternativas:** funcion pura; clase `PIBExtractor`; excepciones locales o
  compartidas.
- **Impacto:** testabilidad y consistencia futura.
- **Recomendacion:** clase pequena o metodo estatico con `ExtractionInput` y
  errores locales minimos.
- **Falta:** convencion de servicios del siguiente componente.

### Politica de celdas vacias y strings especiales

- **Problema:** una publicacion no prueba su semantica universal.
- **Alternativas:** omitir; registro nulo; error; politica por indicador.
- **Impacto:** conteos y compatibilidad con el Data Contract no nullable.
- **Recomendacion:** omitir del conjunto valido, medir y advertir hasta contar
  con evidencia adicional.
- **Falta:** mas publicaciones DANE y confirmacion metodologica.

## 34. Secuencia de implementacion futura

Esta secuencia es planificacion, no trabajo realizado en este PR:

1. **Modelos/contratos:** definir dataclasses, tipos, campos, configuracion y
   excepciones minimas; verificar mappings con el Inspector.
2. **Nucleo `PIBExtractor`:** validar `ExtractionInput`, abrir/cerrar workbook
   y aplicar fail-fast.
3. **Lectura de `TableRegion`:** implementar el adaptador univoco hacia
   `TableInspection` y acceder solo a coordenadas entregadas.
4. **`ExtractedGDPRecord`:** construir registros largos con periodo, actividad,
   indicador, serie, agregacion, valor y metadata.
5. **Trazabilidad:** incorporar `SourceLocation`, raw value, manifest, hash y
   relacion region/tabla.
6. **Metadata/metricas:** agregar contadores, cobertura y timestamps separados.
7. **Manejo de errores:** completar categorias bloqueantes, warnings y
   mensajes con contexto.
8. **Unit tests:** cubrir input, valores, dominios, duplicados, trazabilidad y
   determinismo con fixtures pequenos.
9. **Integration test:** ejecutar Inspector + Extractor contra el XLSX real
   cuando este disponible.
10. **Validacion completa:** ejecutar pytest, revisar tipos/estilo disponibles,
    `git diff --check` y confirmar que solo cambie el modulo permitido en el
    PR de implementacion.

## 35. Criterios de aceptacion

La implementacion futura sera aceptada si:

- usa el `InspectionResult` recibido y rechaza uno invalido;
- no redetecta hojas, regiones, indicadores, periodos, merges, actividades,
  agregaciones o series;
- implementa la estructura concreta en `sources` sin crear modulos
  innecesarios;
- consume `openpyxl` sin agregar dependencias;
- verifica correspondencia de workbook y hash cuando corresponda;
- relaciona `TableRegion` y `TableInspection` de forma univoca;
- recorre cuadro, region, fila y periodo en orden determinista;
- lee unicamente las celdas direccionadas por la inspeccion;
- conserva todos los campos de `ExtractedGDPRecord` y su valor bruto;
- distingue cero de vacio y no convierte `None` en cero;
- conserva actividades, codigos complejos y los tres tipos de total;
- mantiene indicadores, series, agregaciones, periodos y estados ya resueltos;
- usa `Decimal` o documenta una revision aprobada de esa decision;
- detecta duplicados sin descartarlos silenciosamente;
- produce `ExtractionMetadata` separada, con metricas y errores;
- no incluye timestamps ni IDs aleatorios en registros;
- entrega exactamente `ExtractedGDPRecord[] + ExtractionMetadata` al
  Transformer;
- pasa unit, integration y regression tests definidos;
- no modifica el Inspector, Transformer, modelo estrella, tests existentes,
  workflows ni `local_data`.

## 36. Estado de este documento

Este PR crea unicamente esta especificacion. No crea `dane_pib_extractor.py`,
clases Python, tests, fixtures, dependencias, workflows ni artefactos de
salida. El XLSX real `local_data/anex-ProduccionConstantes-IItrim2026.xlsx`
permanece fuera de Git.
