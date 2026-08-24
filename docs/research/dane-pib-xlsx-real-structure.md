# Estructura real del XLSX del PIB trimestral DANE

## Alcance y método

Este documento es una investigación estructural del archivo real
`anex-ProduccionConstantes-IItrim2026.xlsx`. La evidencia se obtuvo mediante
inspección programática con `openpyxl` del XLSX, sin extraer observaciones para
un dataset, sin transformar valores y sin modificar el Inspector.

Las afirmaciones se clasifican de la siguiente forma:

- **Observado:** está presente en hojas, celdas, rangos, títulos o propiedades
  del XLSX.
- **Inferido:** interpretación técnica razonable de evidencia observada.
- **No demostrado:** no debe convertirse en una regla del Inspector a partir
  de este archivo.

La prioridad de interpretación es: XLSX real, evidencia observada,
documentación del proyecto e inferencia.

## 1. Resumen ejecutivo

El workbook contiene la publicación del **Producto Interno Bruto desde el
enfoque de la producción**, en **series encadenadas de volumen con año de
referencia 2015**, para el período que termina en el segundo trimestre de
2026. Tiene siete hojas: una hoja `Índice` y seis hojas de cuadros.

Los seis cuadros son dos familias de serie, cada una con tres niveles de
agregación: datos originales en 12, 25 y 61 agrupaciones, y datos ajustados por
efecto estacional y calendario en los mismos tres niveles. Cada cuadro está
organizado verticalmente en tres tablas consecutivas. Las tablas contienen
niveles o tasas de crecimiento, mientras que sus columnas contienen años y
trimestres.

La estructura no es plana: una misma palabra puede aparecer en una portada,
en un metadato o en una tabla. Además, la unidad `Miles de millones de pesos`
identifica una unidad de publicación, no por sí sola el indicador. Por ello,
**el Inspector debe interpretar la estructura del workbook, no inferir
indicadores únicamente mediante búsqueda global de texto**.

## 2. Fuente analizada

| Propiedad | Evidencia observada |
|---|---|
| Archivo | `anex-ProduccionConstantes-IItrim2026.xlsx` |
| Naturaleza | Publicación DANE del PIB nacional trimestral, enfoque de producción, precios constantes |
| Operación | `PRODUCTO INTERNO BRUTO TRIMESTRAL (PIB_T)` |
| Período de referencia | 2005-I a 2026-II, según el indicador |
| Fecha de actualización | `Actualizado el 18 de agosto de 2026` |
| Formato | XLSX |
| Enfoque | Producción |
| Serie | Series encadenadas de volumen |
| Año de referencia | 2015 |
| Último período publicado | Segundo trimestre de 2026, encabezado `2026pr` y trimestre `II` |

La hoja `Índice` muestra `PRODUCTO INTERNO BRUTO TRIMESTRAL (PIB_T)`,
`Producto Interno Bruto desde el enfoque de la producción` y `Series
encadenadas de volumen con año de referencia 2015`. Las tablas muestran además
la fuente `Fuente: DANE, PIB_T`.

## 3. Estructura general del workbook

Se observaron siete hojas visibles, en este orden:

| Hoja | Propósito | Serie | Agregación |
|---|---|---|---|
| `Índice` | Índice de la publicación y descripción de los cuadros | No aplica | No aplica |
| `Cuadro 1` | Datos por secciones CIIU | Original | 12 agrupaciones |
| `Cuadro 2` | Datos por secciones y divisiones CIIU | Original | 25 agrupaciones |
| `Cuadro 3` | Datos por divisiones CIIU | Original | 61 agrupaciones |
| `Cuadro 4` | Datos por secciones CIIU | Ajustada por efecto estacional y calendario | 12 agrupaciones |
| `Cuadro 5` | Datos por secciones y divisiones CIIU | Ajustada por efecto estacional y calendario | 25 agrupaciones |
| `Cuadro 6` | Datos por divisiones CIIU | Ajustada por efecto estacional y calendario | 61 agrupaciones |

Dimensiones reportadas por XLSX/openpyxl:

| Hoja | Filas | Columnas | Celdas combinadas observadas |
|---|---:|---:|---:|
| `Índice` | 16 | 13 | 3 |
| `Cuadro 1` | 175 | 93 | 79 |
| `Cuadro 2` | 175 | 90 | 82 |
| `Cuadro 3` | 322 | 90 | 82 |
| `Cuadro 4` | 100 | 89 | 79 |
| `Cuadro 5` | 175 | 90 | 82 |
| `Cuadro 6` | 322 | 90 | 81 |

Las dimensiones físicas pueden incluir formato, notas y filas fuera del área
económica. No son conteos de actividades.

## 4. Las seis combinaciones estructurales

Las seis combinaciones siguientes se observaron explícitamente en el workbook:

1. **Datos originales x 12 agrupaciones**: `Cuadro 1`.
2. **Datos originales x 25 agrupaciones**: `Cuadro 2`.
3. **Datos originales x 61 agrupaciones**: `Cuadro 3`.
4. **Datos ajustados por efecto estacional y calendario x 12 agrupaciones**:
   `Cuadro 4`.
5. **Datos ajustados por efecto estacional y calendario x 25 agrupaciones**:
   `Cuadro 5`.
6. **Datos ajustados por efecto estacional y calendario x 61 agrupaciones**:
   `Cuadro 6`.

La hoja `Índice` describe los cuadros con estas etiquetas:

- `12 agrupaciones - Secciones CIIU Rev. 4 A.C.` para los cuadros 1 y 4;
- `25 agrupaciones - Secciones CIIU Rev. 4 A.C.` para los cuadros 2 y 5;
- `61 agrupaciones - Secciones CIIU Rev. 4 A.C.` para los cuadros 3 y 6.

La separación entre cuadros originales y ajustados es estructural y aparece
también en los títulos de los cuadros. No son seis series independientes de
actividad.

## 5. Estructura interna de los cuadros

Cada cuadro contiene tres tablas consecutivas. Cada tabla repite sus títulos,
cabeceras temporales, filas económicas y notas.

### Cuadros 1–3: datos originales

1. `NIVEL`, visible como `Miles de millones de pesos`.
2. `CRECIMIENTO_ANUAL`, visible como `Tasa de crecimiento anual`.
3. `CRECIMIENTO_ANO_CORRIDO`, visible como `Tasa de crecimiento año corrido`.

### Cuadros 4–6: datos ajustados

1. `NIVEL`, visible como `Miles de millones de pesos`.
2. `CRECIMIENTO_TRIMESTRAL`, visible como `Tasa de crecimiento trimestral`.
3. `CRECIMIENTO_ANO_CORRIDO`, visible como `Tasa de crecimiento año corrido`.

En esta investigación, `Tasa de crecimiento anual` corresponde al indicador
`CRECIMIENTO_ANUAL`; `Tasa de crecimiento trimestral` corresponde a
`CRECIMIENTO_TRIMESTRAL`; y `Tasa de crecimiento año corrido` corresponde a
`CRECIMIENTO_ANO_CORRIDO`. Esta correspondencia no convierte la unidad en un
identificador del indicador.

## 6. Mapa de tablas por cuadro

Las filas se refieren a los números de fila de Excel. La fila posterior al
encabezado de períodos es una fila vacía; la primera fila de datos aparece
después de ella. La última fila de datos es la última fila económica antes de
las filas de notas.

| Cuadro | Tabla | Indicador | Fila encabezado | Fila período | Fila vacía posterior | Primera fila datos | Última fila datos | Filas de datos |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `Cuadro 1` | 1 | `NIVEL` | 12 | 13 | 14 | 15 | 29 | 15 |
| `Cuadro 1` | 2 | `CRECIMIENTO_ANUAL` | 45 | 46 | 47 | 48 | 62 | 15 |
| `Cuadro 1` | 3 | `CRECIMIENTO_ANO_CORRIDO` | 78 | 79 | 80 | 81 | 95 | 15 |
| `Cuadro 2` | 1 | `NIVEL` | 12 | 13 | 14 | 15 | 54 | 40 |
| `Cuadro 2` | 2 | `CRECIMIENTO_ANUAL` | 70 | 71 | 72 | 73 | 112 | 40 |
| `Cuadro 2` | 3 | `CRECIMIENTO_ANO_CORRIDO` | 128 | 129 | 130 | 131 | 170 | 40 |
| `Cuadro 3` | 1 | `NIVEL` | 12 | 13 | 14 | 15 | 103 | 89 |
| `Cuadro 3` | 2 | `CRECIMIENTO_ANUAL` | 119 | 120 | 121 | 122 | 210 | 89 |
| `Cuadro 3` | 3 | `CRECIMIENTO_ANO_CORRIDO` | 226 | 227 | 228 | 229 | 317 | 89 |
| `Cuadro 4` | 1 | `NIVEL` | 12 | 13 | 14 | 15 | 29 | 15 |
| `Cuadro 4` | 2 | `CRECIMIENTO_TRIMESTRAL` | 45 | 46 | 47 | 48 | 62 | 15 |
| `Cuadro 4` | 3 | `CRECIMIENTO_ANO_CORRIDO` | 78 | 79 | 80 | 81 | 95 | 15 |
| `Cuadro 5` | 1 | `NIVEL` | 12 | 13 | 14 | 15 | 54 | 40 |
| `Cuadro 5` | 2 | `CRECIMIENTO_TRIMESTRAL` | 70 | 71 | 72 | 73 | 112 | 40 |
| `Cuadro 5` | 3 | `CRECIMIENTO_ANO_CORRIDO` | 128 | 129 | 130 | 131 | 170 | 40 |
| `Cuadro 6` | 1 | `NIVEL` | 12 | 13 | 14 | 15 | 103 | 89 |
| `Cuadro 6` | 2 | `CRECIMIENTO_TRIMESTRAL` | 119 | 120 | 121 | 122 | 210 | 89 |
| `Cuadro 6` | 3 | `CRECIMIENTO_ANO_CORRIDO` | 226 | 227 | 228 | 229 | 317 | 89 |

Cada tabla tiene además tres filas de notas antes de la fila de actualización:
`Fuente: DANE, PIB_T`, `prpreliminar` y `pprovisional`. La actualización se
observa en las filas 34, 67 y 100 de los cuadros 1 y 4; 59, 117 y 175 de los
cuadros 2 y 5; y 108, 215 y 322 de los cuadros 3 y 6.

## 7. Estructura temporal

Los años y trimestres están representados en columnas. La fila superior del
encabezado contiene el año y la fila inferior contiene el trimestre romano:
`I`, `II`, `III` o `IV`.

Los años utilizan celdas combinadas. Ejemplos observados en los cuadros 3 y
6: `E12:H12` contiene `2005`, `I12:L12` contiene `2006`, `CC12:CF12`
corresponde a `2024p`, `CG12:CJ12` a `2025pr` y `CK12:CL12` contiene el
último año publicado `2026pr` para `I` y `II`. En el primer cuadro, por
ejemplo, el período comienza en `D`; en los cuadros 2, 3, 5 y 6 comienza en
`E`. Las tablas posteriores repiten el mismo patrón en sus propias filas de
encabezado.

Conceptualmente, debajo de cada año aparecen `I`, `II`, `III`, `IV`; para el
último año aparecen solo `I`, `II`. El año debe propagarse estructuralmente a
las columnas cubiertas por la celda combinada. Esta sección documenta el
comportamiento observado; no implementa esa propagación.

## 8. Estados `p` / `pr`

Los marcadores aparecen como sufijos del encabezado anual, no como períodos
separados. Se observaron encabezados `2024p`, `2025pr` y `2026pr`.

La interpretación estructural es:

- `2024p` + `I`, `II`, `III`, `IV` -> estado `p`;
- `2025pr` + `I`, `II`, `III`, `IV` -> estado `pr`;
- `2026pr` + `I`, `II` -> estado `pr`.

El estado se propaga a cada trimestre cubierto por el año combinado. Los
años anteriores pueden no contener estado y, en ese caso, el estado puede ser
`null`. En las notas, el archivo muestra literalmente `pprovisional` y
`prpreliminar`, pero el Inspector debe conservar el código observado `p` o
`pr`; no debe convertirlo todavía en `provisional` o `preliminar`.

## 9. Horizonte temporal por indicador

Los indicadores no comparten necesariamente el mismo período inicial:

| Indicador | Rango observado |
|---|---|
| `NIVEL` | 2005-I -> 2026-II |
| `CRECIMIENTO_ANUAL` | 2006-I -> 2026-II |
| `CRECIMIENTO_ANO_CORRIDO` | 2006-I -> 2026-II |
| `CRECIMIENTO_TRIMESTRAL` | 2005-II -> 2026-II |

Esta diferencia importa para la validación. No es válido exigir que todos los
indicadores tengan exactamente los mismos períodos ni tratar un período
ausente al inicio como una estructura inválida por sí sola.

## 10. Estructura de columnas

Las columnas descriptoras cambian con el nivel de agregación.

### Cuadros 1 y 4

Se observan, en orden, `Clasificación Cuentas Nacionales`, `Secciones CIIU
Rev. 4 A.C. / 12 agrupaciones`, `Concepto` y las columnas temporales. La
matriz temporal comienza en `D`.

### Cuadros 2 y 5

Se observan `Clasificación Cuentas Nacionales`, `Secciones CIIU Rev. 4 A.C. /
12 agrupaciones`, `Secciones y divisiones CIIU Rev. 4 A.C. / 25 agrupaciones`,
`Concepto` y las columnas temporales. La matriz temporal comienza en `E`.

### Cuadros 3 y 6

Se observan `Clasificación Cuentas Nacionales`, `Secciones y divisiones CIIU
Rev. 4 A.C. / 25 agrupaciones`, `Divisiones CIIU Rev. 4 A.C. / 61
agrupaciones`, `Concepto` y las columnas temporales. La matriz temporal
comienza en `E`.

## 11. Filas de actividades y totales

Las filas económicas observadas por tabla son:

| Nivel | Filas de conceptos/actividades | `Valor agregado bruto` | `Impuestos menos subvenciones sobre los productos` | `Producto Interno Bruto` | Total filas económicas |
|---:|---:|---:|---:|---:|---:|
| 12 | 12 | 1 | 1 | 1 | 15 |
| 25 | 37 | 1 | 1 | 1 | 40 |
| 61 | 86 | 1 | 1 | 1 | 89 |

Los conteos anteriores se obtienen clasificando las filas económicas del área
de datos, no contando `max_row`. Las filas de notas, encabezados y separadores
no son observaciones económicas.

**12, 25 y 61 no deben inferirse contando filas.** Son niveles de
agregación/clasificación declarados por los encabezados del workbook. Las
filas adicionales de agregados y totales hacen que el número de filas físicas
sea distinto del nombre del nivel.

## 12. Clasificación económica

La estructura observada es:

```text
nivel de agregación
  -> código de clasificación
    -> concepto
```

Ejemplos no exhaustivos observados:

- secciones: `A`, `B`, `C`;
- agrupaciones: `C01`, `C02`, `C03`;
- códigos combinados o rangos: `043, 044` y `045 - 047`;
- código compuesto observado en una actividad del cuadro de 61:
  `001, 002, 004 - 008, 013`.

Los códigos y conceptos pertenecen a diferentes niveles de desagregación y
deben conservarse como texto publicado. Esta investigación no diseña una
dimensión de actividad ni expande rangos.

## 13. Metadatos del encabezado

Los metadatos observados deben mantenerse conceptualmente separados:

| Dimensión | Texto o evidencia observada |
|---|---|
| Indicador | `Miles de millones de pesos`, `Tasa de crecimiento anual`, `Tasa de crecimiento trimestral`, `Tasa de crecimiento año corrido` |
| Unidad | `Miles de millones de pesos` para `NIVEL`; las tablas de tasas se identifican por su título de crecimiento |
| Serie | `Datos originales` o `Datos ajustados por efecto estacional y calendario` |
| Base | `Series encadenadas de volumen con año de referencia 2015` |
| Cobertura | `2005 - 2026pr segundo trimestre` en el encabezado de los cuadros |
| Estado | Sufijos anuales `p` y `pr`; notas `pprovisional` y `prpreliminar` |
| Fuente | `Fuente: DANE, PIB_T` |
| Fecha de actualización | `Actualizado el 18 de agosto de 2026` |
| Publicación | `Producto Interno Bruto (PIB)` |

`Producto Interno Bruto (PIB)` es el título de la publicación/cuadro; no es
el indicador de cada bloque. `NIVEL` y las tasas son indicadores; `Miles de
millones de pesos` es una unidad; `Original` y `Ajustada por efecto estacional
y calendario` son familias de serie; `p` y `pr` son estados; y la fecha de
actualización es metadato de publicación.

## 14. Reglas estructurales respaldadas por evidencia

El Inspector sí puede asumir, para validar esta estructura observada, que:

1. Existe una hoja `Índice`.
2. Existen seis hojas de cuadros.
3. Existen seis combinaciones serie x agregación.
4. Cada cuadro contiene tres tablas verticales.
5. El indicador depende de la tabla/bloque dentro del cuadro.
6. Los años utilizan celdas combinadas.
7. Los trimestres están en una fila debajo del año.
8. `p` y `pr` forman parte del encabezado anual.
9. El estado se propaga a los trimestres cubiertos por ese año.
10. Los indicadores pueden tener diferentes horizontes temporales.
11. Los niveles 12/25/61 no deben inferirse contando filas.
12. La clasificación tiene estructura jerárquica.
13. Las unidades no deben utilizarse como identificador único del indicador.

Estas reglas están respaldadas por este archivo concreto. No garantizan que
una futura publicación conserve todas las posiciones físicas.

## 15. Reglas que deben evitarse

El Inspector no debe asumir:

- `Miles de millones de pesos` -> `NIVEL` sin confirmar el contexto del
  bloque;
- texto encontrado en cualquier parte de la hoja -> indicador de toda la hoja;
- contar filas -> determinar 12/25/61;
- una ventana fija de filas -> encontrar el año;
- que todos los años tienen `p` o `pr`;
- que todos los indicadores tienen el mismo período inicial;
- que todas las tablas tienen exactamente la misma cantidad de filas;
- convertir `p` o `pr` en etiquetas semánticas dentro del Inspector.

## 16. Implicaciones para `PIBWorkbookInspector`

La evidencia del XLSX real cambia las decisiones de diseño de la siguiente
manera:

### Detección de indicador

Debe depender del bloque vertical y sus títulos estructurales, no de una
búsqueda global de texto. La misma hoja contiene varios indicadores.

### Detección de período

Debe considerar las celdas combinadas y los encabezados jerárquicos de año y
trimestre. Un año vacío en una celda posterior puede ser el efecto de una
celda combinada, no la ausencia de período.

### Estado

Debe derivarse del encabezado anual y propagarse a los trimestres de ese año.
El código publicado se conserva como `p`, `pr` o `null` cuando no hay estado.

### Agregación

Debe determinarse a partir de los encabezados `Secciones`, `Secciones y
divisiones` o `Divisiones`, junto con `12`, `25` o `61 agrupaciones`; no
contando filas.

### Serie

Debe determinarse desde el cuadro y/o sus metadatos explícitos: `Datos
originales` frente a `Datos ajustados por efecto estacional y calendario`.

### Validación

Debe validar las seis combinaciones reales de serie y agregación, y fallar de
forma controlada ante hojas, bloques, estados o encabezados desconocidos.

Ninguna de estas correcciones se implementa en este documento.

## 17. Mapa conceptual

```text
DANE PIB_T
|
|-- ORIGINAL
|   |-- 12
|   |   |-- NIVEL
|   |   |-- CRECIMIENTO ANUAL
|   |   `-- CRECIMIENTO ANO CORRIDO
|   |-- 25
|   |   |-- NIVEL
|   |   |-- CRECIMIENTO ANUAL
|   |   `-- CRECIMIENTO ANO CORRIDO
|   `-- 61
|       |-- NIVEL
|       |-- CRECIMIENTO ANUAL
|       `-- CRECIMIENTO ANO CORRIDO
|
`-- AJUSTADA POR EFECTO ESTACIONAL Y CALENDARIO
    |-- 12
    |   |-- NIVEL
    |   |-- CRECIMIENTO TRIMESTRAL
    |   `-- CRECIMIENTO ANO CORRIDO
    |-- 25
    |   |-- NIVEL
    |   |-- CRECIMIENTO TRIMESTRAL
    |   `-- CRECIMIENTO ANO CORRIDO
    `-- 61
        |-- NIVEL
        |-- CRECIMIENTO TRIMESTRAL
        `-- CRECIMIENTO ANO CORRIDO
```

## 18. Tabla final de evidencia

| Hallazgo | Evidencia observada | Confianza | Implicación |
|---|---|---|---|
| Seis cuadros | Hojas `Cuadro 1` a `Cuadro 6` y hoja `Índice` | ALTA | Validar las seis hojas de cuadros |
| Seis combinaciones | Índice y títulos de cuadros declaran original/ajustada y 12/25/61 | ALTA | Validar cada combinación serie x agregación |
| Tres tablas por cuadro | Tres encabezados de bloque repetidos en cada cuadro | ALTA | Detectar bloques verticales |
| Celdas combinadas | Rangos como `E12:H12`, `CG12:CJ12` y `CK12:CL12` | ALTA | Resolver y propagar años estructuralmente |
| Estados `p`/`pr` | Encabezados `2024p`, `2025pr`, `2026pr` y notas correspondientes | ALTA | Propagar el código sin traducirlo |
| Horizontes distintos | `NIVEL` inicia en 2005-I; crecimiento trimestral en 2005-II; otros crecimientos en 2006-I | ALTA | No exigir una cobertura idéntica |
| Niveles 12/25/61 | Encabezados CIIU y hoja `Índice` | ALTA | No calcular el nivel con conteo de filas |
| Clasificación jerárquica | Columnas CIIU separadas y códigos como `C01` y rangos | ALTA | Conservar nivel, código y concepto separados |
| Indicador y unidad separados | Títulos de bloque y unidad `Miles de millones de pesos` | ALTA | La unidad no identifica por sí sola el indicador |
| Filas adicionales | Filas económicas incluyen VAB, impuestos y PIB además de actividades | ALTA | No interpretar el número físico de filas como agrupación |

La confianza `ALTA` se usa únicamente para hallazgos directamente observables
en este XLSX. Las reglas sobre futuras publicaciones serían, como máximo,
inferencias y no se presentan como evidencia universal.

## 19. Limitaciones

- El análisis se basa en un XLSX concreto: `anex-ProduccionConstantes-IItrim2026.xlsx`.
- Una futura publicación DANE puede cambiar nombres, posiciones, filas,
  columnas, notas o combinaciones.
- Este documento describe evidencia observada; no constituye una afirmación
  universal sobre todos los futuros archivos DANE.
- No se garantiza que otro XLSX tenga exactamente las mismas filas físicas o
  rangos temporales.
- El Inspector deberá fallar de forma controlada si encuentra una estructura
  desconocida o ambigua, en vez de convertirla silenciosamente en datos.

## 20. Relación con la documentación existente

Este documento aporta evidencia empírica del XLSX real y complementa la
documentación arquitectónica:

- [Estructura previa del XLSX](dane-pib-xlsx-structure.md) contiene la
  investigación estructural anterior y contexto de inspección.
- [Modelo de datos PIB](../architecture/pib-data-model.md) define el contrato
  analítico que el documento de investigación no modifica.
- [Especificación del transformador PIB](../architecture/pib-transformer-spec.md)
  describe una implementación futura; esta investigación aporta evidencia
  para sus decisiones, pero no implementa el transformador.
- La estrategia de fuente `dane-pib-trimestral-source-strategy.md` se
  relaciona con la identificación de la publicación y su origen, pero no fue
  modificada en este cambio.
- `PIBWorkbookInspector` es la implementación que deberá consumir esta
  evidencia en un cambio posterior; no se modifica en este PR.

## 21. No implementado

Este cambio contiene únicamente documentación. No se modificaron `src/`,
`tests/`, pipelines, workflows, GitHub Actions, Data Contract, Extractor,
Transformer ni datasets. El XLSX fue utilizado como artefacto local de
investigación y no se agrega al repositorio.