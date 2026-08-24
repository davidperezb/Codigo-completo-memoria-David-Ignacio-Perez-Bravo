
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
    eléctrico (cálculo de Lmin); no se muestra directamente al usuario.
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