# Colombia Economic Intelligence

Colombia Economic Intelligence es un proyecto para construir una plataforma de inteligencia económica sobre Colombia a partir de datos públicos oficiales. Su propósito es organizar, procesar, validar y visualizar indicadores económicos relevantes para análisis ejecutivo, seguimiento macroeconómico y generación de insights.

## Objetivo

Desarrollar una base analítica reproducible que integre información oficial, principalmente de DANE y Banco de la República, con una arquitectura preparada para automatización futura, análisis estadístico/económico y dashboards en Power BI.

## Alcance inicial

Esta fase prepara únicamente la estructura base del repositorio. No incluye descarga de datos, consultas a APIs, implementación de pipelines de extracción, workflows de GitHub Actions ni desarrollos de Power BI.

Antes de implementar pipelines, las fuentes, datasets, series específicas, metodologías y métodos de extracción serán documentados en los archivos de documentación del proyecto.

## Dominios económicos previstos

Los dominios iniciales de análisis son:

- Crecimiento económico.
- Inflación y precios.
- Mercado laboral.
- Política monetaria y sistema financiero.
- Sector externo.

XM se considera inicialmente una fuente de expansión para incorporar indicadores del dominio energético en fases posteriores.

## Fuentes principales previstas

- **DANE**: estadísticas oficiales de actividad económica, precios, mercado laboral y otros indicadores nacionales.
- **Banco de la República**: series macroeconómicas, monetarias, financieras y externas.
- **XM**: fuente potencial de expansión para información energética.

## Arquitectura general

El flujo previsto del proyecto es:

```text
Fuentes oficiales
→ extracción
→ raw data
→ transformación/validación
→ processed data
→ Power BI
→ análisis/insights
```

La automatización con GitHub Actions será incorporada posteriormente para ejecutar actualizaciones, validaciones y procesos recurrentes cuando las fuentes y series estén definidas.

## Estructura del repositorio

```text
.github/workflows/   # Workflows futuros de GitHub Actions
data/raw/            # Datos originales por fuente
data/processed/      # Datos transformados y validados
src/                 # Código futuro por fuente o dominio
powerbi/             # Artefactos futuros de Power BI
analysis/            # Análisis estadístico/económico futuro
docs/                # Documentación técnica y metodológica
tests/               # Pruebas futuras
```

## Estado actual del proyecto

El proyecto está en fase inicial de preparación del repositorio. La estructura de carpetas, documentación base, dependencias mínimas y reglas de exclusión de archivos quedan definidas para habilitar el desarrollo posterior de pipelines, validaciones, modelo analítico y dashboards.
