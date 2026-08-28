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
            "rango recomendado."
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