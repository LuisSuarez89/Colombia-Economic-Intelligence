# Especificación técnica del PIBWorkbookInspector

**Estado:** Especificación técnica; no implementada
**Fecha:** 2026-08-24
**Versión:** 1.0
**Alcance:** inspección estructural del XLSX trimestral del PIB del DANE

## 1. Propósito

`PIBWorkbookInspector` abre un workbook XLSX del PIB del DANE, identifica y
valida su estructura interna y devuelve una representación estructurada de esa
estructura, sin transformar todavía los datos económicos.

Debe responder, como mínimo:

- qué workbook se recibió;
- qué hojas contiene;
- qué cuadros contiene;
- qué serie y nivel de agregación representa cada cuadro;
- qué tablas contiene cada cuadro;
- qué indicador representa cada tabla;
- dónde están las columnas temporales;
- cómo se interpretan las celdas combinadas;
- qué período y estado representa cada columna;
- dónde están las filas de actividades y los totales;
- si la estructura es válida;
- qué warnings y errores estructurales existen.

La prioridad para interpretar el formato es la evidencia del XLSX real
documentada en [la investigación de estructura real](../research/dane-pib-xlsx-real-structure.md).
Las reglas de este documento que no sean una observación directa están
marcadas como **Decisión de diseño del Inspector**.

## 2. Responsabilidad y límites

### El Inspector sí hace

- inspecciona el workbook;
- identifica hojas, cuadros, series, agregaciones, tablas y encabezados;
- construye una representación lógica de períodos y filas;
- valida la estructura esperada;
- reporta resultados, warnings y errores estructurales.

### El Inspector no hace

- transforma valores económicos;
- calcula indicadores o tasas de crecimiento;
- convierte unidades;
- genera datasets finales;
- construye el modelo estrella;
- carga datos ni crea archivos para Power BI;
- descarga el XLSX;
- modifica el XLSX de entrada.

La separación de responsabilidades es:

```text
INSPECTOR   -> ¿Dónde y qué están los datos?
EXTRACTOR   -> Voy a leer los datos según la estructura conocida.
TRANSFORMER -> Voy a convertir registros al modelo de datos.
LOADER      -> Voy a almacenarlos.
POWER BI    -> Voy a analizarlos.
```

## 3. Interfaz pública

La interfaz conceptual mínima es:

```text
PIBWorkbookInspector.inspect(path) -> InspectionResult
```

### Entrada

| Campo | Tipo conceptual | Requerido | Regla |
|---|---|---:|---|
| `path` | Ruta a archivo | Sí | Debe apuntar a un XLSX legible |

No se agregan parámetros de configuración en esta etapa. La implementación
puede utilizar excepciones o resultados de validación para reportar un archivo
ilegible, pero debe preservar la información disponible sobre el fallo.

### Salida

La salida es un `InspectionResult` que describe estructura, metadatos,
períodos, filas y validaciones. No contiene la matriz de valores económicos
normalizada.

## 4. Modelo conceptual del resultado

```text
InspectionResult
|
|-- workbook: WorkbookMetadata
|-- sheets[]: SheetInspection
|-- tables[]: TableInspection
|-- periods[]: Period
|-- activities[]: ActivityRow
|-- validations[]: ValidationResult
`-- warnings[]: ValidationResult
```

La implementación no está obligada a usar estas clases literalmente, pero un
resultado válido debe exponer equivalentemente toda la información definida
en este documento.

## 5. WorkbookMetadata

`WorkbookMetadata` representa el workbook completo.

| Campo | Tipo conceptual | Descripción |
|---|---|---|
| `filename` | Texto o `null` | Nombre del archivo recibido |
| `sheet_count` | Entero o `null` | Número de hojas detectadas |
| `expected_sheet_count` | Entero | 7 para la estructura de referencia |
| `source` | Texto o `null` | Fuente identificada, por ejemplo `DANE` o `DANE, PIB_T` |
| `publication_date` | Fecha/texto o `null` | Fecha de actualización si está presente y es interpretable |
| `reference_year` | Entero o `null` | Año de referencia identificado en el workbook |
| `detected_series` | Colección o `null` | Familias de serie observadas |

Para el XLSX de referencia se observaron siete hojas, año de referencia 2015
y textos de fuente `DANE`/`PIB_T`. También se observó `Actualizado el 18 de
agosto de 2026`.

**Decisión de diseño del Inspector:** ningún metadato debe inventarse. Si no
puede determinarse confiablemente, su valor es `null` y puede emitirse un
warning. No se sustituyen valores desconocidos por valores del nombre del
archivo ni por valores esperados.

## 6. SheetInspection

`SheetInspection` describe una hoja y su clasificación estructural.

| Campo | Tipo conceptual | Descripción |
|---|---|---|
| `name` | Texto | Nombre literal de la hoja |
| `sheet_type` | `INDEX`, `CUADRO` o `UNKNOWN` | Tipo identificado |
| `cuadro_number` | Entero o `null` | Número 1 a 6 cuando aplica |
| `series` | `ORIGINAL`, `AJUSTADA` o `null` | Familia de serie |
| `aggregation_level` | 12, 25, 61 o `null` | Nivel declarado por encabezados |
| `expected_tables` | Entero | 3 para una hoja de cuadro |
| `detected_tables` | Colección | Tablas encontradas en la hoja |
| `header_structure` | Estructura o `null` | Encabezados CIIU y temporales |
| `validation_status` | Estado | Resultado de validación de la hoja |

La estructura real observada es:

| Hoja | Tipo | Serie | Agregación |
|---|---|---|---:|
| `Índice` | `INDEX` | `null` | `null` |
| `Cuadro 1` | `CUADRO` | `ORIGINAL` | 12 |
| `Cuadro 2` | `CUADRO` | `ORIGINAL` | 25 |
| `Cuadro 3` | `CUADRO` | `ORIGINAL` | 61 |
| `Cuadro 4` | `CUADRO` | `AJUSTADA` | 12 |
| `Cuadro 5` | `CUADRO` | `AJUSTADA` | 25 |
| `Cuadro 6` | `CUADRO` | `AJUSTADA` | 61 |

La hoja `Índice` describe los seis cuadros y sus agrupaciones. Una hoja que
no pueda clasificarse es `UNKNOWN`; su tratamiento y severidad se determinan
por las reglas de validación de este documento.

## 7. Familias de serie

Los valores conceptuales permitidos son:

| Valor | Texto observado |
|---|---|
| `ORIGINAL` | `Datos originales` |
| `AJUSTADA` | `Datos ajustados por efecto estacional y calendario` |

`AJUSTADA` representa exclusivamente la etiqueta observada completa:
**Ajustada por efecto estacional y calendario**. No se inventan otros tipos de
serie.

**Decisión de diseño del Inspector:** la familia se identifica mediante el
título o metadato estructural del cuadro, con el número de cuadro como
consistencia secundaria. No se infiere a partir de valores numéricos ni del
nombre del archivo.

## 8. Nivel de agregación

```text
aggregation_level ∈ {12, 25, 61}
```

El nivel se identifica mediante los encabezados CIIU del cuadro:

- cuadros 1 y 4: `Secciones CIIU Rev. 4 A.C. / 12 agrupaciones`;
- cuadros 2 y 5: `Secciones y divisiones CIIU Rev. 4 A.C. / 25 agrupaciones`;
- cuadros 3 y 6: `Divisiones CIIU Rev. 4 A.C. / 61 agrupaciones`.

El nivel **no** se determina contando filas. El conteo de filas puede ser una
validación secundaria, pero no el mecanismo principal de identificación,
porque cada nivel contiene filas adicionales para agregados y totales.

## 9. TableInspection

Cada cuadro debe contener exactamente tres tablas estructurales.

| Campo | Tipo conceptual | Descripción |
|---|---|---|
| `table_id` | Texto/entero | Identificador estable dentro del cuadro |
| `indicator` | Indicador controlado | Indicador del bloque |
| `title` | Texto | Título visible del bloque |
| `header_row` | Entero | Fila del encabezado principal |
| `period_row` | Entero | Fila de trimestres |
| `data_start_row` | Entero | Primera fila económica |
| `data_end_row` | Entero | Última fila económica |
| `first_period_column` | Columna | Primera columna temporal |
| `last_period_column` | Columna | Última columna temporal |
| `period_count` | Entero | Cantidad de períodos válidos del bloque |
| `activity_row_count` | Entero | Cantidad de filas de conceptos/actividades |
| `validation_status` | Estado | Resultado de la tabla |

El mapa físico observado para el archivo de referencia es:

| Cuadro | Tabla | Indicador | Encabezado | Períodos | Datos | Filas económicas |
|---|---:|---|---:|---:|---:|---:|
| `Cuadro 1` | 1 | `NIVEL` | 12 | 13 | 15-29 | 15 |
| `Cuadro 1` | 2 | `CRECIMIENTO_ANUAL` | 45 | 46 | 48-62 | 15 |
| `Cuadro 1` | 3 | `CRECIMIENTO_ANO_CORRIDO` | 78 | 79 | 81-95 | 15 |
| `Cuadro 2` | 1 | `NIVEL` | 12 | 13 | 15-54 | 40 |
| `Cuadro 2` | 2 | `CRECIMIENTO_ANUAL` | 70 | 71 | 73-112 | 40 |
| `Cuadro 2` | 3 | `CRECIMIENTO_ANO_CORRIDO` | 128 | 129 | 131-170 | 40 |
| `Cuadro 3` | 1 | `NIVEL` | 12 | 13 | 15-103 | 89 |
| `Cuadro 3` | 2 | `CRECIMIENTO_ANUAL` | 119 | 120 | 122-210 | 89 |
| `Cuadro 3` | 3 | `CRECIMIENTO_ANO_CORRIDO` | 226 | 227 | 229-317 | 89 |
| `Cuadro 4` | 1 | `NIVEL` | 12 | 13 | 15-29 | 15 |
| `Cuadro 4` | 2 | `CRECIMIENTO_TRIMESTRAL` | 45 | 46 | 48-62 | 15 |
| `Cuadro 4` | 3 | `CRECIMIENTO_ANO_CORRIDO` | 78 | 79 | 81-95 | 15 |
| `Cuadro 5` | 1 | `NIVEL` | 12 | 13 | 15-54 | 40 |
| `Cuadro 5` | 2 | `CRECIMIENTO_TRIMESTRAL` | 70 | 71 | 73-112 | 40 |
| `Cuadro 5` | 3 | `CRECIMIENTO_ANO_CORRIDO` | 128 | 129 | 131-170 | 40 |
| `Cuadro 6` | 1 | `NIVEL` | 12 | 13 | 15-103 | 89 |
| `Cuadro 6` | 2 | `CRECIMIENTO_TRIMESTRAL` | 119 | 120 | 122-210 | 89 |
| `Cuadro 6` | 3 | `CRECIMIENTO_ANO_CORRIDO` | 226 | 227 | 229-317 | 89 |

Los números anteriores son evidencia de una publicación concreta y sirven
para validar una inspección; no autorizan a usar filas fijas como única regla
de detección.

## 10. Indicadores soportados

| Serie | Indicadores esperados | Título visible |
|---|---|---|
| `ORIGINAL` | `NIVEL` | `Miles de millones de pesos` dentro del bloque de nivel |
| `ORIGINAL` | `CRECIMIENTO_ANUAL` | `Tasa de crecimiento anual` |
| `ORIGINAL` | `CRECIMIENTO_ANO_CORRIDO` | `Tasa de crecimiento año corrido` |
| `AJUSTADA` | `NIVEL` | `Miles de millones de pesos` dentro del bloque de nivel |
| `AJUSTADA` | `CRECIMIENTO_TRIMESTRAL` | `Tasa de crecimiento trimestral` |
| `AJUSTADA` | `CRECIMIENTO_ANO_CORRIDO` | `Tasa de crecimiento año corrido` |

El indicador se identifica por el contexto estructural de la tabla: posición
del bloque, título, encabezado repetido y metadatos asociados. No se usa como
mecanismo principal una búsqueda global de texto, la unidad ni una aparición
aislada de una frase.

`Miles de millones de pesos` no implica automáticamente `NIVEL`: es una
unidad/metadato de publicación y debe interpretarse dentro del bloque de
nivel. La unidad y el indicador son dimensiones conceptualmente distintas.

## 11. Period

`Period` representa una columna temporal lógica.

| Campo | Tipo conceptual | Descripción |
|---|---|---|
| `year` | Entero | Año numérico, por ejemplo 2026 |
| `quarter` | 1, 2, 3 o 4 | Trimestre derivado de `I`, `II`, `III`, `IV` |
| `status` | `null`, `p` o `pr` | Código publicado del encabezado anual |
| `column` | Columna | Coordenada de la columna temporal |
| `label` | Texto | Etiqueta lógica, por ejemplo `2026-II` |

Ejemplo conceptual:

```text
year    = 2026
quarter = 2
status  = "pr"
column  = CK
label   = "2026-II"
```

El `label` normalizado no reemplaza la evidencia original: la implementación
debe conservar también el encabezado anual y el trimestre observados para
trazabilidad.

## 12. Celdas combinadas y encabezados temporales

El XLSX real utiliza merged cells para representar los años. El año aparece
en una fila superior y los trimestres romanos en la fila inmediatamente
inferior. La celda con el valor del año puede cubrir varias columnas.

Ejemplos observados incluyen:

```text
Cuadro 3 / Cuadro 6:
E12:H12  -> 2005
I12:L12  -> 2006
CC12:CF12 -> 2024p
CG12:CJ12 -> 2025pr
CK12:CL12 -> 2026pr

Fila inferior:
CK13 -> I
CL13 -> II
```

En cuadros cuya matriz temporal comienza en `D`, el último grupo equivalente
se observa como `CJ12:CK12` para `2026pr`, con `CJ13 -> I` y `CK13 -> II`.
Las coordenadas exactas varían por las columnas descriptoras de cada cuadro;
la regla lógica es la misma.

La representación lógica requerida es:

```text
CJ -> 2026pr
CK -> 2026pr

CJ -> 2026-I-pr
CK -> 2026-II-pr
```

**Decisión de diseño del Inspector:** debe resolver merged ranges y expandir
su valor a cada columna cubierta al construir períodos. Una celda vacía
dentro de un merged range no significa ausencia de año. La expansión existe
solo en la representación lógica; el workbook de entrada nunca se modifica.

El Inspector debe ubicar las filas de año y trimestre por estructura de la
tabla. No debe depender únicamente de que estén en las filas 12 y 13 en
futuras publicaciones.

## 13. Estados `p` y `pr`

```text
status ∈ {null, "p", "pr"}
```

El estado procede del sufijo del encabezado anual y se propaga a los
trimestres cubiertos por ese año:

```text
2025pr
 I
 II
 III
 IV

-> cada período tiene status = "pr"
```

Para el archivo observado:

- `2024p` + `I`, `II`, `III`, `IV` -> `p`;
- `2025pr` + `I`, `II`, `III`, `IV` -> `pr`;
- `2026pr` + `I`, `II` -> `pr`.

Los años anteriores pueden no contener estado y entonces el valor puede ser
`null`. El Inspector conserva el código `p` o `pr`; no lo convierte en
`provisional` ni `preliminar`. Las notas observadas `pprovisional` y
`prpreliminar` sirven como evidencia contextual, no como reemplazo del código.

## 14. Horizontes temporales

Los rangos observados dependen del indicador:

| Indicador | Rango esperado en el XLSX de referencia |
|---|---|
| `NIVEL` | 2005-I -> 2026-II |
| `CRECIMIENTO_ANUAL` | 2006-I -> 2026-II |
| `CRECIMIENTO_ANO_CORRIDO` | 2006-I -> 2026-II |
| `CRECIMIENTO_TRIMESTRAL` | 2005-II -> 2026-II |

**Decisión de diseño del Inspector:** la validación se basa en el rango
esperado por indicador, no únicamente en un número absoluto de columnas. No
debe exigirse que todos los indicadores tengan el mismo período inicial.

## 15. ActivityRow

`ActivityRow` representa una fila económica identificada dentro de una tabla.

| Campo | Tipo conceptual | Descripción |
|---|---|---|
| `row_number` | Entero | Fila física del XLSX |
| `classification_level` | Texto | Nivel CIIU aplicable a la columna |
| `classification_code` | Texto o `null` | Código textual publicado |
| `concept` | Texto | Concepto publicado |
| `is_total` | Booleano | Si es VAB, impuestos o PIB |
| `total_type` | `null` o controlado | Tipo de agregado cuando aplica |

La clasificación se entiende jerárquicamente:

```text
nivel de agregación
  -> código de clasificación
    -> concepto
```

El XLSX contiene diferentes niveles CIIU. Se observaron, entre otros,
secciones `A`, `B`, `C`, códigos como `C01`, `C02`, `C03`, y códigos combinados
o rangos como `043, 044`, `045 - 047` y `001, 002, 004 - 008, 013`.
Los códigos se conservan como texto; esta especificación no expande rangos ni
diseña la dimensión definitiva de actividades.

## 16. Totales

Los siguientes registros se reconocen separadamente:

- `Valor agregado bruto`;
- `Impuestos menos subvenciones sobre los productos`;
- `Producto Interno Bruto`.

Conceptualmente:

```text
is_total = true
total_type = VAB | IMPUESTOS_MENOS_SUBVENCIONES | PIB
```

Estos registros no se tratan automáticamente como actividades económicas
ordinarias. La especificación identifica su ubicación y naturaleza, pero no
define todavía la dimensión final de actividades ni modifica el Data Contract.

## 17. ValidationResult

Cada validación produce conceptualmente:

| Campo | Tipo conceptual | Descripción |
|---|---|---|
| `code` | Texto controlado | Código de validación |
| `severity` | `INFO`, `WARNING`, `ERROR` | Severidad |
| `message` | Texto | Explicación legible |
| `expected` | Valor o `null` | Estructura esperada |
| `actual` | Valor o `null` | Estructura observada |

Códigos mínimos:

| Código | Uso |
|---|---|
| `EXPECTED_SHEET_COUNT` | Cantidad de hojas distinta de la esperada |
| `EXPECTED_TABLE_COUNT` | Cantidad de tablas distinta de tres por cuadro |
| `UNEXPECTED_INDICATOR` | Indicador desconocido o incompatible |
| `MISSING_TABLE` | Falta una tabla esperada |
| `INVALID_PERIOD` | Año/trimestre imposible o inconsistente |
| `UNKNOWN_STATUS` | Estado distinto de `null`, `p`, `pr` |
| `UNEXPECTED_STRUCTURE` | Estructura crítica no interpretable |

No se agregan códigos de error que no representen una condición estructural
accionable.

## 18. Validaciones obligatorias

### Workbook

- Deben detectarse siete hojas para la estructura de referencia.
- Debe registrarse si existen hojas ocultas o adicionales.
- El conteo observado debe compararse con `expected_sheet_count`.

### Índice y cuadros

- Debe existir una hoja `Índice` o una hoja identificable como índice.
- Deben identificarse seis cuadros.
- Deben estar presentes las combinaciones:
  `ORIGINAL x 12`, `ORIGINAL x 25`, `ORIGINAL x 61`, `AJUSTADA x 12`,
  `AJUSTADA x 25`, `AJUSTADA x 61`.

### Tablas e indicadores

- Cada cuadro debe contener tres tablas.
- Los cuadros originales deben exponer `NIVEL`, `CRECIMIENTO_ANUAL` y
  `CRECIMIENTO_ANO_CORRIDO`.
- Los cuadros ajustados deben exponer `NIVEL`, `CRECIMIENTO_TRIMESTRAL` y
  `CRECIMIENTO_ANO_CORRIDO`.

### Períodos

- Solo se aceptan trimestres `I`, `II`, `III`, `IV`.
- Deben resolverse años combinados y su propagación a columnas.
- Deben validarse rangos por indicador.
- El último año puede contener solo `I` y `II`.

### Estados

- Solo se aceptan `null`, `p` y `pr`.
- Un estado presente debe propagarse a las columnas trimestrales cubiertas.

### Filas

- Las filas identificadas como económicas deben tener concepto.
- VAB, impuestos y PIB deben poder separarse como totales.
- Los niveles 12/25/61 deben provenir de encabezados CIIU.

## 19. Severidad

### ERROR

Se reporta `ERROR` cuando el resultado no permite interpretar confiablemente
la estructura:

- falta un cuadro esperado;
- un cuadro no contiene exactamente tres tablas interpretables;
- hay un indicador desconocido o incompatible;
- existe un período imposible;
- el encabezado temporal no puede interpretarse;
- la combinación serie/agregación es incompatible;
- la estructura contradice el contrato estructural.

### WARNING

Se reporta `WARNING` cuando la estructura principal sigue siendo interpretable:

- falta un metadato no crítico;
- falta estado en un año donde no es obligatorio;
- cambia de forma no crítica la cantidad de filas;
- aparece un concepto inesperado pero legible;
- existen diferencias físicas explicables por formato o notas.

La implementación futura debe evitar fallar por diferencias menores que no
impidan identificar las tablas y sus períodos.

## 20. Orden obligatorio de detección

La inspección debe seguir esta jerarquía:

1. Workbook.
2. Sheets.
3. Cuadro.
4. Serie.
5. Agregación.
6. Tablas.
7. Indicadores.
8. Encabezados temporales.
9. Celdas combinadas.
10. Períodos.
11. Actividades y totales.
12. Validaciones.

Cada etapa debe utilizar el contexto resuelto por las etapas anteriores. No se
debe reconstruir el workbook mediante búsquedas globales independientes.

## 21. Reglas que la implementación no debe utilizar como mecanismo principal

- `Miles de millones de pesos` -> `NIVEL` sin contexto de tabla.
- Contar filas -> determinar 12/25/61.
- Buscar cualquier año mediante regex global.
- Buscar `p`/`pr` únicamente en celdas de datos.
- Asumir que cada año ocupa una sola columna.
- Interpretar una celda vacía de un merged range como ausencia de año.
- Asumir que todos los indicadores tienen el mismo horizonte temporal.
- Buscar indicadores en todo el workbook sin contexto de tabla.
- Usar filas absolutas fijas como único detector de bloques.
- Inferir serie o indicador a partir de valores numéricos.

## 22. Contrato de un InspectionResult válido

Un `InspectionResult` válido debe permitir que un futuro Extractor conozca,
sin redescubrir el workbook:

- qué tablas existen;
- dónde empieza y termina cada tabla;
- qué indicador representa;
- qué serie representa;
- qué nivel de agregación representa;
- qué columnas contienen períodos;
- qué período representa cada columna;
- qué estado tiene cada período;
- qué filas contienen actividades/conceptos;
- qué filas contienen totales;
- si la estructura es válida;
- qué warnings o errores deben considerarse.

El Extractor posterior no debe volver a buscar headers, merged cells ni
períodos por su cuenta.

## 23. Relación con Extractor y Transformer

```text
Inspector   -> descubre la estructura.
Extractor   -> extrae valores según esa estructura.
Transformer -> transforma registros al modelo estrella.
```

El Inspector no debe extraer valores económicos ni normalizar registros. El
Extractor consume su salida estructurada. El Transformer consume registros del
Extractor y aplica el modelo analítico definido por el Data Contract. Esta
separación evita duplicar detección de headers, períodos, estados e
indicadores.

## 24. Compatibilidad con el modelo de datos

La salida del Inspector prepara información para el modelo estrella existente,
sin implementarlo ni redefinirlo:

| Inspección | Uso posterior |
|---|---|
| `classification_code` y `concept` | Construcción posterior de actividad |
| `Period` | Dimensión de fecha/período |
| `series` | Campo de serie/familia en el modelo posterior |
| `indicator` | Indicador y unidad en el modelo posterior |
| `status` | Estado de publicación de la observación |
| `total_type` | Distinción posterior de agregados |

No se introducen dimensiones nuevas. El resultado del Inspector es una
descripción estructural, no un nuevo contrato de datos.

## 25. Futura implementación

La implementación posterior debe:

- usar `openpyxl` o la librería ya establecida por el proyecto;
- trabajar sobre una representación lógica de merged cells;
- mantener separadas inspección, extracción y transformación;
- producir resultados deterministas;
- ser testeable sin internet;
- no descargar datos;
- no depender de una conexión externa;
- no modificar el archivo de entrada;
- conservar coordenadas y etiquetas originales suficientes para diagnóstico.

Nada de lo anterior se implementa en este PR.

## 26. Escenarios de tests futuros

No se crean tests en este cambio. La futura suite deberá cubrir como mínimo:

1. XLSX real completo.
2. Falta de un cuadro.
3. Cuadro con una tabla faltante.
4. Indicador inesperado.
5. Encabezado de año combinado.
6. Año con estado `p`.
7. Año con estado `pr`.
8. Año sin estado.
9. Último año con solo `I` y `II`.
10. Horizontes temporales distintos.
11. Serie original.
12. Serie ajustada.
13. 12 agrupaciones.
14. 25 agrupaciones.
15. 61 agrupaciones.
16. Totales VAB, impuestos y PIB.
17. Estructura desconocida.

## 27. Criterios de aceptación

Una futura implementación será aceptada únicamente si:

- identifica correctamente los seis cuadros;
- identifica serie y agregación por estructura;
- identifica tres tablas por cuadro;
- identifica los indicadores compatibles con cada familia;
- interpreta merged cells;
- reconstruye períodos por columna;
- conserva `p`/`pr` como códigos;
- reconoce horizontes distintos por indicador;
- identifica filas de actividades y conceptos;
- separa VAB, impuestos y PIB como totales;
- genera validaciones con severidad y contexto;
- no depende de heurísticas globales;
- no extrae valores económicos durante la inspección;
- no transforma datos.

## 28. Limitaciones

Esta especificación se basa en la estructura observada en el archivo concreto
`anex-ProduccionConstantes-IItrim2026.xlsx`. Futuras publicaciones DANE
podrían cambiar filas, columnas, rangos temporales, textos, notas o estructura
secundaria.

Por tanto, las coordenadas y conteos de la investigación son evidencia de
referencia y regresión, no una afirmación universal. El Inspector debe validar
la estructura y fallar de forma controlada ante estructuras incompatibles o
ambiguas.

## 29. Evidencia y decisiones de diseño

### Evidencia observada en el XLSX

- siete hojas: `Índice` y `Cuadro 1` a `Cuadro 6`;
- seis combinaciones de serie y agregación;
- tres tablas verticales por cuadro;
- años en merged cells y trimestres en la fila inferior;
- estados `p` y `pr` unidos al encabezado anual;
- rangos temporales distintos por indicador;
- columnas CIIU jerárquicas;
- filas adicionales para VAB, impuestos y PIB;
- textos de fuente, año base 2015 y actualización.

### Decisiones de diseño del Inspector

- representar períodos con una columna lógica por trimestre;
- expandir merged ranges sin editar el workbook;
- devolver `null` para metadatos no demostrados;
- clasificar errores estructurales por severidad;
- entregar al Extractor la estructura completa para evitar redetección;
- usar posiciones físicas como evidencia y validación secundaria, no como única
  heurística.

Las decisiones anteriores no son afirmaciones adicionales sobre el DANE.

## 30. Diagrama final

```text
XLSX DANE
    |
    v
PIBWorkbookInspector
    |
    |-- WorkbookMetadata
    |
    |-- SheetInspection
    |
    |-- TableInspection
    |
    |-- Period
    |
    |-- ActivityRow
    |
    `-- ValidationResult
              |
              v
       InspectionResult
              |
              v
          Extractor
              |
              v
         Transformer
              |
              v
       Modelo estrella
              |
              v
           Power BI
```

## 31. Fuentes y relación documental

La fuente principal es [la investigación de estructura real del XLSX](../research/dane-pib-xlsx-real-structure.md),
que contiene la evidencia empírica del archivo `anex-ProduccionConstantes-IItrim2026.xlsx`.

Esta especificación se relaciona además con:

- [PIB Data Contract](pib-data-model.md), que define el modelo analítico y sus
  valores controlados;
- [PIB Transformer Technical Specification](pib-transformer-spec.md), que
  describe el consumo futuro de una estructura inspeccionada;
- la estrategia de fuente DANE, cuando esté disponible en el repositorio, para
  resolver el origen del archivo sin trasladar esa responsabilidad al
  Inspector;
- el resolver de fuentes existente, únicamente como frontera de descarga y
  manifest.

Este documento establece el contrato técnico del Inspector, pero no modifica
ninguno de esos documentos ni implementa el componente.