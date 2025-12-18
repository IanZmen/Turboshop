# Tarea Técnica – Pipeline ETL Turboshop

Este proyecto implementa el proceso ETL solicitado en `ArchivosIniciales/README.md`: toma hojas de proveedores con formatos heterogéneos, extrae/normaliza información de repuestos y compatibilidades (incluidas medidas), y genera un catálogo unificado listo para consumo.

## Arquitectura y flujo
- **Input**: `ArchivosIniciales/datos_tarea_reclutamiento.xlsx` con 4 formatos de proveedor actualmente soportados.
- **Detección de formato**: `detect/format_detector.py` identifica qué transform aplicar.
- **Extract / Enriquecimiento** (proveedor 3: solo OEM):
  - `extract/oem_enrichment.py` orquesta la búsqueda externa de datos de OEM.
  - **Scraping**: `extract/scrapping/sites/toyota_parts_deal.py` usa Selenium vía `WebDriverWrapper` para buscar el OEM, leer especificaciones, dimensiones y cada fitment (compatibilidad). Devuelve múltiples filas: una por modelo/motor/variante. Fue diseñado para ir agregando más páginas para escrapear según se requiera, ahorrando así llamadas al LLM.
  - **LLM opcional**: `extract/OpenAI/oem_llm.py` consulta OpenAI (con `use_llm=True`) como fallback si el scraping no devuelve resultados.
  - Los datos enriquecidos se devuelven en el mismo shape esperado por los transformadores (nombre, especificaciones, medidas, compatibilidades y links).
- **Transform**:
  - `transform/formats/` contiene los procesadores para cada formato (completo, aplicaciones, nombre embebido, OEM solo).
  - `transform/parsing_medidas.py` extrae medidas (evita confundir OEM con medidas) y normaliza textos.
  - `transform/parsing_compatibilidades.py` desglosa marca/modelo/años/motor desde textos.

- **Salida Load**: DataFrame unificado, ordenado con `constants/output.py`, escrito por `load/writer.py` a `out/` en CSV/XLSX u otros según config.

## Ejecución
1) Instala dependencias: `python -m pip install -r requirements.txt`
2) Configura `.env`: `OPENAI_API_KEY=...`
3) Ejecuta el ETL:
```bash
python main.py
```
Parámetros principales en `config.py` (ruta de entrada, directorio de salida, formato, `use_llm`) (se setean en main.py).

## Supuestos y decisiones clave
- Se realizaron supuestos acerca de que eran los numeros de motor
- Para OEM con múltiples compatibilidades, se emite una fila por motor/variante para así facilitar busqueda.
- `repuesto_especificaciones_texto` solo conserva medidas limpias o se reconstruye desde valores numéricos.
- Scraping `toyotapartsdeal` es la primera fuente, después se pueden incluir más según vaya siendo necesario; LLM se usa solo si `use_llm=True`.

## Estructura de salida (columnas)
Orden definida en `constants/output.py`: `repuesto_sku`, `repuesto_oem`, `proveedor`, `formato_origen`, `repuesto_nombre`, `repuesto_especificaciones_texto`, `repuesto_medida_1..4`, `repuesto_cantidad_medidas`, `repuesto_separador_medidas`, compatibilidades (marca/modelo/años/motor/código), `compatibilidad_texto`, `uso_de_OPEN_AI`, `paginas_de_informacion`.

## Notas de mantenimiento
- Si agregas proveedores nuevos, y posee columnas distintas crea un processor en `transform/formats/` y actualiza `detect/format_detector.py` o adaptapta los existentes según compatibilidad.
- Si cambian las páginas de scraping, ajusta selectores en `extract/scrapping/sites/toyota_parts_deal.py`.

## Mejoras:

- Clean code: un solo idioma, hacer funciones más cortas.
- Se puede optimizar el tiempo de scrapping ya que se espera harto,pero es para asegurarnos de que cargue.
- Se podría pensar alguna manera de reducir los tokens por consulta en los llm.
- En general creo que se puede pulir un poco más el provedor 3, pero es una buena base para ir mejorandolo. 


## TODO'S

- No alcancé a separar en filas las compatibilidades del provedor 3
- Quedan filas sin información porque no logró ser encontrada, quizás se podría probar con otros modelos de openai u otros provedores, también se pueden buscar a amano ya que son pocos o quizás al ir implementando más páginas para scrapping se encuentran.