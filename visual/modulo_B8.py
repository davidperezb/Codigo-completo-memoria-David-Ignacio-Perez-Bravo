# =============================================================================
# B.8 - CLI interactivo (CORREGIDO)
# =============================================================================
# Cambios respecto a la versión anterior:
#  - Ya no se pide "cf" como dato de entrada: se pide "s_arco" (distancia
#    de arco S), consistente con evaluar_modulo_mecanico (B.5) y con la
#    Sección 4.2.3.4 ("CF no se solicita como dato de entrada directo").
#  - Se agregó la solicitud de "s_aleta" (espaciado entre aletas, símbolo
#    "s" en s/p) de forma explícita y separada de "s_arco", para no
#    confundir ambas variables normativas que comparten letra.
#  - La rama de graficado ahora llama a evaluar_modulo_mecanico() con el
#    orden de argumentos correcto (incluye clase_severidad real, no un
#    valor de cf mal ubicado).
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
    altitud = _pedir_float("Altitud del sitio (msnm): ", minimo=0)

    print("\n--- Datos mecánicos ---")
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
    print("\nIndicadores ambientales:")
    for k, v in resultado.indicadores_ambientales.items():
        print(f"  - {k}: {v}")

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
            s_arco, resultado_sps.clase_severidad,
            con_nervaduras=con_nervaduras, diametro_vastago=diametro_vastago,
            estado_hidrofobicidad=estado_hidrofobicidad
        )
        ka = calcular_ka_altitud(altitud, perfil)
        lmin_corregido, _ = calcular_lmin_corregido(
            resultado_electrico, resultado_mecanico, ka=ka
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