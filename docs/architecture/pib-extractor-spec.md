# Especificación técnica del PIB Extractor

**Versión:** 1.0  
**Estado:** especificación técnica; no implementada  
**Fecha:** 2026-08-25  
**Fuente:** DANE, PIB trimestral desde el enfoque de la producción, precios constantes

## 1. Objetivo

`PIBExtractor` toma un workbook XLSX cuya estructura ya fue validada por
`PIBWorkbookInspector` y extrae las observaciones económicas de sus regiones
de tabla (`TableRegion`) a una representación intermedia larga, determinista y
trazable.

La regla central es **extraer, no interpretar**. El Extractor copia la
evidencia publicada y la metadata estructural resuelta por el Inspector; no
calcula indicadores, no clasifica el modelo analítico y no aplica reglas de
negocio.

## 2. Alcance

El componente debe:

- recibir un workbook y un `InspectionResult` válido;
- recorrer las tablas identificadas por el Inspector;
- leer las celdas de valores dentro de los límites inspeccionados;
- producir un registro por combinación de fila económica y período;
- conservar códigos, conceptos, valores, unidades, estado y coordenadas de origen;
- producir metadata y métricas de la ejecución;
- rechazar entradas estructuralmente no válidas antes de extraer.

La evidencia de referencia es `local_data/anex-ProduccionConstantes-IItrim2026.xlsx`.
No es un artefacto versionado y no forma parte de esta especificación.

## 3. No alcance

Quedan fuera del Extractor: descarga, autenticación, resolución de URL,
almacenamiento, publicación, transformación de negocio, cálculo de tasas,
normalización definitiva, dimensiones, claves surrogate, modelo estrella,
Loader, Power BI, DAX, visualizaciones y GitHub Actions.

En particular, el Extractor no crea `DimDate`, `DimActivity`, `DimIndicator`,
`DimSeries`, `DimAggregation`, `FactGDP` ni sus equivalentes físicos.

## 4. Arquitectura

```mermaid
flowchart TD
    A[DANE XLSX] --> B[PIBWorkbookInspector]
    B --> C[InspectionResult válido]
    C --> D[PIBExtractor]
    A --> D
    D --> E[ExtractedGDPRecord[]]
    E --> F[PIB Transformer]
    F --> G[Modelo estrella]
    G --> H[Power BI]
```

La separación contractual es:

```text
Inspector   -> descubre y valida estructura.
Extractor   -> lee valores según la estructura descubierta.
Transformer -> normaliza y aplica el modelo de datos.
Loader      -> almacena o publica el resultado posterior.
```

## 5. Relación con `PIBWorkbookInspector`

La precondición obligatoria es:

```text
inspection.is_valid == True
```

Si es falsa, el Extractor debe detenerse sin generar una salida de datos
aceptable. No debe intentar extraer “lo mejor posible”.

El Inspector ya determina:

- hojas y número de cuadro;
- serie y nivel de agregación;
- bloques y su indicador;
- límites de encabezado y región;
- columnas temporales;
- períodos, año, trimestre y estado `p`/`pr`;
- filas económicas, códigos, conceptos y totales;
- warnings y errores estructurales.

El Extractor consume esos campos. No vuelve a buscar textos para inferir
`NIVEL`, `CRECIMIENTO_ANUAL`, `CRECIMIENTO_TRIMESTRAL` o
`CRECIMIENTO_ANO_CORRIDO`; debe utilizar `table_region.indicator` o el campo
equivalente del contrato implementado.

En la implementación actual, `TableInspection` contiene las filas
económicas, sus coordenadas y los períodos; `TableRegion` contiene además el
indicador, los límites de encabezado y la primera columna temporal. La
implementación futura debe resolver ambos objetos mediante una relación
estable, sin redescubrir la estructura del XLSX. Si se requiere un campo que
el Inspector no expone, es una ampliación del contrato del Inspector, no una
heurística privada del Extractor.

## 6. Input Contract

La entrada conceptual es:

```text
ExtractionInput
  workbook_path: Path o workbook legible
  inspection: InspectionResult
  source_manifest: SourceManifest, si está disponible
  configuration: configuración explícita y versionada
```

`workbook_path` debe apuntar al mismo archivo cuya estructura produjo
`inspection`. La implementación debe verificar que el archivo sea legible y,
cuando exista `source_manifest`, que su hash corresponda al archivo leído.

La inspección debe suministrar, como mínimo, por cada tabla:

| Campo | Uso del Extractor |
|---|---|
| hoja y cuadro | contexto de origen |
| `series` | `ORIGINAL` o familia ajustada |
| `aggregation_level` | `12`, `25` o `61` |
| `indicator` | indicador controlado ya resuelto |
| límites de región | filas y columnas que se pueden leer |
| `periods` | columna, etiqueta, año, trimestre y estado |
| filas económicas | fila, clasificación, código y concepto |
| metadata estructural | unidad, base, fuente y encabezados cuando estén disponibles |

El Extractor puede leer directamente del workbook únicamente las celdas de
valores y, para trazabilidad, su representación cruda y coordenada. Puede
leer la unidad o notas asociadas si forman parte de la región ya identificada,
pero no puede usarlas para volver a clasificar el indicador o la serie.

## 7. Cobertura de las regiones reales

Para la publicación de referencia se esperan 6 cuadros y 18 regiones:

| Cuadros | Serie | Agregación | Indicadores por cuadro |
|---|---|---:|---|
| 1, 2, 3 | `ORIGINAL` | 12, 25, 61 | `NIVEL`, `CRECIMIENTO_ANUAL`, `CRECIMIENTO_ANO_CORRIDO` |
| 4, 5, 6 | `AJUSTADA` | 12, 25, 61 | `NIVEL`, `CRECIMIENTO_TRIMESTRAL`, `CRECIMIENTO_ANO_CORRIDO` |

El número 18 es un criterio de integración de esta publicación, no un límite
temporal permanente. Los períodos se toman siempre de la inspección. No se
hardcodean `2026`, `2026-II` ni `2026-II-pr`.

## 8. Output Contract: registro largo

La salida lógica es una secuencia ordenada de `ExtractedGDPRecord`. Cada
registro representa una observación publicada para una fila económica, un
período, un indicador, una serie y una agregación.

### 8.1 Campos obligatorios del registro

| Campo | Tipo conceptual | Regla |
|---|---|---|
| `source_file` | texto | nombre o identidad del archivo; no solo una ruta local |
| `source_sha256` | texto nullable | hash del manifest, si existe |
| `source_sheet` | texto | nombre literal de la hoja |
| `cuadro` | entero | número del cuadro |
| `table_id` | texto | identificador estable de la tabla inspeccionada |
| `table_region` | texto | identificador de región/bloque para auditoría |
| `series_type` | texto | `ORIGINAL` o `AJUSTADA` en esta capa |
| `aggregation_level` | entero | `12`, `25` o `61` |
| `indicator` | texto | valor entregado por el Inspector |
| `period` | texto | etiqueta lógica, por ejemplo `2026-II-pr` |
| `period_original` | texto | encabezado publicado, por ejemplo año `2026pr` + trimestre `II` |
| `year` | entero | año estructurado del Inspector |
| `quarter` | entero | 1 a 4 |
| `status` | texto nullable | `p`, `pr` o ausencia |
| `classification_level` | texto | nivel CIIU publicado |
| `activity_code` | texto nullable | código textual sin expandir ni reescribir |
| `activity_name` | texto | concepto/descripción publicada |
| `entity_kind` | controlado o nullable | actividad, total o sin clasificar según contrato futuro |
| `total_type` | texto nullable | `VAB`, `IMPUESTOS_MENOS_SUBVENCIONES` o `PIB` |
| `value` | número nullable | valor numérico publicado, sin cálculo |
| `unit` | texto nullable | unidad publicada, por ejemplo `Miles de millones de pesos` |
| `price_basis` | texto nullable | evidencia de precios constantes/base 2015 |
| `source_row` | entero | fila física de Excel |
| `source_column` | texto | columna física de Excel |
| `raw_value` | texto/objeto nullable | representación de celda para auditoría |

Los nombres son el contrato lógico de esta especificación. Los tipos físicos
pueden implementarse con objetos tipados o un formato tabular, pero no deben
perder campos ni cambiar su semántica.

`entity_kind` no se convierte todavía en una dimensión definitiva. Su uso
permite preservar la distinción entre actividad y agregado hasta que el
Transformer la resuelva; si el contrato existente no lo admite, esa distinción
debe conservarse en metadata junto con `total_type`.

### 8.2 Metadata separada de los datos

La salida debe incluir un `ExtractionMetadata` separado de los registros:

```text
ExtractionMetadata
  source_manifest
  inspector_summary
  configuration_version
  extractor_version
  started_at / completed_at
  tables_processed
  records_extracted
  records_discarded
  null_values
  duplicates
  errors
  warnings
```

Los timestamps pertenecen a esta metadata, nunca a la identidad de un
registro económico.

## 9. Formato intermedio elegido

La interfaz lógica será una colección de objetos tipados equivalente a
`ExtractedGDPRecord[]` y `ExtractionMetadata`. Para integración tabular, el
formato físico recomendado es un DataFrame durante la ejecución y Parquet
como artefacto posterior del Transformer, no como responsabilidad del
Extractor.

Esta elección conserva tipos, hace explícitos los campos de trazabilidad,
facilita tests unitarios por registro y se adapta al volumen pequeño del PIB.
CSV no es el contrato primario porque puede perder tipos, nulos y precisión;
Parquet es apropiado para `processed`, pero almacenar allí el resultado del
Extractor mezclaría extracción con almacenamiento. La interfaz debe permitir
serialización futura sin rediseñar los campos.

**Decisión abierta:** el repositorio no define todavía una clase común de
registros ni una política de persistencia del resultado intermedio. Antes de
implementar debe elegirse entre dataclasses/objetos tipados y un DataFrame
como interfaz pública, manteniendo este esquema lógico.

## 10. Reglas de extracción

1. Abrir el workbook sin modificarlo.
2. Verificar `inspection.is_valid` y correspondencia del archivo/manifest.
3. Recorrer las tablas en el orden estable de la inspección.
4. Para cada fila económica inspeccionada, recorrer sus períodos en el orden
   de columnas temporales.
5. Leer únicamente la intersección fila económica/columna de período.
6. Copiar el valor, la unidad y la metadata ya resuelta.
7. Emitir coordenadas y encabezados originales para cada registro.
8. Validar la clave natural intermedia antes de entregar la salida.

No se deben leer filas de notas, encabezados, separadores o la hoja `Índice`
como observaciones. No se deben usar posiciones fijas como `12`, `13`, `15`
o `2026` para encontrar datos; las coordenadas vienen de la inspección.

## 11. Indicadores, series y agregaciones

Los únicos indicadores iniciales son exactamente los del Inspector y del Data
Contract: `NIVEL`, `CRECIMIENTO_ANUAL`, `CRECIMIENTO_TRIMESTRAL` y
`CRECIMIENTO_ANO_CORRIDO`. El Extractor conserva el código recibido, sin
calcular tasas ni sustituirlo por el texto del título.

`series_type` debe conservar la diferencia entre `ORIGINAL` y `AJUSTADA`.
La correspondencia posterior con `AJUSTADA_ESTACIONAL_CALENDARIO` pertenece
al Transformer/Data Contract y no debe ocultar la etiqueta publicada en la
metadata de origen.

`aggregation_level` conserva el entero `12`, `25` o `61`. No se convierte en
un nombre arbitrario ni se deduce contando filas.

## 12. Períodos y estados

El período se toma de `Period` producido por el Inspector. Cada registro debe
conservar la etiqueta original y la representación estructurada:

```text
year=2026, quarter=2, status="pr"
period="2026-II-pr"
period_original="2026pr-II"
```

El Extractor no vuelve a resolver merged cells, años ni trimestres, y no
calcula tasas. Debe aceptar futuros períodos sin asumir un último período
concreto.

Los estados son `p`, `pr` o ausencia (`null`). Se conserva el código tal como
lo entrega el Inspector; no se cambia a `provisional` o `preliminar`.

## 13. Actividades, conceptos y totales

El código, concepto, nivel CIIU e identificadores se copian como texto del
workbook. Los rangos y listas, como `045 - 047` o `001, 002, 004 - 008, 013`,
no se expanden.

El Extractor conserva por separado las filas de actividad y los agregados:

- `Valor agregado bruto` -> `VAB`;
- `Impuestos menos subvenciones sobre los productos` ->
  `IMPUESTOS_MENOS_SUBVENCIONES`;
- `Producto Interno Bruto` -> `PIB`.

No convierte un total en actividad ordinaria ni crea una tabla especial de
totales. La clasificación definitiva corresponde al Transformer. La fila
`Producto Interno Bruto` se preserva como observación identificable, no se
reconstruye sumando actividades.

## 14. Valores, unidades y precios

Las celdas numéricas se conservan como números, incluyendo negativos, cero y
la precisión publicada. Un cero explícito nunca es nulo. No se recalculan
tasas ni se convierten miles de millones a pesos.

La unidad se conserva literalmente cuando está disponible. Para `NIVEL`, la
evidencia de referencia es `Miles de millones de pesos`; las tasas mantienen
su unidad publicada o la metadata correspondiente, sin inferir una conversión.

También se conserva la evidencia de `Series encadenadas de volumen con año de
referencia 2015`, `precios constantes`, año de referencia, fuente y cualquier
tipo de medida disponible. No se mezclan precios constantes con corrientes.

Para texto inesperado (`-`, `--`, `...`, `N.D.`, `ND`, `NA`, símbolos, notas o
texto libre), el Extractor no inventa una conversión. Debe conservar
`raw_value`, registrar warning y excluir el registro numérico o detenerse si
la columna requiere un valor numérico según el contexto inspeccionado. La
política exacta de rechazo frente a preservación textual es una decisión
abierta porque el workbook real no contiene esos marcadores.

## 15. Datos faltantes

Una celda vacía en un encabezado no se interpreta: la inspección ya resolvió
merged cells. Una celda vacía en la matriz temporal no equivale a cero.

Como regla conservadora de extracción, una celda temporal vacía no produce un
registro con `value=0`; se registra como ausencia/valor nulo en las métricas y
con warning con coordenadas, sin inventar observación económica. Si la
implementación necesita transportar explícitamente esa ausencia, puede usar
un registro de diagnóstico fuera de `ExtractedGDPRecord[]`.

**Decisión abierta:** falta evidencia de varias publicaciones para distinguir
de forma universal dato no disponible, diseño de tabla y ausencia semántica.
Antes de fijar el contrato físico debe confirmarse si las celdas vacías se
omiten, se materializan como registros nulos o son error en determinados
bloques.

## 16. Duplicados y clave natural

La clave natural de extracción debe identificar una observación y su lugar en
la fuente:

```text
source_sha256 o source_file
+ source_sheet
+ table_id/table_region
+ series_type
+ aggregation_level
+ indicator
+ period
+ activity_code o concepto
```

`source_row` y `source_column` son evidencia de ubicación, no sustituyen la
identidad económica. La misma observación lógica en otra versión del archivo
no es un duplicado si cambia la fuente/hash.

Una clave repetida dentro de la misma inspección es error: no se elimina ni se
elige una fila arbitrariamente. El Transformer aplicará después la clave del
Data Contract (`fecha_id + actividad_id + indicador_id + fuente_id +
tipo_serie + estado_dato`) y sus claves de dimensión.

## 17. Trazabilidad

Cada registro debe permitir recorrer:

```text
DANE -> URL -> archivo -> SHA-256 -> hoja -> cuadro -> región
     -> indicador -> período -> fila -> columna -> valor
```

El Extractor debe conservar, como mínimo, `source_file`, `source_sha256`,
`source_sheet`, cuadro, región, indicador, agregación, serie, fila, columna,
período, código/concepto, unidad y valor crudo. La fecha de descarga, URL,
operación y fuente institucional provienen de `SourceManifest` cuando exista.

Los campos de auditoría no tienen que llegar al dataset final, pero no pueden
perderse entre Extractor y Transformer. El Transformer podrá proyectarlos a
metadata de lineage; el hecho final debe seguir siendo auditable hasta la
celda original.

## 18. Metadata, hash y versionado

`SourceManifest` es la fuente de verdad para `source`, `operation`, `url`,
`filename`, `download_timestamp`, `file_size_bytes` y `sha256`. El Extractor
los transporta sin reemplazarlos por datos inferidos del nombre de archivo.

La fecha de publicación, año de referencia, unidad, base y actualización se
conservan desde el workbook/Inspector cuando estén disponibles. El hash es el
SHA-256 de los bytes del archivo y debe ser de 64 caracteres hexadecimales.

La versión lógica de una ejecución se compone de hash del archivo, versión de
la inspección, configuración y versión del Extractor. No se usan timestamps ni
IDs aleatorios para identificar registros. Dos versiones de archivo pueden
producir observaciones coexistentes; no se sobrescriben silenciosamente.

**Decisión abierta:** el Data Contract define el hash y la preservación de
revisiones, pero no define un almacén físico de metadata intermedia ni el
campo/versionado exacto de `InspectionResult`. Esa política debe fijarse al
implementar el pipeline.

## 19. Orden, determinismo e idempotencia

El orden lógico obligatorio es:

```text
cuadro ascendente
 -> región/bloque en orden de inspección
 -> fila económica ascendente
 -> columna/período ascendente
```

Dentro de una fila se usa el orden de las columnas temporales entregado por el
Inspector. La salida no depende de hashes de mapas, timestamps, nombres
temporales ni orden accidental de descubrimiento.

Para el mismo XLSX, la misma inspección y la misma configuración, la salida
lógica, sus claves y su orden deben ser iguales. La metadata de ejecución
puede variar en timestamps, pero queda separada de los registros.

## 20. Error handling y fail-fast

Se reutiliza la terminología del Inspector y del Transformer:

| Severidad | Condiciones |
|---|---|
| `ERROR` | inspección inválida, workbook ilegible, hash incompatible, región inexistente, indicador desconocido, período imposible, columna o fila declarada ausente, estructura incompatible, duplicado o valor requerido ilegible |
| `WARNING` | celda vacía, valor no numérico aislado que puede auditarse, metadata opcional ausente, cambio no crítico de conteo |
| `INFO` | inicio/fin, tablas, regiones, períodos, registros procesados y cobertura |

No se crean códigos nuevos si puede reutilizarse `UNEXPECTED_STRUCTURE`,
`INVALID_PERIOD`, `UNKNOWN_STATUS`, `UNEXPECTED_INDICATOR` u otra validación
existente. Si la implementación necesita categorías específicas de extracción,
debe mapearlas explícitamente a la nomenclatura contractual.

Son bloqueantes: `inspection.is_valid == False`, cualquier región declarada
que no pueda localizarse, metadata controlada faltante o contradictoria,
indicador/serie/agregación fuera de catálogo, período inválido, duplicado o
imposibilidad de identificar la celda de un valor esperado. No se publica una
salida parcial como válida.

## 21. Métricas de extracción

`ExtractionMetadata` debe reportar al menos:

- tablas y regiones procesadas;
- registros extraídos y descartados;
- valores nulos/ausentes;
- duplicados;
- errores y warnings por categoría;
- períodos encontrados;
- cobertura por cuadro, serie, agregación e indicador.

Los conteos deben derivarse de la ejecución real y no ocultar descartes. Para
el workbook de referencia, la integración futura debe comprobar 6 cuadros y
18 regiones; no debe asumir un número fijo de registros porque depende de
filas y períodos publicados.

## 22. Salida para el Transformer

El Transformer recibe registros largos con evidencia publicada y metadata de
lineage. Es responsable de:

- normalizar nombres y tipos finales;
- convertir el período a `dim_fecha`;
- construir `dim_actividad`, sin expandir códigos sin una regla aprobada;
- construir `dim_indicador`, `dim_fuente` y claves;
- clasificar actividades y totales;
- construir `fact_pib`;
- validar integridad referencial y reglas del Data Contract;
- materializar Parquet/processed.

El Extractor no debe producir ya `fecha_id`, `actividad_id`, `indicador_id`,
`fuente_id` ni `valor` como sustituto del registro raw. Puede exponer un valor
numérico para conservar la celda publicada, pero no realizar normalización
analítica.

## 23. Relación con el modelo estrella

La correspondencia futura es:

| Registro extraído | Destino posterior |
|---|---|
| `year`, `quarter`, `period` | `dim_fecha` |
| código, nombre, nivel y total | `dim_actividad` |
| `indicator`, unidad y descripción | `dim_indicador` |
| manifest, URL, fecha y hash | `dim_fuente` |
| serie, estado y valor | `fact_pib` |

Esta tabla describe una proyección posterior, no una responsabilidad del
Extractor. El Data Contract sigue siendo la autoridad para nombres finales,
tipos, nulabilidad y claves del modelo estrella.

## 24. Testing futuro

No se crean tests en este cambio. La implementación deberá cubrir:

### Unit tests

- una `TableRegion` y sus coordenadas;
- extracción de períodos ya inspeccionados;
- actividades, códigos, rangos y conceptos;
- VAB, impuestos y PIB como totales;
- `NIVEL` y los tres indicadores de crecimiento;
- series original y ajustada;
- agregaciones 12, 25 y 61;
- cero, negativos, nulos y texto inesperado;
- estados sin sufijo, `p` y `pr`;
- clave natural y duplicados;
- trazabilidad hoja/fila/columna/hash.

### Integration test

Ejecutar contra `local_data/anex-ProduccionConstantes-IItrim2026.xlsx` cuando
esté disponible, usando el Inspector real, y esperar 6 cuadros, 18 regiones,
períodos coherentes, las seis combinaciones serie/agregación y registros
trazables. El fixture no debe agregarse al repositorio.

### Data quality tests

Comprobar que cada región genera cobertura, no hay duplicados, los períodos
son los inspeccionados, los valores numéricos se preservan, los códigos y
conceptos son identificables y ningún registro pierde su origen.

## 25. Criterios de aceptación

La futura implementación será aceptada si:

- rechaza una inspección inválida antes de extraer;
- consume metadata del Inspector sin redetectar estructura;
- procesa las 18 regiones de la publicación de referencia;
- produce registros largos con todos los campos obligatorios;
- conserva indicadores, series, agregaciones, períodos y estados;
- distingue actividades y totales sin crear dimensiones finales;
- conserva unidades, precios constantes, base 2015 y valores publicados;
- no convierte vacío en cero ni calcula tasas;
- detecta duplicados y reporta métricas completas;
- permite rastrear cada valor hasta hoja, fila, columna y hash;
- es idempotente y determinista;
- entrega una entrada compatible con el Transformer y el Data Contract.

## 26. Riesgos técnicos

- DANE puede cambiar títulos, merges, columnas, bloques o notas.
- Las coordenadas físicas de la publicación no son un contrato permanente.
- Una celda vacía puede ser estructural o representar ausencia de dato.
- `p` y `pr` podrían cambiar de alcance en futuras publicaciones.
- Los códigos CIIU pueden ser listas o rangos no expandibles automáticamente.
- La salida del Inspector actual separa `TableRegion` y `TableInspection`, lo
  que exige una relación estable entre ambos durante la implementación.
- El manifest actual puede no inferir el trimestre desde nombres como
  `IItrim2026`; los períodos analíticos deben provenir del workbook inspeccionado.
- Una revisión del archivo puede cambiar valores sin cambiar el período.

## 27. Decisiones abiertas

1. Definir la interfaz pública concreta: dataclasses/objetos tipados o
   DataFrame, manteniendo el esquema lógico de este documento.
2. Confirmar con más publicaciones el significado de celdas temporales vacías
   y la política física de omisión frente a registro nulo.
3. Definir cómo conservar metadata de ejecución y lineage fuera de los
   registros cuando el Transformer materialice Parquet.
4. Definir la versión exacta del `InspectionResult` usada para compatibilidad
   entre Inspector y Extractor.
5. Confirmar si aparecen nuevos indicadores, series, estados o niveles de
   agregación; ninguno debe aceptarse silenciosamente.
6. Definir el mecanismo físico de revisiones y consulta por SHA-256; el Data
   Contract solo exige no sobrescribir fuentes distintas.
7. Confirmar la unidad contractual de los indicadores de crecimiento cuando el
   workbook no la declare explícitamente.

## 28. Referencias contractuales

- [PIB Workbook Inspector](pib-workbook-inspector-spec.md)
- [Estructura real del XLSX DANE](../research/dane-pib-xlsx-real-structure.md)
- [PIB Data Contract / modelo de datos](pib-data-model.md)
- [PIB Transformer](pib-transformer-spec.md)
- [PIB XLSX structure research](../research/dane-pib-xlsx-structure.md)

No se encontró en el repositorio un archivo llamado
`docs/research/dane-pib-trimestral-source-strategy.md`. Tampoco se encontró un
archivo separado llamado `docs/architecture/pib-data-contract.md`; el
contrato equivalente vigente es `pib-data-model.md`. Esta especificación no
inventa el contenido de los documentos ausentes y utiliza los equivalentes
existentes.
