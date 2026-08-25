"""
=============================================================================
HERRAMIENTA DE CLASIFICACIÓN DE SEVERIDAD DE CONTAMINACIÓN DEL SITIO (SPS)
PARA AISLADORES DE ALTA TENSIÓN - IEC TS 60815-1/2/3:2008
=============================================================================
Memoria de Título - David Pérez
"Impacto de la polución salina en equipos primarios de subestaciones AT:
clasificación del sitio y diseño de medidas de mitigación"
Universidad de Santiago de Chile (USACH) - Departamento de Ingeniería Eléctrica

 Código fuente completo (módulos B.1 a B.8)

Módulos:
    B.1 - Estructura de datos y constantes normativas
    B.2 - Clasificación SPS (ESDD/NSDD)
    B.3 - Módulo ambiental (HR, viento, lluvia)
    B.4 - Módulo eléctrico (Um, Uph-e, USCD, Lmin)
    B.5 - Módulo mecánico (perfil, Kad, Ka por altitud, s/p, CF)
    B.6 - Integración de resultados y generación de recomendaciones
    B.7 - Módulo de graficación de resultados
    B.8 - CLI interactivo

=============================================================================
"""

import math
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


# =============================================================================
# B.1 - Estructura de datos y constantes normativas
# =============================================================================

# Tabla 3.1 - Niveles de aceptación operacional (adaptación operacional de
# IEC TS 60815-1:2008)
UMBRALES_CRITICIDAD = {
    "Normal":      {"esdd_max": 0.04, "nsdd_max": 0.10},
    "Advertencia": {"esdd_max": 0.15, "nsdd_max": 0.30},
}

# Tabla 4.1 - Umbrales de HR de activación por entorno (Sección 4.2.1)
UMBRAL_HR_ACTIVACION = {
    "costero":    75,
    "desertico":  60,
    "industrial": 75,
}

# Tabla IEC 60815-1 - USCD (mm/kV) según clase de severidad IEC de 5 niveles
USCD_POR_CLASE_SEVERIDAD = {
    "muy_ligero": 22.0,
    "ligero":     27.8,
    "medio":      34.7,
    "pesado":     43.3,
    "muy_pesado": 53.7,
}


class ResultadoSPS:
    """Resultado de la clasificación SPS (B.2)."""
    def __init__(self, nivel, esdd, nsdd, clase_severidad):
        self.nivel = nivel
        self.esdd = esdd
        self.nsdd = nsdd
        self.clase_severidad = clase_severidad

    def __repr__(self):
        return (f"ResultadoSPS(nivel='{self.nivel}', esdd={self.esdd}, "
                f"nsdd={self.nsdd}, clase_severidad='{self.clase_severidad}')")