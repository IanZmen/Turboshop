# Tarea Técnica - Área de Datos | Turboshop

## 📋 Descripción General

Esta tarea técnica simula uno de los desafíos diarios que enfrenta el equipo de datos de Turboshop: procesar y estructurar datos extremadamente crudos provenientes de diferentes proveedores de repuestos automotrices.

Los proveedores envían archivos con el mismo formato pero con datos actualizados periódicamente (cambios en compatibilidades, nombres de repuestos, códigos OEM, etc.). El objetivo final es construir un catálogo unificado de repuestos donde cada repuesto quede correctamente mapeado a los vehículos con los que es compatible.

### Resumen Ejecutivo

En corto, tienes fuentes de datos de proveedores en formatos variados, con información incompleta y poco exacta y deberás extraer datos de fuentes de internet para completar los datos, transformar los datos para ordenar la información y cargar los datos en una única tabla de datos que deberá ser utilizada como fuente de verdad.

## 🎯 Objetivo

Desarrollar un proceso ETL (Extract, Transform, Load) que:

1. **Extraiga** toda la información disponible de los repuestos y sus compatibilidades
2. **Transforme** los datos a un esquema estructurado y uniforme, independiente del proveedor
3. **Cargue** los datos procesados en un formato que permita su utilización

### Información a Rescatar

- ✅ Información completa del repuesto
- ✅ Compatibilidades asociadas a cada repuesto
- ✅ Medidas y especificaciones técnicas
- ✅ Compatibilidades por tipo de motor **OJITO**
- ✅ Datos estructurados y uniformes

## 🚨 Desafíos Reales del Día a Día

Los datos que recibimos presentan múltiples desafíos que pueden parecer de chiste pero son completamente reales:

### Casos Comunes:

1. **Compatibilidades en el nombre**: Las compatibilidades muchas veces están embebidas en el nombre del repuesto y no en la sección dedicada de compatibilidades
2. **Compatibilidades vagas**: Información incompleta o ambigua sobre qué vehículos son compatibles
3. **Solo códigos OEM**: El peor escenario donde los proveedores solo proporcionan códigos OEM sin información adicional

### ¿Qué es un OEM?

Un **OEM** (Original Equipment Manufacturer) es un código único que funciona como un "código de barras" para identificar un repuesto en su totalidad. Es un número de referencia estándar que permite identificar de manera precisa un componente específico del fabricante original.

## 📊 Estructura de los Datos

El archivo `datos_tarea_reclutamiento.xlsx` contiene 4 hojas que representan diferentes proveedores con distintos niveles de completitud:

### Proveedor 1

- **Columnas**: SKU, OEM, COMPATIBILIDADES, REPUESTO
- **Nivel**: Datos relativamente completos con compatibilidades explícitas

### Proveedor 2

- **Columnas**: CODIGO, DESCRIPCION, APLICACIONES
- **Nivel**: Formato diferente pero con compatibilidades estructuradas

### Proveedor 3 ⚠️

- **Columnas**: Solo OEM
- **Nivel**: **PEOR ESCENARIO** - Solo códigos OEM sin información adicional
- **Desafío**: Es responsabilidad del postulante encontrar los datos correspondientes al repuesto y sus compatibilidades

### Proveedor 4

- **Columnas**: SKU, REPUESTO, codigo
- **Nivel**: Las compatibilidades están embebidas en el nombre del repuesto

## 🔍 Requisitos Técnicos

### Funcionalidad

- ✅ El ETL debe funcionar con **datos nuevos** del mismo formato
- ✅ El procesamiento debe ser consistente y reproducible
- ✅ La solución debe ser escalable y mantenible

### Caso Especial: Proveedor 3

Para el proveedor 3 (solo OEMs), es necesario:

- 🔍 Buscar información complementaria en internet (scraping)
- 📝 Encontrar datos del repuesto y compatibilidades asociadas
- 💡 Demostrar creatividad y proactividad en la búsqueda de datos

> **Nota**: En Turboshop todos los días estudiamos y buscamos información relevante en internet que nos ayude a complementar los datos que manejamos. Esta tarea simula un día en la oficina y queremos ver hasta dónde puede llegar tu creatividad y hambre por resolver problemas.

## 🛠️ Herramientas y Recursos

### API Key de OpenAI

Se proporcionará una **API_KEY de OpenAI** en caso de requerir el uso de IA para el procesamiento de datos.

> ⚠️ **Importante**: Un uso exhaustivo de la API tampoco es positivo. Se valora la eficiencia y el uso inteligente de recursos.

### Recomendaciones de Páginas

Para complementar los datos, especialmente en el caso del proveedor 3, te recomendamos explorar la siguiente referencia:

- **[Boston.cl](https://boston.cl)**: Catálogo de repuestos con datos técnicos y compatibilidades

> ⚠️ **Nota**: Esta es solo una recomendación y no garantizamos que sea útil al 100% para todos los casos. Sin embargo, te dará un contexto valioso sobre cómo se mueven los repuestos automotrices en Chile y cómo diferentes plataformas estructuran y presentan la información de compatibilidades.

Esta página puede servirte como referencia para:
- Entender cómo se estructura la información de repuestos en el mercado chileno
- Ver ejemplos de cómo se presentan compatibilidades y aplicaciones
- Explorar diferentes formatos de datos y estructuras de catálogos
- Obtener ideas sobre cómo complementar información faltante

> 💡 **Pista**: Investiga cómo se puede hacer scraping de manera ética y eficiente para obtener información complementaria. Considera siempre respetar los términos de servicio y las políticas de uso de los sitios web.

## 📤 Formato de Salida

La estructura de salida de los datos queda **a criterio del postulante**. Algunas consideraciones:

- Formato estructurado y fácil de consumir (JSON, CSV, Parquet, etc.)
- Esquema uniforme independiente del proveedor
- Información completa y validada
- Documentación del esquema de salida

## ✅ Criterios de Evaluación

Buscamos:

1. **Buenas prácticas de programación**

   - Código limpio y mantenible
   - Estructura clara y organizada
   - Documentación adecuada
2. **Funcionalidad robusta**

   - Que funcione para diferentes datos
   - Manejo de casos edge
   - Validación de datos
3. **Creatividad**

   - Soluciones innovadoras para problemas complejos
   - Uso inteligente de herramientas disponibles
   - Complementación de datos faltantes
4. **Interés y dedicación**

   - No tiene que ser perfecto, pero debe mostrar interés en la solución
   - Mientras más se pueda complementar los datos, mejor
   - Proactividad en la búsqueda de información

5. **Insights y análisis**

   - Generar insights sobre los datos procesados
   - Identificar qué cosas ve difíciles pero que cree que se pueden resolver
   - Observaciones sobre patrones, inconsistencias o oportunidades de mejora
   - Reflexiones sobre el proceso y posibles optimizaciones

## 📝 Entregables

1. **Código del ETL** con documentación
2. **README** explicando:

   - Arquitectura de la solución
   - Decisiones técnicas tomadas
   - Cómo ejecutar el código
   - Estructura de salida de datos
3. **Datos procesados** en el formato elegido
4. **Insights y observaciones** (opcional pero valorado):

   - Análisis de los datos procesados
   - Identificación de desafíos encontrados y posibles soluciones
   - Observaciones sobre patrones o inconsistencias detectadas
   - Reflexiones sobre el proceso y oportunidades de mejora

## 🚀 Cómo Empezar

1. Explora el archivo `datos_tarea_reclutamiento.xlsx`
2. Analiza la estructura de cada proveedor
3. Diseña tu estrategia de ETL
4. Implementa la solución
5. Documenta tu trabajo

## 💬 Preguntas y Contacto

Si tienes dudas, preguntas o necesitas aclaraciones sobre la tarea, puedes contactarnos con toda libertad:

- **Email**: [gonzalo@Turboshop.cl](mailto:gonzalo@Turboshop.cl)
- **WhatsApp**: [+56992895340](https://wa.me/56992895340)

Estamos disponibles para ayudarte y resolver cualquier inquietud que tengas durante el desarrollo de la tarea.

## 💬 Notas Finales

Esta tarea no busca la solución perfecta, sino demostrar:

- Tu capacidad para trabajar con datos complejos y desestructurados
- Tu creatividad para resolver problemas reales
- Tu interés en complementar y mejorar los datos disponibles
- Tu habilidad para escribir código limpio y mantenible

**¡Mucha suerte y que disfrutes el desafío!** 🚗🔧
