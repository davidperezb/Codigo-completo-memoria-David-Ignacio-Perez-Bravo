# =============================================================================
# B.6 - Módulo de integración de resultados y generación de recomendaciones
# =============================================================================

NOTA_MATERIAL = {
    "ceramico": (
        "Dada la superficie hidrófila del material, se prioriza lavado de "
        "alta presión y/o recubrimiento RTV (Tabla 4.12)."
    ),
    "vidrio": (
        "Dada la superficie hidrófila del material, se prioriza lavado de "
        "alta presión y/o recubrimiento RTV (Tabla 4.12)."
    ),
    "polimerico": (
        "Dada la hidrofobicidad del material, se recomienda lavado según "
        "indicación del fabricante, reservando la intervención para casos "
        "de degradación de la hidrofobicidad por UV o contaminación "
        "industrial severa (Tabla 4.12)."
    ),
}


class ResultadoFinal:
    def __init__(self, nivel, medida_recomendada, aislamiento_suficiente,
                 alertas, indicadores_ambientales):
        self.nivel = nivel
        self.medida_recomendada = medida_recomendada
        self.aislamiento_suficiente = aislamiento_suficiente
        self.alertas = alertas
        self.indicadores_ambientales = indicadores_ambientales

    def __repr__(self):
        return (f"ResultadoFinal(nivel='{self.nivel}', "
                f"aislamiento_suficiente={self.aislamiento_suficiente}, "
                f"n_alertas={len(self.alertas)})")

    def resumen(self):
        lineas = [
            f"Nivel de aceptación operacional: {self.nivel}",
            f"Medida recomendada: {self.medida_recomendada}",
            f"Aislamiento suficiente (Linst >= Lmin): "
            f"{'Sí' if self.aislamiento_suficiente else 'No'}",
        ]
        if self.alertas:
            lineas.append("Alertas activadas:")
            lineas.extend(f"  - {a}" for a in self.alertas)
        else:
            lineas.append("Sin alertas adicionales de perfil, geometría o "
                           "distancia de fuga.")
        return "\n".join(lineas)


def integrar_resultados(resultado_sps, resultado_ambiental,
                         resultado_suficiencia, resultado_mecanico,
                         material, entorno, kad_aplicado=True):
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
        resultado_sps.nivel, medida, resultado_suficiencia.suficiente,
        alertas, indicadores_ambientales
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

    # NOTA: con la implementación actual de _calcular_kad (B.5, curvas de
    # Fig. A.1 según estado_hidrofobicidad), kad_aplicado siempre es True,
    # ya que la función nunca retorna None. Esta alerta se conserva como
    # resguardo defensivo ante una futura extensión del módulo mecánico,
    # pero en la versión actual de la herramienta no se activa en la
    # práctica.
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

    if resultado_mecanico.alerta_sp and entorno == "costero" \
            and resultado_ambiental.activacion_hr:
        alertas.append(
            "Riesgo de puente entre aletas por formación de película de "
            "agua continua bajo condiciones de niebla severa (razón s/p "
            "en zona de desviación mayor)."
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
    Función de orquestación principal de la herramienta (Sección 5.3).

    Nota sobre 'estado_hidrofobicidad': solo tiene efecto cuando
    material == "polimerico"; determina qué curva de la Figura A.1 se
    usa para el factor Kad en el módulo mecánico (B.5). Si no se conoce
    el estado real del polimérico, se mantiene el default
    "sin_transferencia" (Non-HTM), supuesto conservador declarado en la
    Sección 4.2.3.2.

    Nota sobre 'altitud': se recibe en msnm y se utiliza internamente
    para calcular el factor Ka (Sección 5.3.6). Para altitud <= 1000
    msnm, Ka = 1,0; sobre ese umbral se aplica la Ecuación 4.6 con el
    exponente correspondiente al perfil del aislador (calcular_ka_altitud,
    B.4).

    Nota sobre 's_aleta' y 's_arco': no se solicita 'cf' como dato de
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
        s_aleta, p, linst, s_arco, resultado_sps.clase_severidad,
        con_nervaduras=con_nervaduras, diametro_vastago=diametro_vastago,
        estado_hidrofobicidad=estado_hidrofobicidad
    )

    ka = calcular_ka_altitud(altitud, perfil)

    lmin_final, kad_aplicado = calcular_lmin_corregido(
        resultado_electrico, resultado_mecanico, ka=ka
    )

    resultado_suficiencia = verificar_suficiencia_aislamiento(
        linst, lmin_final
    )

    return integrar_resultados(
        resultado_sps, resultado_ambiental, resultado_suficiencia,
        resultado_mecanico, material, entorno, kad_aplicado=kad_aplicado
    )