DEFAULT_OUTPUT_FIELDS = {
    "uso_de_OPEN_AI": False,
    "paginas_de_informacion": "-",
}

# Orden recomendado de columnas para la salida final
OUTPUT_COLUMN_ORDER = [
    # Identificación básica del repuesto y origen
    "repuesto_sku",
    "repuesto_oem",
    "proveedor",
    "formato_origen",

    # Datos del repuesto
    "repuesto_nombre",
    "repuesto_especificaciones_texto",
    "repuesto_medida_1",
    "repuesto_medida_2",
    "repuesto_medida_3",
    "repuesto_medida_4",
    "repuesto_cantidad_medidas",
    "repuesto_separador_medidas",

    # Compatibilidad
    "compatibilidad_marca",
    "compatibilidad_modelo",
    "compatibilidad_anio_desde",
    "compatibilidad_anio_hasta",
    "compatibilidad_motor_litros",
    "compatibilidad_codigo_motor",
    "compatibilidad_texto",

    # IA y enlaces
    "uso_de_OPEN_AI",
    "paginas_de_informacion",
]
