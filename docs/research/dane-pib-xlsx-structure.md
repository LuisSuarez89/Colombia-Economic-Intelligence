# Estructura del XLSX real del PIB trimestral DANE

## Alcance y método

Este documento registra una inspección de un único XLSX real y reciente del DANE. La inspección fue realizada localmente con `openpyxl`, sin transformar los datos, crear datasets ni modificar el resolver, el downloader o los tests.

Las afirmaciones se clasifican así:

- **Observado:** leído directamente de celdas, propiedades o estructura del libro.
- **Inferido:** interpretación técnica derivada de lo observado.
- **Pendiente:** aspecto que debe confirmarse antes de implementar el transformador.

## 1. Archivo inspeccionado

- **Fuente:** DANE, PIB nacional trimestral, enfoque producción, precios constantes.
- **URL final utilizada:** `https://www.dane.gov.co/files/operaciones/PIB/anex-ProduccionConstantes-IItrim2026.xlsx`
- **Nombre:** `anex-ProduccionConstantes-IItrim2026.xlsx`
- **Tamaño:** 1.140.426 bytes.
- **SHA-256:** `1ece527765811c8b412d308201e5b2a2ab814f08f6e1e9c22888fceefb91ff04`
- **Fecha/hora de descarga:** `2026-08-21T21:52:32.797286+00:00` (UTC).
- **Trimestre identificable:** el nombre contiene `IItrim2026`; las cabeceras del libro llegan hasta `2026pr`, trimestre `II`. El campo `trimestre` del manifest actual quedó vacío porque su patrón solo reconoce formatos como `2026-2`.
- **Artefacto local:** se conservó fuera del repositorio, en un directorio temporal del sistema. No se agregó a Git.

## 2. Hojas encontradas

El libro contiene 7 hojas visibles, sin hojas ocultas observadas:

| Hoja | Dimensión reportada | Uso observado |
|---|---:|---|
| `Índice` | 16 x 13 | Portada/índice. Identifica los seis cuadros, sus agrupaciones CIIU y la separación entre datos originales y ajustados. |
| `Cuadro 1` | 175 x 93 | Datos originales; 12 agrupaciones, secciones CIIU Rev. 4 A.C. |
| `Cuadro 2` | 175 x 90 | Datos originales; 25 agrupaciones, con secciones y divisiones CIIU Rev. 4 A.C. |
| `Cuadro 3` | 322 x 90 | Datos originales; 61 agrupaciones, divisiones CIIU Rev. 4 A.C. |
| `Cuadro 4` | 100 x 89 | Datos ajustados por efecto estacional y calendario; 12 agrupaciones. |
| `Cuadro 5` | 175 x 90 | Datos ajustados por efecto estacional y calendario; 25 agrupaciones. |
| `Cuadro 6` | 322 x 90 | Datos ajustados por efecto estacional y calendario; 61 agrupaciones. |

Las dimensiones anteriores son las reportadas por Excel/openpyxl y pueden incluir filas o columnas formateadas. Las filas con contenido efectivo se describen más adelante.

La hoja `Índice` contiene, entre otros textos, `Producto Interno Bruto desde el enfoque de la producción` y `Series encadenadas de volumen con año de referencia 2015`. Sus celdas combinadas principales son `A1:J2`, `A3:J4` y `A5:J7`.

## 3. Hoja(s) de datos

Los cuadros 1 a 6 contienen datos. No son seis series independientes de actividad económica: forman dos familias de presentación:

- **Cuadros 1 a 3:** datos originales.
- **Cuadros 4 a 6:** datos ajustados por efecto estacional y calendario.

Cada familia ofrece tres niveles de agregación: 12, 25 y 61 agrupaciones.

En los seis cuadros se observan tres bloques verticales por hoja:

1. valores en `Miles de millones de pesos`;
2. tasa de crecimiento anual, o tasa de crecimiento trimestral en los cuadros ajustados;
3. tasa de crecimiento año corrido.

Los títulos de bloque y notas se repiten. Las filas exactas de inicio de los bloques de datos son:

| Hojas | Valores | Segunda medida | Tercera medida |
|---|---:|---:|---:|
| `Cuadro 1`, `Cuadro 4` | 15 | 48 | 81 |
| `Cuadro 2`, `Cuadro 5` | 15 | 73 | 131 |
| `Cuadro 3`, `Cuadro 6` | 15 | 122 | 229 |

Las filas 12-13 son cabeceras del primer bloque. Cada bloque posterior tiene sus propias cabeceras, normalmente en dos filas y con celdas combinadas. La fila inmediatamente anterior al primer bloque de datos está vacía en los cuadros observados.

## 4. Estructura de encabezados

En los cuadros de 12 agrupaciones, las columnas descriptoras del primer bloque son:

- `A`: `Clasificación Cuentas Nacionales`.
- `B`: código o agrupación CIIU.
- `C`: `Concepto`.
- Desde `D`: períodos.

En los cuadros de 25 y 61 agrupaciones, las columnas descriptoras son:

- `A`: `Clasificación Cuentas Nacionales`.
- `B`: secciones o agrupaciones CIIU.
- `C`: segundo nivel CIIU o código de actividad, según el cuadro.
- `D`: `Concepto`.
- Desde `E`: períodos.

Las tablas usan celdas combinadas. Por ejemplo, en `Cuadro 1` se observan combinaciones en las cabeceras de año y en los bloques de datos; en el total del libro hay numerosas combinaciones por hoja. El transformador futuro no debe asumir que una celda vacía de una cabecera repetida equivale a ausencia de período.

La primera tabla de valores tiene los títulos observados en las filas 7-10:

- `Series encadenadas de volumen con año de referencia 2015`.
- `Datos originales` o `Datos ajustados por efecto estacional y calendario`.
- `Miles de millones de pesos`.
- `2005 - 2026pr segundo trimestre`.

## 5. Estructura temporal

Los períodos están organizados **en columnas**, no en filas. La cabecera usa dos niveles:

- fila superior: año;
- fila inferior: trimestre romano.

Ejemplo observado en `Cuadro 3` y `Cuadro 6`:

- `E12 = 2005`, `E13 = I`, `F13 = II`, `G13 = III`, `H13 = IV`;
- `I12 = 2006`, `I13 = I`;
- ...;
- `CC12 = 2024p`;
- `CG12 = 2025pr`;
- `CK12 = 2026pr`, `CK13 = I`, `CL13 = II`.

En los cuadros 1 y 4 los períodos comienzan en la columna `D`; en los cuadros 2, 3, 5 y 6 comienzan en `E`. La última columna temporal observada es `CK`/`CL`, correspondiente a `2026pr` I/II, según la hoja.

**Observado:** no se encontraron columnas separadas para años anuales, acumulados o comparaciones interanuales. Sí existen bloques de indicadores llamados tasa de crecimiento anual, tasa de crecimiento trimestral y tasa de crecimiento año corrido.

**Inferido:** un registro normalizado necesitará conservar el bloque o indicador de origen para no confundir un valor de nivel con una tasa.

**Pendiente:** confirmar con la metodología si la tasa de crecimiento año corrido se calcula sobre los períodos disponibles y si la semántica de los bloques es idéntica en todas las actualizaciones.

## 6. Actividades económicas

Los cuadros contienen códigos y nombres en columnas separadas. Se observó, entre otros:

- `A`, `B`, `C`, `D + E` y otras agrupaciones de secciones;
- códigos como `C01`, `003`, `009 - 012` y `001, 002, 004 - 008, 013`;
- conceptos extensos en español, por ejemplo `Agricultura, ganadería, caza, silvicultura y pesca`;
- filas de agregación `Valor agregado bruto`, `Impuestos menos subvenciones sobre los productos` y `Producto Interno Bruto`.

La evidencia dentro del propio archivo identifica explícitamente:

- `Secciones CIIU Rev. 4 A.C. 12 agrupaciones`;
- `Secciones y divisiones CIIU Rev. 4 A.C. 25 agrupaciones`;
- `Divisiones CIIU Rev. 4 A.C. 61 agrupaciones`.

Por tanto, la pertenencia a CIIU Rev. 4 A.C. no es una suposición externa: está escrita en las cabeceras del XLSX. El nivel de agregación cambia según el cuadro. El PIB total aparece en filas con código `B.1b` y concepto `Producto Interno Bruto`; el valor agregado bruto aparece también con `B.1b` en los bloques observados.

**Pendiente:** definir si el dataset futuro conservará tanto las filas de actividad como las filas macroeconómicas agregadas, o si las separará mediante un tipo de entidad.

## 7. Medidas y series

Se observaron por separado las siguientes dimensiones:

- **Nivel:** `Miles de millones de pesos`.
- **Base conceptual:** `Series encadenadas de volumen con año de referencia 2015`.
- **Ajuste:** datos originales frente a datos ajustados por efecto estacional y calendario.
- **Crecimiento:** tasa de crecimiento anual en cuadros originales; tasa de crecimiento trimestral en cuadros ajustados; tasa de crecimiento año corrido en ambas familias.

No se observó una hoja separada de índices dentro de las siete hojas. La palabra `Índice` aparece en la portada y en títulos de columnas superiores de los cuadros, por lo que debe inspeccionarse la estructura completa de cada bloque antes de decidir si constituye una medida independiente o una etiqueta de presentación.

**Inferido:** `indicador` y `tipo_serie` deben ser dimensiones distintas. Por ejemplo, `nivel` no debe mezclarse con `tasa_crecimiento_anual`, y `original` no debe mezclarse con `ajustada_estacionalmente`.

**Pendiente:** verificar en las siguientes actualizaciones si aparecen índices explícitos, contribuciones u otras medidas que no estén presentes en este archivo.

## 8. Estados de publicación

Las cabeceras contienen los marcadores:

- `2024p`;
- `2025pr`;
- `2026pr`.

Al final de cada bloque se observan notas literales, por ejemplo en `Cuadro 1` filas 32-33 y en `Cuadro 3` filas 106-107:

- `prpreliminar`;
- `pprovisional`.

**Observado:** el propio archivo concatena el marcador con la descripción, sin espacio. La evidencia vincula `pr` con `preliminar` y `p` con `provisional`.

**Inferido:** el transformador futuro debería extraer el estado desde la cabecera y normalizarlo a valores controlados, conservando también el texto original de la cabecera para trazabilidad.

**Pendiente:** confirmar si el orden de los marcadores y su aplicación puede cambiar en una publicación futura o en otras tablas DANE.

## 9. Valores nulos y especiales

En la inspección con `openpyxl`:

- no se encontraron guiones `-`, `--`, `...`, `N.D.`, `ND`, `NA`, `no disponible` ni `no aplica` como valores de celda;
- se observaron celdas vacías (`None`), especialmente en columnas descriptoras, cabeceras multinivel, celdas combinadas y zonas sin dato;
- no se observaron textos que describan faltantes o datos no aplicables;
- se observaron dos ceros explícitos: `AB240` y `CB240` en `Cuadro 3` y los mismos dos identificadores en `Cuadro 6`. Corresponden a la actividad código `022`, `Actividades de apoyo para otras actividades de explotación de minas y canteras`, en el bloque de tasa de crecimiento año corrido. El cero debe conservarse como cero, no convertirse en nulo.

**Pendiente:** confirmar con más publicaciones si una celda vacía significa siempre dato no disponible, estructura de la tabla o combinación de celdas. No debe inferirse una semántica de nulo solo por el valor vacío.

## 10. Metadatos y notas relevantes

Las notas repetidas al final de los bloques contienen:

- `Fuente: DANE, PIB_T`;
- `prpreliminar`;
- `pprovisional`;
- `Actualizado el 18 de agosto de 2026`.

El año de referencia 2015 y la naturaleza de series encadenadas de volumen aparecen en la fila 7 de cada cuadro y en la hoja `Índice`. Las unidades del bloque de niveles aparecen como `Miles de millones de pesos`.

La distinción entre datos originales y ajustados por efecto estacional y calendario aparece explícitamente en la fila 8 de cada familia. No se encontraron en este archivo notas extensas de metodología, revisiones o cambios metodológicos; la hoja `Índice` funciona como navegación hacia los cuadros.

## 11. Propuesta de modelo analítico

La siguiente estructura es una propuesta **inferida**, basada en la separación observada de períodos, actividades, bloques de medidas y estados:

| Campo | Procedencia | Tratamiento propuesto |
|---|---|---|
| `periodo_original` | Cabeceras de año y trimestre | Conservar literalmente, por ejemplo año `2026pr` y trimestre `II`. |
| `periodo` | Derivado | Normalizar solo después de definir reglas para `p`/`pr`; no convertir durante esta investigación. |
| `actividad_codigo` | Columnas B/C o A/B/C según cuadro | Conservar el código textual original, incluidos rangos y combinaciones. |
| `actividad_nombre` | Columna `Concepto` o equivalente | Conservar el texto original. |
| `nivel_agregacion` | Cabecera del cuadro | Valores derivados como 12, 25 o 61 agrupaciones. |
| `indicador` | Título del bloque/fila | Separar nivel, tasa anual, tasa trimestral y tasa año corrido. |
| `valor` | Celdas numéricas | Convertir a numérico validando primero el bloque de origen. |
| `unidad` | Título del bloque | Conservar `Miles de millones de pesos` para niveles; definir unidad explícita para tasas. |
| `tipo_serie` | Cabeceras | Distinguir series encadenadas de volumen y otros tipos si aparecen. |
| `ajuste_estacional` | Familia de cuadro | Distinguir original de ajustada por efecto estacional y calendario. |
| `estado_dato` | Cabecera `p`/`pr` y notas | Normalizar a estados controlados, conservando el marcador original. |
| `fuente` | Nota `Fuente: DANE, PIB_T` | Conservar para trazabilidad. |
| `fecha_actualizacion` | Nota final del bloque | Parsear como metadato de publicación, no como período. |
| `archivo_nombre` | Descarga | Conservar. |
| `archivo_sha256` | Manifest | Conservar como versión del insumo. |
| `hoja_origen` y `fila_origen` | Derivados de ingestión | Conservar para auditoría y diagnóstico de cambios estructurales. |

No se recomienda guardar las filas de portada, títulos, notas o cabeceras como observaciones económicas. Sí se recomienda conservar sus metadatos relevantes fuera de la tabla de hechos.

## 12. Reglas de transformación futuras

Estas reglas son propuestas, no implementadas:

1. Seleccionar solo las hojas `Cuadro 1` a `Cuadro 6` y clasificar cada una por original/ajustada, nivel de agrupación e indicador.
2. Detectar cada bloque vertical por sus títulos, en lugar de depender únicamente de números de fila fijos.
3. Leer las dos filas de cabecera temporal y propagar el año de la primera columna del grupo de cuatro trimestres.
4. Conservar `I`, `II`, `III`, `IV` como período original y normalizarlos en un campo derivado separado.
5. Separar los marcadores `p` y `pr` del año y asignar el estado según las notas del propio archivo.
6. No convertir celdas vacías de descriptoras en datos; decidir la semántica de vacíos solo dentro del área temporal de una fila de actividad.
7. Convertir únicamente celdas numéricas de la matriz de valores/tasas; conservar ceros como valores válidos.
8. Separar filas de actividades, subtotales y agregados macroeconómicos mediante sus códigos y conceptos.
9. Conservar códigos textuales tal como aparecen, sin expandir rangos CIIU durante la primera transformación.
10. Guardar fuente, fecha de actualización, hoja, fila, nombre de archivo y SHA-256 para trazabilidad.

## 13. Validaciones futuras

Antes de aceptar una nueva publicación deberían comprobarse, como mínimo:

- existencia de las siete hojas esperadas y detección de hojas nuevas o faltantes;
- presencia de las seis hojas de cuadros y de las familias original/ajustada;
- presencia de los tres niveles de agrupación 12, 25 y 61;
- existencia de las cabeceras temporales y de los períodos esperados;
- continuidad de los trimestres y detección de cambios en la última fecha;
- existencia de una fila `Producto Interno Bruto` y una fila `Valor agregado bruto` por bloque;
- códigos y conceptos no vacíos en las filas de actividad;
- ausencia de duplicados por hoja, bloque, actividad, indicador y período;
- tipos numéricos en las celdas de valor, con ceros permitidos;
- estados de publicación dentro de un catálogo controlado;
- unidad y año de referencia consistentes;
- actualización y SHA-256 registrados;
- detección de cambios en filas de cabecera, celdas combinadas y posiciones de notas.

Los conteos esperados de actividades no deben fijarse todavía solo a partir de `max_row`, porque hay filas de subtotales, notas y zonas formateadas. Primero debe definirse la taxonomía de filas por bloque.

## 14. Riesgos y ambigüedades

- El archivo actual representa una publicación puntual; la estructura puede cambiar en futuras actualizaciones.
- `p` y `pr` están pegados al año (`2024p`, `2025pr`) y a sus notas (`pprovisional`, `prpreliminar`); el parser debe evitar confundirlos con parte del año.
- Los cuadros ajustados no deben combinarse con los originales como si fueran la misma serie.
- Los tres indicadores se organizan verticalmente y usan cabeceras repetidas; una lectura plana de la hoja puede mezclar niveles y tasas.
- Las celdas combinadas hacen que muchas celdas vacías sean estructurales.
- Los códigos de actividad pueden ser simples, rangos o listas de códigos; no deben normalizarse de forma destructiva.
- El nombre del archivo usa `IItrim2026`, mientras que el helper de trimestre del manifest no reconoce ese formato. Esto es una observación del flujo existente, no una modificación realizada en esta tarea.
- No se inspeccionaron múltiples publicaciones, por lo que no se puede afirmar estabilidad histórica de nombres, filas o notas.

## 15. Conclusión

El XLSX real contiene seis cuadros de datos organizados en dos familias: originales y ajustados por estacionalidad/calendario, cada una con 12, 25 y 61 agrupaciones CIIU Rev. 4 A.C. Las observaciones económicas están en matrices anchas: actividades en filas, trimestres en columnas y dos niveles de cabecera temporal. Cada hoja contiene niveles y tasas en bloques verticales separados.

La futura transformación debe modelar por separado período, actividad, indicador, ajuste, estado y trazabilidad del archivo. Debe basarse en detección de títulos y cabeceras, conservar el texto original y validar cambios estructurales. No se implementó ningún transformador ni se creó dataset en esta investigación.
