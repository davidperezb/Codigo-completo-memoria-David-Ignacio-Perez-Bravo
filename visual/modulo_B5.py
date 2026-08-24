
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

# Tabla A.1 - Umbrales de desviación del factor de creepage (CF) para
# aisladores poliméricos, obtenidos por lectura gráfica de la Figura A.4
# (Umbrales del factor de creepage para poliméricos).
#
# CORRECCIÓN: a diferencia de cerámico/vidrio, para poliméricos el límite
# de "desviación menor" (CF <=, distinto por clase SPS) y el de
# "desviación mayor" (CF >, fijo en 5,00 para las cinco clases) son dos
# umbrales independientes, no el mismo valor. La versión anterior de la
# herramienta usaba por error "desviacion_menor_max" también como umbral
# de alerta para poliméricos, disparando la alerta de CF prematuramente
# (p. ej. en CF = 4,45 para clase "medio", en vez de en CF = 5,00).
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
            "calcula como Linst / S (Ecuación 4.6)."
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
    # curvas de hidrofobicidad); ver docstring de _calcular_kad.
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
    Evalúa la razón espaciado-vuelo de aleta (s/p) contra los umbrales de
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
    Calcula el factor de creepage CF = Linst / S (Ecuación 4.6), según lo
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
    equivalente (USCD_corregido = RUSCD * Kad * Ka, Ecuación 4.4).
    """
    kad = resultado_mecanico.kad
    ka = resultado_mecanico.ka

    if kad is None:
        return resultado_electrico.lmin, resultado_electrico.uscd, False

    uscd_corregido = resultado_electrico.uscd * kad * ka
    lmin_corregido = resultado_electrico.lmin * kad * ka
    return lmin_corregido, uscd_corregido, True