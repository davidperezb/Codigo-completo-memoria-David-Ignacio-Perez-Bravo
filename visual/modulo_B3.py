# =============================================================================
# B.3 - Módulo ambiental (evaluación de HR, viento y lluvia)
# =============================================================================

# Umbral de velocidad de viento 
UMBRAL_VIENTO_MS = 3.5

# Umbral de intensidad de lluvia para lavado natural efectivo 
UMBRAL_LLUVIA_MM_DIA = 50


EXPLICACION_INDICADOR_AMBIENTAL = {
    "activacion_hr": (
        "Activación del contaminante por humedad relativa (HR alcanza el "
        "umbral del entorno)"
    ),
    "acumulacion_viento": (
        "Acumulación acelerada de contaminante por viento (> 3,5 m/s)"
    ),
    "lavado_lluvia": (
        "Lavado natural efectivo por lluvia (>= 50 mm/día)"
    ),
}


class ResultadoAmbiental:
    """
    Contenedor del resultado del módulo ambiental (Sección 5.3.3).

    A diferencia de la clasificación SPS (B.2), este módulo no reclasifica
    el nivel de aceptación operacional del sitio; solo genera indicadores
    de tendencia de riesgo independientes entre sí, a partir de las
    variables ambientales caracterizadas en el Capítulo 4.

    Atributos:
        entorno (str): "costero", "desertico" o "industrial".
        activacion_hr (bool): True si la HR ingresada supera el umbral de
            activación del entorno (Tabla 4.1).
        acumulacion_viento (bool): True si la velocidad de viento supera
            el umbral de 3,5 m/s (Sección 4.2.2), indicando acumulación
            acelerada de contaminante.
        lavado_lluvia (bool): True si la intensidad de lluvia alcanza o
            supera el umbral de 50 mm/día (Sección 4.2.3), indicando
            lavado natural probable.
    """

    def __init__(self, entorno, activacion_hr, acumulacion_viento, lavado_lluvia):
        self.entorno = entorno
        self.activacion_hr = activacion_hr
        self.acumulacion_viento = acumulacion_viento
        self.lavado_lluvia = lavado_lluvia

    def __repr__(self):
        return (f"ResultadoAmbiental(entorno='{self.entorno}', "
                f"activacion_hr={self.activacion_hr}, "
                f"acumulacion_viento={self.acumulacion_viento}, "
                f"lavado_lluvia={self.lavado_lluvia})")


def evaluar_modulo_ambiental(entorno, hr, viento, lluvia):
    """
    Evalúa las variables ambientales (HR, viento y lluvia) contra los
    umbrales definidos en la Sección 4.2.1, generando indicadores de
    tendencia de riesgo independientes de la clasificación SPS (Sección 5.3.3).

    Args:
        entorno (str): tipo de entorno del sitio ("costero", "desertico"
            o "industrial").
        hr (float): humedad relativa promedio del sitio (%).
        viento (float): velocidad de viento promedio (m/s).
        lluvia (float): intensidad de lluvia de referencia (mm/día).

    Returns:
        ResultadoAmbiental: objeto con los tres indicadores de tendencia
        de riesgo evaluados de forma independiente.

    Raises:
        ValueError: si entorno no corresponde a uno de los tres valores
            válidos, o si hr, viento o lluvia son negativos.
    """
    if entorno not in UMBRAL_HR_ACTIVACION:
        raise ValueError(
            f"Entorno '{entorno}' no válido. Debe ser 'costero', "
            f"'desertico' o 'industrial'."
        )
    if hr < 0 or viento < 0 or lluvia < 0:
        raise ValueError("HR, viento y lluvia deben ser valores no negativos.")

    activacion_hr = _evaluar_activacion_hr(entorno, hr)
    acumulacion_viento = _evaluar_acumulacion_viento(viento)
    lavado_lluvia = _evaluar_lavado_lluvia(lluvia)

    return ResultadoAmbiental(entorno, activacion_hr, acumulacion_viento, lavado_lluvia)


def _evaluar_activacion_hr(entorno, hr):
    """
    Determina si la HR ingresada activa el contaminante depositado sobre
    el aislador, según el umbral del entorno correspondiente (Tabla 4.1).
    """
    return hr >= UMBRAL_HR_ACTIVACION[entorno]


def _evaluar_acumulacion_viento(viento):
    """
    Determina si la velocidad de viento favorece una acumulación acelerada
    de contaminante sobre el aislador (Sección 4.2.2, umbral de 3,5 m/s
    adaptado de [40]).
    """
    return viento > UMBRAL_VIENTO_MS


def _evaluar_lavado_lluvia(lluvia):
    """
    Determina si la intensidad de lluvia ingresada corresponde a un
    evento de lavado natural efectivo (Sección 4.2.3, umbral de
    50 mm/día adaptado de [42]).
    """
    return lluvia >= UMBRAL_LLUVIA_MM_DIA