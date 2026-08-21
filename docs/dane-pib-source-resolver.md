# DANE PIB source resolver

Este módulo implementa la primera pieza técnica del pipeline de PIB trimestral: resolver y descargar temporalmente el XLSX oficial de DANE para `PIB producción` a `precios constantes`.

## Fuente oficial

La fuente principal es la página vigente de información técnica de cuentas nacionales trimestrales del DANE:

- <https://www.dane.gov.co/index.php/estadisticas-por-tema/cuentas-nacionales/cuentas-nacionales-trimestrales/pib-informacion-tecnica>

La fuente histórica documentada para fases posteriores es:

- <https://www.dane.gov.co/index.php/estadisticas-por-tema/cuentas-nacionales/cuentas-nacionales-trimestrales/historicos-producto-interno-bruto-pib>

## Cómo identifica el XLSX

El resolver parsea el HTML oficial, normaliza los enlaces y busca el bloque de `Anexos estadísticos PIB producción`. Dentro de ese contexto selecciona únicamente enlaces compatibles con `PIB a precios constantes`.

Antes de aceptar un candidato valida que la URL:

- use HTTPS;
- pertenezca exactamente a `www.dane.gov.co`;
- apunte a un archivo `.xlsx`;
- corresponda a producción y precios constantes;
- no corresponda a precios corrientes, enfoque de gasto o enfoque de ingreso.

Si no hay candidatos válidos se lanza `MissingDanePibSourceError`. Si hay más de un candidato válido se lanza `AmbiguousDanePibSourceError` con las URLs encontradas para diagnosticar el cambio del sitio.

## Descarga, hash y manifest

`download_xlsx()` descarga el archivo a una ruta temporal, con timeout configurable, límite de redirects, validación de errores HTTP, content type cuando está disponible y tamaño mínimo/máximo. Si ocurre un error durante la descarga, el archivo temporal se elimina.

`calculate_sha256()` calcula el SHA-256 leyendo el archivo por bloques. `build_manifest()` genera metadatos con fuente, operación, enfoque, precios, URL, nombre de archivo, trimestre inferido cuando el nombre lo permite, timestamp de descarga, tamaño y hash. La fecha de publicación se deja en `None` si no puede determinarse de forma fiable desde la fuente.

## Ejecución local

Ejemplo mínimo desde la raíz del repositorio:

```bash
python - <<'PY'
from colombia_economic_intelligence.sources.dane_pib_resolver import resolve_download_and_manifest

downloaded, manifest = resolve_download_and_manifest()
print(manifest.to_dict())
print(f"Archivo temporal: {downloaded.path}")
# El consumidor futuro debe mover o eliminar el archivo temporal según su flujo.
PY
```

Los tests unitarios usan fixtures HTML y no requieren conectividad al DANE.
