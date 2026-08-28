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


# =============================================================================
# B.2 - Módulo de clasificación SPS (ESDD/NSDD)
# =============================================================================

def clasificar_sps(esdd, nsdd):
    """
    Clasifica el nivel de aceptación operacional del sitio (Normal,
    Advertencia o Crítico) a partir de los valores de ESDD y NSDD medidos
    o simulados, según la Tabla 3.1.

    Regla de combinación: se adopta el criterio más restrictivo entre
    ambos indicadores (si ESDD y NSDD caen en niveles distintos, prevalece
    el de mayor severidad), dado que la componente soluble (ESDD) domina
    la conductividad de la película húmeda mientras que la componente no
    soluble (NSDD) controla la retención de humedad.

    Args:
        esdd (float): densidad equivalente de depósito salino (mg/cm2).
        nsdd (float): densidad de depósito no soluble (mg/cm2).

    Returns:
        ResultadoSPS: objeto con el nivel de aceptación y la clase de
        severidad IEC asociada (usada luego por el módulo eléctrico).

    Raises:
        ValueError: si esdd o nsdd son negativos.
    """
    if esdd < 0 or nsdd < 0:
        raise ValueError("ESDD y NSDD deben ser valores no negativos.")

    nivel_esdd = _nivel_por_esdd(esdd)
    nivel_nsdd = _nivel_por_nsdd(nsdd)

    orden = {"Normal": 0, "Advertencia": 1, "Crítico": 2}
    nivel_final = max([nivel_esdd, nivel_nsdd], key=lambda n: orden[n])

    clase_severidad = _clase_severidad_iec(esdd, nsdd)

    return ResultadoSPS(nivel_final, esdd, nsdd, clase_severidad)


def _nivel_por_esdd(esdd):
    """Determina el nivel operacional según el umbral de ESDD (Tabla 3.1)."""
    if esdd < UMBRALES_CRITICIDAD["Normal"]["esdd_max"]:
        return "Normal"
    elif esdd <= UMBRALES_CRITICIDAD["Advertencia"]["esdd_max"]:
        return "Advertencia"
    else:
        return "Crítico"


def _nivel_por_nsdd(nsdd):
    """Determina el nivel operacional según el umbral de NSDD (Tabla 3.1)."""
    if nsdd < UMBRALES_CRITICIDAD["Normal"]["nsdd_max"]:
        return "Normal"
    elif nsdd <= UMBRALES_CRITICIDAD["Advertencia"]["nsdd_max"]:
        return "Advertencia"
    else:
        return "Crítico"


def _clase_severidad_iec(esdd, nsdd):
    """
    Obtiene la clase de severidad IEC de 5 niveles (muy ligero, ligero,
    medio, pesado, muy pesado) a partir de ESDD y NSDD combinados, según
    la Tabla 4.1 (IEC TS 60815-1:2008), que empareja ambos indicadores
    con el USCD y el Lmin resultante.

    Regla de combinación: se adopta el criterio más restrictivo entre
    la clase que resulta de evaluar solo ESDD y la que resulta de
    evaluar solo NSDD (misma lógica que en clasificar_sps), ya que la
    tabla normativa asocia a cada clase un rango de ESDD y un rango de
    NSDD en paralelo, no una condición conjunta explícita.

    Esta clase se usa exclusivamente para obtener el USCD en el módulo
    eléctrico (cálculo de Lmin).
    """
    orden = {"muy_ligero": 0, "ligero": 1, "medio": 2,
             "pesado": 3, "muy_pesado": 4}

    clase_esdd = _clase_por_esdd(esdd)
    clase_nsdd = _clase_por_nsdd(nsdd)

    return max([clase_esdd, clase_nsdd], key=lambda c: orden[c])


def _clase_por_esdd(esdd):
    """Clase de severidad IEC según el rango de ESDD (Tabla 4.1)."""
    if esdd < 0.01:
        return "muy_ligero"
    elif esdd <= 0.04:
        return "ligero"
    elif esdd <= 0.15:
        return "medio"
    elif esdd <= 0.40:
        return "pesado"
    else:
        return "muy_pesado"


def _clase_por_nsdd(nsdd):
    """Clase de severidad IEC según el rango de NSDD (Tabla 4.1)."""
    if nsdd < 0.03:
        return "muy_ligero"
    elif nsdd <= 0.10:
        return "ligero"
    elif nsdd <= 0.30:
        return "medio"
    elif nsdd <= 0.80:
        return "pesado"
    else:
        return "muy_pesado"


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
    de contaminante sobre el aislador.
    """
    return viento > UMBRAL_VIENTO_MS


def _evaluar_lavado_lluvia(lluvia):
    """
    Determina si la intensidad de lluvia ingresada corresponde a un
    evento de lavado natural efectivo.
    """
    return lluvia >= UMBRAL_LLUVIA_MM_DIA


# =============================================================================
# B.4 - Módulo eléctrico (Um, Uph-e, USCD, Lmin básicos)
# =============================================================================

TABLA_UM = {
    33:  36.0,
    44:  48.3,
    66:  72.5,
    110: 123.0,
    121: 145.0,
    154: 170.0,
    220: 245.0,
}


class ResultadoElectrico:
    def __init__(self, un, um, uph_e, uscd, lmin, material):
        self.un = un
        self.um = um
        self.uph_e = uph_e
        self.uscd = uscd
        self.lmin = lmin
        self.material = material

    def __repr__(self):
        return (f"ResultadoElectrico(un={self.un}, um={self.um}, "
                f"uph_e={round(self.uph_e, 2)}, uscd={self.uscd}, "
                f"lmin={round(self.lmin, 1)}, material='{self.material}')")


class ResultadoSuficiencia:
    def __init__(self, linst, lmin, suficiente):
        self.linst = linst
        self.lmin = lmin
        self.suficiente = suficiente

    def __repr__(self):
        return (f"ResultadoSuficiencia(linst={self.linst}, "
                f"lmin={round(self.lmin, 1)}, suficiente={self.suficiente})")


def calcular_modulo_electrico(un, clase_severidad, material):
    um = _obtener_um(un)
    uph_e = _calcular_uph_e(um)
    uscd = _obtener_uscd(clase_severidad)
    lmin = uscd * uph_e

    return ResultadoElectrico(un, um, uph_e, uscd, lmin, material)


def _obtener_um(un):
    if un not in TABLA_UM:
        niveles_validos = ", ".join(str(n) for n in sorted(TABLA_UM.keys()))
        raise ValueError(
            f"Un = {un} kV no corresponde a un nivel normalizado. "
            f"Niveles válidos: {niveles_validos} kV."
        )
    return TABLA_UM[un]


def _calcular_uph_e(um):
    return um / (3 ** 0.5)


def _obtener_uscd(clase_severidad):
    if clase_severidad not in USCD_POR_CLASE_SEVERIDAD:
        clases_validas = ", ".join(USCD_POR_CLASE_SEVERIDAD.keys())
        raise ValueError(
            f"Clase de severidad '{clase_severidad}' no válida. "
            f"Clases válidas: {clases_validas}."
        )
    return USCD_POR_CLASE_SEVERIDAD[clase_severidad]


def verificar_suficiencia_aislamiento(linst, lmin):
    if linst < 0:
        raise ValueError("Linst debe ser un valor no negativo.")

    return ResultadoSuficiencia(linst, lmin, linst >= lmin)


# =============================================================================
# B.5 - Módulo mecánico (perfil, Kad, Ka por altitud, s/p y CF)
# =============================================================================

PERFIL_RECOMENDADO_POR_ENTORNO = {
    "costero":    "antiniebla",
    "desertico":  "aerodinamico",
    "industrial": "alternante",
}

# Figura A.3 - Umbrales de desviación s/p para cerámico y vidrio [3].
# No distingue por diámetro de vástago, solo por presencia de nervaduras.
UMBRALES_SP_CERAMICO_VIDRIO = {
    "con_nervaduras": {"mayor_max": 0.60, "menor_max": 0.75},
    "sin_nervaduras": {"mayor_max": 0.50, "menor_max": 0.65},
}

# Figura A.4 - Umbrales de desviación s/p para poliméricos [7].
# Distingue por diámetro de vástago (<=110 mm o >110 mm) y por presencia
# de nervaduras internas.
UMBRALES_SP_POLIMERICO = {
    "diametro_menor_110": {
        "con_nervaduras": {"mayor_max": 0.70, "menor_max": 0.80},
        "sin_nervaduras": {"mayor_max": 0.60, "menor_max": 0.70},
    },
    "diametro_mayor_110": {
        "con_nervaduras": {"mayor_max": 0.50, "menor_max": 0.70},
        "sin_nervaduras": {"mayor_max": 0.50, "menor_max": 0.60},
    },
}

# Tabla 4.9 - Umbrales de desviación del factor de creepage (CF) según clase
# SPS, para aisladores cerámicos y de vidrio [7]. Aquí el límite superior de
# "desviación menor" coincide con el inicio de "desviación mayor", por lo
# que un solo valor (desviacion_menor_max) sirve como umbral de alerta.
UMBRALES_CF_CERAMICO_VIDRIO = {
    "muy_ligero": {"sin_desviacion_max": 3.50,  "desviacion_menor_max": 4.25},
    "ligero":     {"sin_desviacion_max": 3.625, "desviacion_menor_max": 4.40},
    "medio":      {"sin_desviacion_max": 3.75,  "desviacion_menor_max": 4.55},
    "pesado":     {"sin_desviacion_max": 3.875, "desviacion_menor_max": 4.70},
    "muy_pesado": {"sin_desviacion_max": 4.00,  "desviacion_menor_max": 4.85},
}


UMBRALES_CF_POLIMERICO = {
    "muy_ligero": {"desviacion_menor_max": 4.25, "desviacion_mayor_max": 5.00},
    "ligero":     {"desviacion_menor_max": 4.35, "desviacion_mayor_max": 5.00},
    "medio":      {"desviacion_menor_max": 4.45, "desviacion_mayor_max": 5.00},
    "pesado":     {"desviacion_menor_max": 4.65, "desviacion_mayor_max": 5.00},
    "muy_pesado": {"desviacion_menor_max": 4.80, "desviacion_mayor_max": 5.00},
}


KAD_POLIMERICO_DA_MIN = 300        # mm, punto de convergencia (Kad = 1.0)
KAD_POLIMERICO_VALOR_MIN = 1.0     # Kad en Da_min, común a las tres curvas
KAD_POLIMERICO_VALOR_MAX = 1.3     # Kad máximo graficado en Fig. A.1

CURVAS_KAD_POLIMERICO = {
    "hidrofobico":            {"da_max": None},   # curva plana, Kad = 1.0 siempre
    "sin_transferencia":      {"da_max": 600},     # llega a 1.3 en Da = 600 mm
    "perdida_hidrofobicidad": {"da_max": 1000},    # llega a 1.3 en Da = 1000 mm
}

ESTADO_HIDROFOBICIDAD_DEFAULT = "sin_transferencia"

# Bajo este umbral se adopta Ka = 1,0; sobre él se aplica la Ecuación A.1 del anexo.
UMBRAL_ALTITUD_KA = 1000  # msnm

# Exponente m de la Ecuación A.1, según perfil del aislador (IEC 60071-2).
# El perfil antiniebla usa m = 0,8; el resto de los perfiles (estándar,
# aerodinámico, alternante) usa m = 0,5 como valor por defecto.
EXPONENTE_M_PERFIL = {
    "antiniebla": 0.8,
}
EXPONENTE_M_DEFAULT = 0.5


class ResultadoMecanico:

    def __init__(self, perfil_ok, perfil_recomendado, da, kad, ka,
                 ka_aplicado, alerta_sp, cf, alerta_cf):
        self.perfil_ok = perfil_ok
        self.perfil_recomendado = perfil_recomendado
        self.da = da
        self.kad = kad
        self.ka = ka
        self.ka_aplicado = ka_aplicado
        self.alerta_sp = alerta_sp
        self.cf = cf
        self.alerta_cf = alerta_cf

    def __repr__(self):
        return (f"ResultadoMecanico(perfil_ok={self.perfil_ok}, "
                f"perfil_recomendado='{self.perfil_recomendado}', "
                f"da={round(self.da, 1)}, kad={round(self.kad, 4)}, "
                f"ka={round(self.ka, 4)}, ka_aplicado={self.ka_aplicado}, "
                f"alerta_sp={self.alerta_sp}, cf={round(self.cf, 3)}, "
                f"alerta_cf={self.alerta_cf})")


def calcular_ka_altitud(altitud, perfil):
    if altitud < 0:
        raise ValueError("La altitud debe ser un valor no negativo.")

    if altitud <= UMBRAL_ALTITUD_KA:
        return 1.0

    m = EXPONENTE_M_PERFIL.get(perfil, EXPONENTE_M_DEFAULT)
    return math.exp(m * altitud / 8150)


def evaluar_modulo_mecanico(material, entorno, perfil, dt, ds1, ds2,
                             s_aleta, p, linst, s_arco, altitud,
                             clase_severidad, con_nervaduras=True,
                             diametro_vastago=None,
                             estado_hidrofobicidad=ESTADO_HIDROFOBICIDAD_DEFAULT):

    if material not in ("ceramico", "vidrio", "polimerico"):
        raise ValueError(
            f"Material '{material}' no válido. Debe ser 'ceramico', "
            f"'vidrio' o 'polimerico'."
        )
    if entorno not in PERFIL_RECOMENDADO_POR_ENTORNO:
        raise ValueError(
            f"Entorno '{entorno}' no válido. Debe ser 'costero', "
            f"'desertico' o 'industrial'."
        )
    if min(dt, ds1, ds2, s_aleta, p, linst) < 0:
        raise ValueError("Los parámetros geométricos y Linst deben ser "
                          "no negativos.")
    if s_arco <= 0:
        raise ValueError(
            "La distancia de arco S debe ser mayor que 0, ya que CF se "
            "calcula como Linst / S (Ecuación 4.7)."
        )
    if altitud < 0:
        raise ValueError("La altitud debe ser un valor no negativo.")
    if material == "polimerico" and diametro_vastago is None:
        raise ValueError(
            "diametro_vastago es obligatorio para aisladores poliméricos "
            "(Figura A.3)."
        )
    if material == "polimerico" and estado_hidrofobicidad not in CURVAS_KAD_POLIMERICO:
        estados_validos = ", ".join(CURVAS_KAD_POLIMERICO.keys())
        raise ValueError(
            f"estado_hidrofobicidad '{estado_hidrofobicidad}' no válido. "
            f"Debe ser uno de: {estados_validos}."
        )

    perfil_recomendado = PERFIL_RECOMENDADO_POR_ENTORNO[entorno]
    perfil_ok = _evaluar_perfil_ok(perfil, entorno)

    # Da se calcula con la misma fórmula (Ecuación 4.5) para los 3 materiales
    da = _calcular_da(dt, ds1, ds2)

    # Solo el criterio de Kad difiere por material (expresión cerrada vs.
    # curvas de hidrofobicidad).
    kad = _calcular_kad(da, material, estado_hidrofobicidad)

    ka = calcular_ka_altitud(altitud, perfil)
    ka_aplicado = altitud > UMBRAL_ALTITUD_KA

    sp = s_aleta / p
    alerta_sp = _evaluar_sp(sp, material, con_nervaduras, diametro_vastago)

    cf = _calcular_cf(linst, s_arco)
    alerta_cf = _evaluar_cf(cf, material, clase_severidad)

    return ResultadoMecanico(perfil_ok, perfil_recomendado, da, kad, ka,
                              ka_aplicado, alerta_sp, cf, alerta_cf)


def _evaluar_perfil_ok(perfil, entorno):

    if perfil == "alternante":
        return True
    return perfil == PERFIL_RECOMENDADO_POR_ENTORNO[entorno]


def _calcular_da(dt, ds1, ds2):
    """
    Calcula el diámetro promedio del aislador Da, según la Ecuación 4.5
    """
    return (2 * dt + ds1 + ds2) / 4


def _calcular_kad(da, material, estado_hidrofobicidad=ESTADO_HIDROFOBICIDAD_DEFAULT):
    """
    Calcula el factor de corrección Kad según el diámetro promedio del
    aislador Da, según la Ecuación 4.4 - IEC/TS 60815-2:2008.
    """
    if material in ("ceramico", "vidrio"):
        if da < 300:
            return 1.0
        return 0.0005 * da + 0.85

    # material == "polimerico"
    if da < KAD_POLIMERICO_DA_MIN:
        return 1.0

    curva = CURVAS_KAD_POLIMERICO[estado_hidrofobicidad]
    da_max = curva["da_max"]

    if da_max is None:  # "hidrofobico": curva plana
        return 1.0

    if da >= da_max:
        return KAD_POLIMERICO_VALOR_MAX

    pendiente = ((KAD_POLIMERICO_VALOR_MAX - KAD_POLIMERICO_VALOR_MIN) /
                 (da_max - KAD_POLIMERICO_DA_MIN))
    return KAD_POLIMERICO_VALOR_MIN + pendiente * (da - KAD_POLIMERICO_DA_MIN)


def _evaluar_sp(sp, material, con_nervaduras, diametro_vastago):
    """
    Evalúa la razón espaciado-vuelo de aleta (s/p, Ecuación 4.6) contra los umbrales de
    desviación del material correspondiente.

    Returns:
        bool: True si sp cae en zona de desviación mayor para la
        combinación material/configuración indicada.
    """
    if material in ("ceramico", "vidrio"):
        clave = "con_nervaduras" if con_nervaduras else "sin_nervaduras"
        umbral_mayor = UMBRALES_SP_CERAMICO_VIDRIO[clave]["mayor_max"]
        return sp < umbral_mayor

    # material == "polimerico"
    grupo_diametro = ("diametro_menor_110" if diametro_vastago <= 110
                       else "diametro_mayor_110")
    clave = "con_nervaduras" if con_nervaduras else "sin_nervaduras"
    umbral_mayor = UMBRALES_SP_POLIMERICO[grupo_diametro][clave]["mayor_max"]
    return sp < umbral_mayor


def _calcular_cf(linst, s_arco):
    """
    Calcula el factor de creepage CF = Linst / S (Ecuación 4.7), según lo
    descrito en la Sección 4.2.3.4.
    """
    return linst / s_arco


def _evaluar_cf(cf, material, clase_severidad):
    """
    Evalúa el factor de creepage (CF) contra el umbral de desviación
    mayor del material correspondiente.

    - Cerámico/vidrio (Tabla 4.9): el límite superior del rango de
      "desviación menor" coincide con el inicio de "desviación mayor",
      por lo que un único valor (desviacion_menor_max) sirve como
      umbral de alerta.
    - Polimérico (Tabla A.1): "desviación menor" (CF <=, propio de cada
      clase SPS) y "desviación mayor" (CF >, fijo en 5,00 para las cinco
      clases) son umbrales distintos. La alerta de CF debe evaluarse
      contra desviacion_mayor_max, no contra desviacion_menor_max.
    """
    if material in ("ceramico", "vidrio"):
        tabla = UMBRALES_CF_CERAMICO_VIDRIO
        if clase_severidad not in tabla:
            raise ValueError(f"Clase de severidad '{clase_severidad}' no válida.")
        umbral_mayor = tabla[clase_severidad]["desviacion_menor_max"]

    else:  # material == "polimerico"
        tabla = UMBRALES_CF_POLIMERICO
        if clase_severidad not in tabla:
            raise ValueError(f"Clase de severidad '{clase_severidad}' no válida.")
        umbral_mayor = tabla[clase_severidad]["desviacion_mayor_max"]

    return cf > umbral_mayor


def calcular_lmin_corregido(resultado_electrico, resultado_mecanico):
    """
    Aplica la corrección Kad · Ka al Lmin básico (Ecuación 4.4/4.5 y
    Sección 4.2.4 - Ka por altitud), y calcula también el USCD corregido
    equivalente (USCD_corregido = RUSCD * Kad * Ka, Ecuación 4.3).
    """
    kad = resultado_mecanico.kad
    ka = resultado_mecanico.ka

    if kad is None:
        return resultado_electrico.lmin, resultado_electrico.uscd, False

    uscd_corregido = resultado_electrico.uscd * kad * ka
    lmin_corregido = resultado_electrico.lmin * kad * ka
    return lmin_corregido, uscd_corregido, True


# =============================================================================
# B.6 - Módulo de integración de resultados y generación de recomendaciones
# =============================================================================

NOTA_MATERIAL = {
    "ceramico": (
        "Dada la superficie hidrófila del material, se prioriza lavado de "
        "alta presión y/o recubrimiento RTV (Tabla 4.6)."
    ),
    "vidrio": (
        "Dada la superficie hidrófila del material, se prioriza lavado de "
        "alta presión y/o recubrimiento RTV (Tabla 4.6)."
    ),
    "polimerico": (
        "Dada la hidrofobicidad del material, se recomienda lavado según "
        "indicación del fabricante, reservando la intervención para casos "
        "de degradación de la hidrofobicidad por UV o contaminación "
        "industrial severa (Tabla 4.6)."
    ),
}


class ResultadoFinal:
    """
    Resultado  que entrega la herramienta (Sección 5.2).

    Además del nivel de aceptación, la medida recomendada y las alertas,
    este objeto expone explícitamente:
      - El USCD y el Lmin BÁSICOS (según clase de severidad, sin corregir).
      - El USCD y el Lmin CORREGIDOS (tras aplicar Kad y Ka) -- este
        último es la distancia de fuga mínima real y definitiva contra la
        que se verifica Linst.
      - Los factores Kad y Ka aplicados, indicando si Ka realmente se
        calculó (altitud > 1000 msnm) o se dejó en 1,0 por defecto.
      - El valor de CF y si se encuentra dentro o fuera de rango.
      - Los indicadores ambientales, con su significado.
    """

    def __init__(self, nivel, medida_recomendada, aislamiento_suficiente,
                 alertas, indicadores_ambientales, uscd_basico,
                 uscd_corregido, lmin_basico, lmin_corregido, linst,
                 kad, ka, ka_aplicado, cf, alerta_cf):
        self.nivel = nivel
        self.medida_recomendada = medida_recomendada
        self.aislamiento_suficiente = aislamiento_suficiente
        self.alertas = alertas
        self.indicadores_ambientales = indicadores_ambientales
        self.uscd_basico = uscd_basico
        self.uscd_corregido = uscd_corregido
        self.lmin_basico = lmin_basico
        self.lmin_corregido = lmin_corregido
        self.linst = linst
        self.kad = kad
        self.ka = ka
        self.ka_aplicado = ka_aplicado
        self.cf = cf
        self.alerta_cf = alerta_cf

    def __repr__(self):
        return (f"ResultadoFinal(nivel='{self.nivel}', "
                f"aislamiento_suficiente={self.aislamiento_suficiente}, "
                f"n_alertas={len(self.alertas)})")

    def resumen(self):
        def si_no(valor):
            return "Sí" if valor else "No"

        lineas = [
            f"Nivel de aceptación operacional: {self.nivel}",
            f"Medida recomendada: {self.medida_recomendada}",
            "",
            "--- Distancia de fuga (USCD y Lmin) ---",
            f"USCD básico (según clase de severidad, sin corregir): "
            f"{self.uscd_basico:.2f} mm/kV",
            f"USCD corregido (Kad x Ka): {self.uscd_corregido:.2f} mm/kV",
            f"Lmin básico (sin corregir): {self.lmin_basico:.1f} mm",
            f"Lmin corregido (distancia de fuga mínima REAL requerida): "
            f"{self.lmin_corregido:.1f} mm",
            f"Linst (instalada): {self.linst:.1f} mm",
            f"Aislamiento suficiente (Linst >= Lmin corregido): "
            f"{si_no(self.aislamiento_suficiente)}",
            "",
            "--- Factores de corrección aplicados ---",
            f"Kad (corrección por diámetro promedio Da): {self.kad:.4f}",
            f"Ka (corrección por altitud): {self.ka:.4f} -- "
            + ("aplicado: sitio sobre 1000 msnm, se calculó mediante la "
               "Ecuación A.1 del anexo" if self.ka_aplicado else
               "no aplicado: sitio a 1000 msnm o menos, se adopta Ka=1,0 "
               "por defecto (Sección 5.3.6)"),
            "",
            "--- Factor de creepage (CF) ---",
            f"CF = Linst / S = {self.cf:.3f}",
            "Estado: " + (
                "FUERA de rango normativo -> riesgo de arcos localizados "
                "por densidad de distancia de fuga insuficiente sobre una "
                "geometría demasiado concentrada."
                if self.alerta_cf else
                "dentro de rango normativo -> sin riesgo de arcos "
                "localizados por concentración excesiva de distancia de "
                "fuga."
            ),
            "",
            "--- Indicadores ambientales ---",
        ]

        for clave, valor in self.indicadores_ambientales.items():
            explicacion = EXPLICACION_INDICADOR_AMBIENTAL[clave]
            lineas.append(f"{explicacion}: {si_no(valor)}")

        lineas.append("")
        if self.alertas:
            lineas.append("Alertas activadas:")
            lineas.extend(f"  - {a}" for a in self.alertas)
        else:
            lineas.append("Sin alertas adicionales de perfil, geometría o "
                           "distancia de fuga.")
        return "\n".join(lineas)


def integrar_resultados(resultado_sps, resultado_ambiental, resultado_electrico,
                         resultado_mecanico, resultado_suficiencia,
                         lmin_corregido, uscd_corregido, material, entorno,
                         kad_aplicado=True):
    if material not in NOTA_MATERIAL:
        raise ValueError(
            f"Material '{material}' no válido. Debe ser 'ceramico', "
            f"'vidrio' o 'polimerico'."
        )

    medida = _medida_recomendada(
        resultado_sps.nivel, resultado_ambiental.activacion_hr, material
    )

    alertas = _generar_alertas(
        resultado_suficiencia, resultado_mecanico, resultado_ambiental,
        entorno, kad_aplicado
    )

    indicadores_ambientales = {
        "activacion_hr": resultado_ambiental.activacion_hr,
        "acumulacion_viento": resultado_ambiental.acumulacion_viento,
        "lavado_lluvia": resultado_ambiental.lavado_lluvia,
    }

    return ResultadoFinal(
        nivel=resultado_sps.nivel,
        medida_recomendada=medida,
        aislamiento_suficiente=resultado_suficiencia.suficiente,
        alertas=alertas,
        indicadores_ambientales=indicadores_ambientales,
        uscd_basico=resultado_electrico.uscd,
        uscd_corregido=uscd_corregido,
        lmin_basico=resultado_electrico.lmin,
        lmin_corregido=lmin_corregido,
        linst=resultado_suficiencia.linst,
        kad=resultado_mecanico.kad,
        ka=resultado_mecanico.ka,
        ka_aplicado=resultado_mecanico.ka_aplicado,
        cf=resultado_mecanico.cf,
        alerta_cf=resultado_mecanico.alerta_cf,
    )


def _medida_recomendada(nivel, activacion_hr, material):
    if nivel == "Normal":
        return "Monitoreo periódico. Sin intervención urgente."

    if nivel == "Advertencia":
        if activacion_hr:
            base = ("Adelantar intervención: lavado o recubrimiento RTV "
                     "de forma prioritaria.")
        else:
            base = ("Programar lavados preventivos y evaluar aplicación "
                     "de recubrimiento hidrofóbico.")
        return f"{base} {NOTA_MATERIAL[material]}"

    if nivel == "Crítico":
        base = ("Intervención inmediata: limpieza de emergencia y "
                "recubrimiento RTV; si persiste el riesgo, evaluar "
                "sustitución o redimensionamiento del aislamiento.")
        return f"{base} {NOTA_MATERIAL[material]}"

    raise ValueError(f"Nivel '{nivel}' no reconocido.")


def _generar_alertas(resultado_suficiencia, resultado_mecanico,
                      resultado_ambiental, entorno, kad_aplicado=True):
    alertas = []

    if not kad_aplicado:
        alertas.append(
            "Corrección Kad no disponible: no fue posible determinar el "
            "factor de corrección por diámetro para el material y "
            "configuración indicados. El Lmin utilizado corresponde al "
            "valor básico sin corregir por diámetro."
        )

    if not resultado_suficiencia.suficiente:
        alertas.append(
            "Aislamiento subdimensionado: Linst < Lmin. Se requiere "
            "redimensionamiento o reemplazo por un aislador con mayor "
            "distancia de fuga."
        )

    if not resultado_mecanico.perfil_ok:
        alertas.append(
            f"Perfil instalado no corresponde al recomendado para el "
            f"entorno '{entorno}' (perfil recomendado: "
            f"{resultado_mecanico.perfil_recomendado})."
        )

    if resultado_mecanico.alerta_sp and resultado_ambiental.activacion_hr:
        alertas.append(
            "Riesgo de puente entre aletas por formación de película de "
            "agua continua bajo condiciones de humedad crítica del "
            "entorno (razón s/p en zona de desviación mayor)."
        )
    elif resultado_mecanico.alerta_sp and not resultado_ambiental.activacion_hr:
        alertas.append(
            "Razón s/p en zona de desviación mayor, sin activación de "
            "humedad relativa en el entorno actual: sin riesgo inmediato "
            "de puente entre aletas, pero la geometría queda fuera del "
            "rango recomendado ."
        )

    if resultado_mecanico.alerta_cf:
        alertas.append(
            f"Factor de creepage (CF = {resultado_mecanico.cf:.2f}) fuera "
            f"de los umbrales normativos: riesgo de arcos localizados por "
            f"densidad de distancia de fuga insuficiente."
        )

    return alertas


def evaluar_sitio(esdd, nsdd, entorno, hr, viento, lluvia, un, linst,
                   material, perfil, dt, ds1, ds2, s_aleta, p, s_arco,
                   altitud, con_nervaduras=True, diametro_vastago=None,
                   estado_hidrofobicidad="sin_transferencia"):
    """
     'estado_hidrofobicidad': solo tiene efecto cuando
    material == "polimerico"; determina qué curva de la Figura A.1 se
    usa para el factor Kad en el módulo mecánico (B.5). Si no se conoce
    el estado real del polimérico, se mantiene el default
    "sin_transferencia" (Non-HTM).

     'altitud': variable MECÁNICA. Se
    recibe en msnm y se utiliza dentro de evaluar_modulo_mecanico para
    calcular el factor Ka (Sección 5.3.6). Para altitud <= 1000 msnm,
    Ka = 1,0; sobre ese umbral se aplica la Ecuación A.1 con el
    exponente correspondiente al perfil del aislador.

     's_aleta' y 's_arco': no se solicita 'cf' como dato de
    entrada directo (Sección 4.2.3.4). 's_aleta' es el espaciado entre
    aletas (símbolo "s" en la razón s/p); 's_arco' es la distancia de
    arco (símbolo "S" en la norma, usada junto con Linst para calcular
    CF = Linst / S dentro del módulo mecánico, B.5). Ambos parámetros se
    mantienen separados para evitar confundir dos variables normativas
    distintas que comparten letra.
    """
    resultado_sps = clasificar_sps(esdd, nsdd)

    resultado_ambiental = evaluar_modulo_ambiental(entorno, hr, viento, lluvia)

    resultado_electrico = calcular_modulo_electrico(
        un, resultado_sps.clase_severidad, material
    )

    resultado_mecanico = evaluar_modulo_mecanico(
        resultado_electrico.material, entorno, perfil, dt, ds1, ds2,
        s_aleta, p, linst, s_arco, altitud, resultado_sps.clase_severidad,
        con_nervaduras=con_nervaduras, diametro_vastago=diametro_vastago,
        estado_hidrofobicidad=estado_hidrofobicidad
    )

    lmin_final, uscd_final, kad_aplicado = calcular_lmin_corregido(
        resultado_electrico, resultado_mecanico
    )

    resultado_suficiencia = verificar_suficiencia_aislamiento(
        linst, lmin_final
    )

    return integrar_resultados(
        resultado_sps, resultado_ambiental, resultado_electrico,
        resultado_mecanico, resultado_suficiencia, lmin_final, uscd_final,
        material, entorno, kad_aplicado=kad_aplicado
    )

# =============================================================================
# B.7 - Módulo de graficación de resultados
# =============================================================================
"""
Funciones de visualización para acompañar la salida de la herramienta
computacional (Sección 5.4 / Capítulo 6). Generan tres tipos de gráfico:

1. Mapa de clasificación ESDD-NSDD (zonas Normal/Advertencia/Crítico según
   Tabla 3.1), con los escenarios evaluados marcados como puntos.
2. Comparación de Lmin básico, Lmin corregido y Linst para un caso de
   aplicación, por nivel de tensión.
3. Estado de las alertas mecánicas activadas en un caso de aplicación.

Requiere matplotlib (pip install matplotlib).
"""


COLOR_NIVEL = {
    "Normal": "#c8e6c9",
    "Advertencia": "#fff9c4",
    "Crítico": "#ffcdd2",
}
COLOR_BORDE = {
    "Normal": "#2e7d32",
    "Advertencia": "#f9a825",
    "Crítico": "#c62828",
}


def graficar_mapa_clasificacion(escenarios=None, esdd_max=0.30, nsdd_max=0.60,
                                 guardar_en=None):
    """
    Genera el mapa de clasificación ESDD-NSDD con las zonas Normal,
    Advertencia y Crítico según los umbrales de la Tabla 3.1, análogo en
    concepto a la Figura 1/2 de IEC TS 60815-1:2008 pero construido con
    los umbrales operacionales adoptados en el presente trabajo.

    Args:
        escenarios (list[dict], optional): lista de escenarios a marcar
            sobre el mapa. Cada dict debe tener las llaves "nombre",
            "esdd" y "nsdd". Si es None, no se marcan puntos.
        esdd_max (float): límite superior del eje ESDD para el gráfico.
        nsdd_max (float): límite superior del eje NSDD para el gráfico.
        guardar_en (str, optional): ruta donde guardar la figura (png).
            Si es None, no se guarda a disco.

    Returns:
        matplotlib.figure.Figure: la figura generada.
    """
    fig, ax = plt.subplots(figsize=(7, 5.5))

    # Umbrales de la Tabla 3.1
    esdd_normal, esdd_advertencia = 0.04, 0.15
    nsdd_normal, nsdd_advertencia = 0.10, 0.30

    # Zona Crítico: todo el plano (se dibuja primero, de fondo)
    ax.add_patch(mpatches.Rectangle(
        (0, 0), esdd_max, nsdd_max,
        facecolor=COLOR_NIVEL["Crítico"], zorder=0))

    # Zona Advertencia
    ax.add_patch(mpatches.Rectangle(
        (0, 0), esdd_advertencia, nsdd_advertencia,
        facecolor=COLOR_NIVEL["Advertencia"], zorder=1))

    # Zona Normal
    ax.add_patch(mpatches.Rectangle(
        (0, 0), esdd_normal, nsdd_normal,
        facecolor=COLOR_NIVEL["Normal"], zorder=2))

    # Líneas de umbral
    ax.axvline(esdd_normal, color=COLOR_BORDE["Normal"],
               linestyle="--", linewidth=1)
    ax.axvline(esdd_advertencia, color=COLOR_BORDE["Advertencia"],
               linestyle="--", linewidth=1)
    ax.axhline(nsdd_normal, color=COLOR_BORDE["Normal"],
               linestyle="--", linewidth=1)
    ax.axhline(nsdd_advertencia, color=COLOR_BORDE["Advertencia"],
               linestyle="--", linewidth=1)

    # Escenarios marcados
    if escenarios:
        for esc in escenarios:
            ax.plot(esc["esdd"], esc["nsdd"], marker="o", markersize=9,
                    markerfacecolor="black", markeredgecolor="white",
                    markeredgewidth=1.2, zorder=5)
            ax.annotate(
                esc["nombre"], (esc["esdd"], esc["nsdd"]),
                textcoords="offset points", xytext=(8, 6),
                fontsize=9, fontweight="bold", zorder=6
            )

    ax.set_xlim(0, esdd_max)
    ax.set_ylim(0, nsdd_max)
    ax.set_xlabel("ESDD (mg/cm²)")
    ax.set_ylabel("NSDD (mg/cm²)")
    ax.set_title("Mapa de clasificación operacional según ESDD/NSDD\n"
                  "(umbrales Tabla 3.1)")

    leyenda = [
        mpatches.Patch(facecolor=COLOR_NIVEL["Normal"], label="Normal"),
        mpatches.Patch(facecolor=COLOR_NIVEL["Advertencia"], label="Advertencia"),
        mpatches.Patch(facecolor=COLOR_NIVEL["Crítico"], label="Crítico"),
    ]
    ax.legend(handles=leyenda, loc="upper right", framealpha=0.9)
    fig.tight_layout()

    if guardar_en:
        fig.savefig(guardar_en, dpi=200, bbox_inches="tight")

    return fig


def graficar_comparacion_lmin(un, lmin_basico, lmin_corregido, linst,
                               nombre_caso="Caso de aplicación",
                               guardar_en=None):
    """
    Genera un gráfico de barras comparando Lmin básico, Lmin corregido
    (Kad, Ka) y Linst para un caso de aplicación, según el nivel de
    tensión del sitio evaluado (Sección 4.2.2.1, 4.2.3.2 y 4.2.2.2).

    Args:
        un (float or int): tensión nominal del sistema evaluado (kV),
            solo para el título del gráfico.
        lmin_basico (float): Lmin obtenido en calcular_modulo_electrico (mm).
        lmin_corregido (float): Lmin obtenido en calcular_lmin_corregido (mm).
        linst (float): distancia de fuga instalada del caso evaluado (mm).
        nombre_caso (str): nombre descriptivo del caso, usado en el título.
        guardar_en (str, optional): ruta donde guardar la figura (png).

    Returns:
        matplotlib.figure.Figure: la figura generada.
    """
    etiquetas = ["Lmin básico\n(USCD sin corregir)",
                 "Lmin corregido\n(Kad · Ka)",
                 "Linst\n(instalada)"]
    valores = [lmin_basico, lmin_corregido, linst]
    colores = ["#90a4ae", "#5c6bc0", "#43a047" if linst >= lmin_corregido
               else "#e53935"]

    fig, ax = plt.subplots(figsize=(6.5, 5))
    barras = ax.bar(etiquetas, valores, color=colores, edgecolor="black",
                     linewidth=0.8)

    for barra, valor in zip(barras, valores):
        ax.text(barra.get_x() + barra.get_width() / 2, valor + 30,
                f"{valor:,.0f} mm", ha="center", fontsize=9)

    ax.set_ylabel("Distancia de fuga (mm)")
    ax.set_title(f"{nombre_caso} — Un = {un} kV\n"
                  f"Verificación Linst ≥ Lmin: "
                  f"{'Suficiente' if linst >= lmin_corregido else 'Insuficiente'}")
    ax.set_ylim(0, max(valores) * 1.2)
    fig.tight_layout()

    if guardar_en:
        fig.savefig(guardar_en, dpi=200, bbox_inches="tight")

    return fig


def graficar_alertas_mecanicas(resultado_mecanico, resultado_suficiencia,
                                nombre_caso="Caso de aplicación",
                                guardar_en=None):
    """
    Genera un gráfico de barras horizontal mostrando el estado (OK /
    Alerta) de las cuatro verificaciones que aporta al resultado final:
    suficiencia de Linst, perfil, razón s/p y factor de creepage (CF),
    según lo integrado en B.6 (_generar_alertas).

    Args:
        resultado_mecanico (ResultadoMecanico): resultado del módulo B.5.
        resultado_suficiencia (ResultadoSuficiencia): resultado de
            verificar_suficiencia_aislamiento (B.4).
        nombre_caso (str): nombre descriptivo del caso, usado en el título.
        guardar_en (str, optional): ruta donde guardar la figura (png).

    Returns:
        matplotlib.figure.Figure: la figura generada.
    """
    verificaciones = ["Distancia de fuga\n(Linst ≥ Lmin)",
                       "Perfil del aislador",
                       "Razón s/p",
                       "Factor de creepage (CF)"]
    estados_ok = [
        resultado_suficiencia.suficiente,
        resultado_mecanico.perfil_ok,
        not resultado_mecanico.alerta_sp,
        not resultado_mecanico.alerta_cf,
    ]
    colores = ["#43a047" if ok else "#e53935" for ok in estados_ok]
    valores = [1] * len(verificaciones)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.barh(verificaciones, valores, color=colores, edgecolor="black",
            linewidth=0.8)

    for i, ok in enumerate(estados_ok):
        ax.text(0.5, i, "OK" if ok else "ALERTA", ha="center", va="center",
                fontsize=10, fontweight="bold", color="white")

    ax.set_xlim(0, 1)
    ax.set_xticks([])
    ax.set_title(f"{nombre_caso}\nEstado de verificaciones mecánicas y eléctricas")
    fig.tight_layout()

    if guardar_en:
        fig.savefig(guardar_en, dpi=200, bbox_inches="tight")

    return fig


# =============================================================================
# B.8 - CLI interactivo
# =============================================================================



def _pedir_float(mensaje, minimo=None):
    while True:
        try:
            valor = float(input(mensaje).replace(",", "."))
            if minimo is not None and valor < minimo:
                print(f"  -> El valor debe ser >= {minimo}. Intenta de nuevo.")
                continue
            return valor
        except ValueError:
            print("  -> Ingresa un número válido.")


def _pedir_opcion(mensaje, opciones):
    opciones_str = "/".join(opciones)
    while True:
        valor = input(f"{mensaje} ({opciones_str}): ").strip().lower()
        if valor in opciones:
            return valor
        print(f"  -> Opción no válida. Debe ser una de: {opciones_str}.")


def _pedir_int(mensaje, opciones=None):
    while True:
        try:
            valor = int(input(mensaje))
            if opciones is not None and valor not in opciones:
                print(f"  -> Debe ser uno de: {sorted(opciones)}.")
                continue
            return valor
        except ValueError:
            print("  -> Ingresa un número entero válido.")


def ejecutar_cli():
    print("=" * 70)
    print(" HERRAMIENTA DE CLASIFICACIÓN SPS - AISLADORES AT (ESDD/NSDD)")
    print(" IEC TS 60815-1/2/3:2008")
    print("=" * 70)

    print("\n--- Datos de contaminación (ESDD/NSDD) ---")
    esdd = _pedir_float("ESDD (mg/cm2): ", minimo=0)
    nsdd = _pedir_float("NSDD (mg/cm2): ", minimo=0)

    print("\n--- Datos ambientales ---")
    entorno = _pedir_opcion("Entorno", ["costero", "desertico", "industrial"])
    hr = _pedir_float("Humedad relativa promedio (%): ", minimo=0)
    viento = _pedir_float("Velocidad de viento promedio (m/s): ", minimo=0)
    lluvia = _pedir_float("Intensidad de lluvia de referencia (mm/dia): ", minimo=0)

    print("\n--- Datos eléctricos ---")
    un = _pedir_int("Tensión nominal Un (kV) [33/44/66/110/121/154/220]: ",
                     opciones=set(TABLA_UM.keys()))
    linst = _pedir_float("Distancia de fuga instalada Linst (mm): ", minimo=0)
    material = _pedir_opcion("Tipo de aislador instalado (material)",
                              ["ceramico", "vidrio", "polimerico"])

    print("\n--- Datos mecánicos ---")
    altitud = _pedir_float("Altitud del sitio (msnm): ", minimo=0)
    perfil = _pedir_opcion("Perfil instalado",
                            ["estandar", "aerodinamico", "antiniebla", "alternante"])
    dt = _pedir_float("Diámetro del tronco Dt (mm): ", minimo=0)
    ds1 = _pedir_float("Diámetro aleta superior Ds1 (mm): ", minimo=0)
    ds2 = _pedir_float("Diámetro aleta inferior Ds2 (mm): ", minimo=0)
    s_aleta = _pedir_float("Espaciado entre aletas s (mm): ", minimo=0)
    p = _pedir_float("Vuelo de aleta p (mm): ", minimo=0)
    s_arco = _pedir_float("Distancia de arco S (mm): ", minimo=0.0001)

    diametro_vastago = None
    estado_hidrofobicidad = "sin_transferencia"
    if material == "polimerico":
        diametro_vastago = _pedir_float("Diámetro del vástago (mm): ", minimo=0)
        estado_hidrofobicidad = _pedir_opcion(
            "Estado de hidrofobicidad del polimérico",
            ["hidrofobico", "sin_transferencia", "perdida_hidrofobicidad"]
        )

    con_nervaduras_str = _pedir_opcion(
        "¿El aislador presenta nervaduras internas (under-ribs)?", ["si", "no"]
    )
    con_nervaduras = (con_nervaduras_str == "si")

    resultado = evaluar_sitio(
        esdd=esdd, nsdd=nsdd, entorno=entorno, hr=hr, viento=viento,
        lluvia=lluvia, un=un, linst=linst, material=material, perfil=perfil,
        dt=dt, ds1=ds1, ds2=ds2, s_aleta=s_aleta, p=p, s_arco=s_arco,
        altitud=altitud, con_nervaduras=con_nervaduras,
        diametro_vastago=diametro_vastago,
        estado_hidrofobicidad=estado_hidrofobicidad
    )

    print("\n" + "=" * 70)
    print(" RESULTADO")
    print("=" * 70)
    print(resultado.resumen())

    graficar_str = _pedir_opcion(
        "\n¿Generar gráficos de resultados (mapa, Lmin, alertas)?", ["si", "no"]
    )
    if graficar_str == "si":
        resultado_sps = clasificar_sps(esdd, nsdd)
        resultado_electrico = calcular_modulo_electrico(
            un, resultado_sps.clase_severidad, material
        )
        resultado_mecanico = evaluar_modulo_mecanico(
            material, entorno, perfil, dt, ds1, ds2, s_aleta, p, linst,
            s_arco, altitud, resultado_sps.clase_severidad,
            con_nervaduras=con_nervaduras, diametro_vastago=diametro_vastago,
            estado_hidrofobicidad=estado_hidrofobicidad
        )
        lmin_corregido, uscd_corregido, _ = calcular_lmin_corregido(
            resultado_electrico, resultado_mecanico
        )
        resultado_suficiencia = verificar_suficiencia_aislamiento(
            linst, lmin_corregido
        )

        graficar_mapa_clasificacion(
            escenarios=[{"nombre": "Caso ingresado", "esdd": esdd, "nsdd": nsdd}],
            guardar_en="mapa_clasificacion.png"
        )
        graficar_comparacion_lmin(
            un=un, lmin_basico=resultado_electrico.lmin,
            lmin_corregido=lmin_corregido, linst=linst,
            guardar_en="comparacion_lmin.png"
        )
        graficar_alertas_mecanicas(
            resultado_mecanico, resultado_suficiencia,
            guardar_en="alertas_mecanicas.png"
        )
        print("\nGráficos guardados en la carpeta actual:")
        print("  - mapa_clasificacion.png")
        print("  - comparacion_lmin.png")
        print("  - alertas_mecanicas.png")
        plt.show()

    return resultado


if __name__ == "__main__":
    ejecutar_cli()