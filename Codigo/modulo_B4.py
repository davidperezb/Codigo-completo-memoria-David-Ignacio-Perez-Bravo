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