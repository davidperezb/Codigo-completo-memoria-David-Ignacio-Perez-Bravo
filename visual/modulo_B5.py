# =============================================================================
# B.5 - Módulo mecánico (perfil, Kad, Ka por altitud, s/p y CF)
# =============================================================================

PERFIL_RECOMENDADO_POR_ENTORNO = {
    "costero":    "antiniebla",
    "desertico":  "aerodinamico",
    "industrial": "alternante",
}

# Figura A.2 - Umbrales de desviación s/p para cerámico y vidrio [3].
# No distingue por diámetro de vástago, solo por presencia de nervaduras.
UMBRALES_SP_CERAMICO_VIDRIO = {
    "con_nervaduras": {"mayor_max": 0.60, "menor_max": 0.75},
    "sin_nervaduras": {"mayor_max": 0.50, "menor_max": 0.65},
}

# Figura A.3 - Umbrales de desviación s/p para poliméricos [7].
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
# SPS, para aisladores cerámicos y de vidrio [3].
UMBRALES_CF_CERAMICO_VIDRIO = {
    "muy_ligero": {"sin_desviacion_max": 3.50,  "desviacion_menor_max": 4.25},
    "ligero":     {"sin_desviacion_max": 3.625, "desviacion_menor_max": 4.40},
    "medio":      {"sin_desviacion_max": 3.75,  "desviacion_menor_max": 4.55},
    "pesado":     {"sin_desviacion_max": 3.875, "desviacion_menor_max": 4.70},
    "muy_pesado": {"sin_desviacion_max": 4.00,  "desviacion_menor_max": 4.85},
}

# Tabla 4.10 - Umbrales de desviación del factor de creepage (CF) para
# aisladores poliméricos, obtenidos por lectura gráfica de la Figura A.4
# (Umbrales del factor de creepage para poliméricos).
UMBRALES_CF_POLIMERICO = {
    "muy_ligero": {"desviacion_menor_max": 4.25},
    "ligero":     {"desviacion_menor_max": 4.35},
    "medio":      {"desviacion_menor_max": 4.45},
    "pesado":     {"desviacion_menor_max": 4.65},
    "muy_pesado": {"desviacion_menor_max": 4.80},
}

# Figura A.1 [7] - Parámetros de las tres curvas de Kad para aisladores
# poliméricos, según el estado de hidrofobicidad del material. Las tres
# convergen en Da = 300 mm con Kad = 1,0:
#
#   "hidrofobico"            : hidrofobicidad intacta (HTM). Kad = 1,0
#                               en todo el rango de Da (curva plana).
#   "sin_transferencia"      : material sin transferencia de hidrofobicidad
#                               (Non-HTM). Sube más rápido: alcanza Kad = 1,3
#                               en Da = 600 mm.
#   "perdida_hidrofobicidad" : material que tuvo hidrofobicidad y la perdió
#                               por degradación UV o contaminación industrial
#                               severa (Sección 3.3, comportamiento tiende a
#                               asemejarse al cerámico). Sube más lento:
#                               alcanza Kad = 1,3 en Da = 1000 mm (límite de
#                               datos graficados en la norma).

KAD_POLIMERICO_DA_MIN = 300        # mm, punto de convergencia (Kad = 1.0)
KAD_POLIMERICO_VALOR_MIN = 1.0     # Kad en Da_min, común a las tres curvas
KAD_POLIMERICO_VALOR_MAX = 1.3     # Kad máximo graficado en Fig. A.1

CURVAS_KAD_POLIMERICO = {
    "hidrofobico":            {"da_max": None},   # curva plana, Kad = 1.0 siempre
    "sin_transferencia":      {"da_max": 600},     # llega a 1.3 en Da = 600 mm
    "perdida_hidrofobicidad": {"da_max": 1000},    # llega a 1.3 en Da = 1000 mm
}

ESTADO_HIDROFOBICIDAD_DEFAULT = "sin_transferencia"

# Sección 5.3.6 (Ka por altitud) - SEC RPTD N°05, remitido a IEC 60071-2.
# Bajo este umbral se adopta Ka = 1,0; sobre él se aplica la Ecuación 4.6.
UMBRAL_ALTITUD_KA = 1000  # msnm

# Exponente m de la Ecuación 4.6, según perfil del aislador (IEC 60071-2).
# El perfil antiniebla usa m = 0,8; el resto de los perfiles (estándar,
# aerodinámico, alternante) usa m = 0,5 como valor por defecto.
EXPONENTE_M_PERFIL = {
    "antiniebla": 0.8,
}
EXPONENTE_M_DEFAULT = 0.5


class ResultadoMecanico:
    """
    Contenedor del resultado del módulo mecánico (Sección 5.3.5).

    Atributos:
        perfil_ok (bool): True si el perfil instalado coincide con el
            perfil recomendado para el entorno (Tabla 4.8), O si el
            perfil instalado es "alternante", dado que este perfil es
            de aplicación general a cualquier entorno según la Tabla 4.7
            del presente trabajo; ver _evaluar_perfil_ok.
        perfil_recomendado (str): perfil recomendado para el entorno dado.
        da (float): diámetro promedio del aislador (Ecuación 4.5, mm).
            Se calcula con la MISMA fórmula para los tres materiales
            (cerámico, vidrio, polimérico); ver _calcular_da.
        kad (float): factor de corrección por diámetro (Ecuación 4.4 para
            cerámico/vidrio; aproximación lineal de la Figura A.1 según
            estado de hidrofobicidad para polimérico, Sección 4.2.3.2).
            Este es el único punto donde el criterio difiere por material.
        ka (float): factor de corrección por altitud (Ecuación 4.6).
        ka_aplicado (bool): True si la altitud ingresada superó el umbral
            de 1000 msnm y por lo tanto Ka fue efectivamente calculado
            mediante la Ecuación 4.6 (Ka != 1,0). False si el sitio está
            a 1000 msnm o menos, caso en que se adopta Ka = 1,0 por
            defecto (Sección 5.3.6) sin aplicar la ecuación.
        alerta_sp (bool): True si la razón s/p ingresada cae en zona de
            desviación mayor para el material y configuración indicados.
        cf (float): factor de creepage, calculado automáticamente como
            Linst / S (Ecuación 4.9); no es un dato de entrada directo
            (Sección 4.2.3.4).
        alerta_cf (bool): True si el factor de creepage calculado cae en
            zona de desviación mayor para el material y clase SPS
            indicados (Tabla 4.9 para cerámico/vidrio, Tabla 4.10 para
            polimérico).
    """

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
    """
    Calcula el factor de corrección por altitud Ka, según la Ecuación
    4.6 (IEC 60071-2, remitida por SEC Pliego Técnico Normativo N°05).
    Para altitud <= 1000 msnm se adopta Ka = 1,0 (Sección 5.3.6).

    Ka = exp(m * H / 8150)

    donde H es la altitud del sitio (m) y m depende del perfil del
    aislador: 0,8 para perfil antiniebla, 0,5 para el resto (estándar,
    aerodinámico, alternante), según IEC 60071-2.

    Args:
        altitud (float): altitud del sitio sobre el nivel del mar (m).
        perfil (str): perfil del aislador instalado, determina el
            exponente m.

    Returns:
        float: factor Ka (adimensional).

    Raises:
        ValueError: si altitud es negativa.
    """
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
    """
    Evalúa las variables mecánicas del aislador instalado: perfil, factor
    Kad, factor Ka por altitud, razón s/p y factor de creepage (CF),
    contrastando cada una contra los umbrales normativos correspondientes
    al material indicado (Sección 5.3.5).

    Args:
        material (str): "ceramico", "vidrio" o "polimerico".
        entorno (str): "costero", "desertico" o "industrial".
        perfil (str): perfil del aislador instalado (Tabla 4.8).
        dt (float): diámetro del tronco del aislador (mm).
        ds1 (float): diámetro de la aleta superior adyacente (mm).
        ds2 (float): diámetro de la aleta inferior adyacente (mm).
        s_aleta (float): espaciado entre aletas, símbolo "s" en la razón
            s/p (mm). No confundir con s_arco.
        p (float): vuelo de aleta (mm).
        linst (float): distancia de fuga instalada (mm), variable
            eléctrica ya definida en B.4/Sección 4.2.2.2; se reutiliza
            aquí como numerador de CF (Ecuación 4.9).
        s_arco (float): distancia de arco, símbolo "S" en la norma
            (Sección 4.2.3.4) (mm). No confundir con s_aleta.
        altitud (float): altitud del sitio sobre el nivel del mar (m).
            Variable mecánica (ver nota de módulo B.5): determina el
            factor Ka junto con el perfil instalado.
        clase_severidad (str): clase de severidad IEC de 5 niveles,
            obtenida desde ResultadoSPS.clase_severidad (B.2). Se usa
            tanto para el umbral de CF cerámico/vidrio (Tabla 4.9) como
            para el umbral de CF polimérico (Tabla 4.10).
        con_nervaduras (bool, optional): True si el aislador presenta
            nervaduras internas (under-ribs) en la aleta (Figuras
            A.2/A.3). Si no se dispone de este dato en la hoja técnica
            del fabricante, se asume True (con nervaduras) como supuesto
            conservador, dado que esta configuración exige el umbral
            "mayor" más exigente (zona de desviación mayor más amplia,
            Sección 4.2.3.3), reduciendo el riesgo de subestimar una
            alerta real de puente entre aletas. Default: True.
        diametro_vastago (float, optional): diámetro del vástago del
            aislador (mm). Obligatorio solo si material == "polimerico",
            ya que la Figura A.3 distingue umbrales según este valor
            (<=110 mm o >110 mm).
        estado_hidrofobicidad (str, optional): estado del recubrimiento
            polimérico, solo aplica si material == "polimerico". Uno de
            "hidrofobico" (hidrofobicidad intacta), "sin_transferencia"
            (material sin transferencia de hidrofobicidad) o
            "perdida_hidrofobicidad" (tuvo hidrofobicidad y la perdió por
            degradación UV o contaminación industrial severa). Si no se
            conoce el estado real, se asume "sin_transferencia" como
            supuesto conservador (Sección 4.2.3.2). Default:
            "sin_transferencia".

    Returns:
        ResultadoMecanico: objeto con los resultados de las cinco
        verificaciones mecánicas (perfil, Kad, Ka, s/p, CF).

    Raises:
        ValueError: si material o entorno no son válidos, si algún
            parámetro geométrico es negativo, si s_arco no es positivo
            (CF = Linst/S no está definido para S <= 0), si altitud es
            negativa, si material == "polimerico" y no se entrega
            diametro_vastago, o si estado_hidrofobicidad no es válido.
    """
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
            "calcula como Linst / S (Ecuación 4.9)."
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
    """
    Evalúa si el perfil instalado es aceptable para el entorno, según la
    Tabla 4.7 (Clasificación de perfiles de aislador según entorno
    recomendado).

    El perfil "alternante" se acepta en CUALQUIER entorno sin generar
    alerta, ya que la Tabla 4.7 lo describe explícitamente como
    "aplicable en general a cualquier entorno" (combina las ventajas de
    autolimpiado del perfil abierto con la mayor distancia de fuga del
    perfil antiniebla). Para los demás perfiles (estándar, aerodinámico,
    antiniebla), se exige coincidencia exacta con el perfil de
    referencia del entorno (PERFIL_RECOMENDADO_POR_ENTORNO).
    """
    if perfil == "alternante":
        return True
    return perfil == PERFIL_RECOMENDADO_POR_ENTORNO[entorno]


def _calcular_da(dt, ds1, ds2):
    """
    Calcula el diámetro promedio del aislador Da, según la Ecuación 4.5
    - IEC/TS 60815-2/3:2008.

    Esta fórmula es idéntica para aisladores cerámicos, de vidrio y
    poliméricos (no depende del material); lo que sí difiere por
    material es el criterio de Kad aplicado sobre Da (ver _calcular_kad).
    """
    return (2 * dt + ds1 + ds2) / 4


def _calcular_kad(da, material, estado_hidrofobicidad=ESTADO_HIDROFOBICIDAD_DEFAULT):
    """
    Calcula el factor de corrección Kad según el diámetro promedio del
    aislador Da, según la Ecuación 4.4 - IEC/TS 60815-2:2008.

    Cerámico/vidrio: expresión cerrada de [3] (Ecuación 4.4).

    Polimérico: [7] no entrega expresión cerrada, solo la familia de
    curvas de la Figura A.1, diferenciadas según el estado de
    hidrofobicidad del material (ver CURVAS_KAD_POLIMERICO). Las tres
    curvas convergen en Kad = 1,0 para Da < 300 mm. Para Da >= 300 mm:

    - "hidrofobico": curva plana, Kad = 1,0 en todo el rango.
    - "sin_transferencia" y "perdida_hidrofobicidad": interpolación
      lineal entre (300 mm, 1,0) y (da_max, 1,3), capada en Kad = 1,3
      para Da >= da_max, ya que extrapolar más allá del rango graficado
      en la norma no está respaldado por datos (limitación declarada en
      Sección 4.2.3.2).
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
    desviación del material correspondiente (Figuras A.2 y A.3, [3, 7]),
    determinando si corresponde emitir advertencia de riesgo de puente
    entre aletas (Sección 4.2.3.3).

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
    Calcula el factor de creepage CF = Linst / S (Ecuación 4.9), según lo
    descrito en la Sección 4.2.3.4: CF no se solicita como dato de
    entrada directo, se obtiene a partir de Linst (variable eléctrica,
    Sección 4.2.2.2) y S, la distancia de arco (variable mecánica).
    """
    return linst / s_arco


def _evaluar_cf(cf, material, clase_severidad):
    """
    Evalúa el factor de creepage (CF) contra los umbrales de desviación
    mayor del material correspondiente, según la Sección 4.2.3.4:

    - Cerámico/vidrio: Tabla 4.9, umbral "desviacion_menor_max" por
      clase SPS; CF por sobre ese valor corresponde a desviación mayor.
    - Polimérico: Tabla 4.10 (lectura gráfica de la Figura A.4),
      mismo criterio, con umbrales propios del material por clase SPS.

    Returns:
        bool: True si cf corresponde a desviación mayor para el
        material y clase de severidad indicados.

    Raises:
        ValueError: si clase_severidad no es válida para el material.
    """
    tabla = (UMBRALES_CF_CERAMICO_VIDRIO if material in ("ceramico", "vidrio")
             else UMBRALES_CF_POLIMERICO)

    if clase_severidad not in tabla:
        raise ValueError(
            f"Clase de severidad '{clase_severidad}' no válida."
        )

    umbral_mayor = tabla[clase_severidad]["desviacion_menor_max"]
    return cf > umbral_mayor


def calcular_lmin_corregido(resultado_electrico, resultado_mecanico):
    """
    Aplica la corrección Kad · Ka al Lmin básico (Ecuación 4.4/4.5 y
    Sección 4.2.4 - Ka por altitud), y calcula también el USCD corregido
    equivalente (USCD_corregido = RUSCD * Kad * Ka, Ecuación 4.4).

    Nota (corrección post-Figura A.1): con la actualización de
    _calcular_kad, el factor Kad ya no retorna None para ningún caso
    cubierto por la herramienta (ver B.5), por lo que kad_aplicado es
    siempre True en la versión actual. Se mantiene el flag por
    trazabilidad y como resguardo ante futuras extensiones del módulo
    mecánico (p. ej., si se incorpora un estado de hidrofobicidad
    degradada como variable de entrada).

    Returns:
        tuple: (lmin_corregido, uscd_corregido, kad_aplicado)
    """
    kad = resultado_mecanico.kad
    ka = resultado_mecanico.ka

    if kad is None:
        return resultado_electrico.lmin, resultado_electrico.uscd, False

    uscd_corregido = resultado_electrico.uscd * kad * ka
    lmin_corregido = resultado_electrico.lmin * kad * ka
    return lmin_corregido, uscd_corregido, True