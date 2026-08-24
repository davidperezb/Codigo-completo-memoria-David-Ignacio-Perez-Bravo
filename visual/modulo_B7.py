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

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


# Colores consistentes con el diagrama de flujo 1 (Normal=verde,
# Advertencia=amarillo, Crítico=rojo), para que la memoria se vea coherente
# entre el diagrama y los gráficos.
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
        fig.savefig(guardar_en, dpi=200)

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
        fig.savefig(guardar_en, dpi=200)

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

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(verificaciones, valores, color=colores, edgecolor="black",
            linewidth=0.8)

    for i, ok in enumerate(estados_ok):
        ax.text(0.5, i, "OK" if ok else "ALERTA", ha="center", va="center",
                fontsize=10, fontweight="bold", color="white")

    ax.set_xlim(0, 1)
    ax.set_xticks([])
    ax.set_title(f"{nombre_caso} — Estado de verificaciones mecánicas y eléctricas")
    fig.tight_layout()

    if guardar_en:
        fig.savefig(guardar_en, dpi=200)

    return fig


# -----------------------------------------------------------------------
# Ejemplo de uso con datos ilustrativos (mismos que irían en el Capítulo 6)
# -----------------------------------------------------------------------
if __name__ == "__main__":
    escenarios_ejemplo = [
        {"nombre": "Costero (Tarapacá)", "esdd": 0.18, "nsdd": 0.35},
        {"nombre": "Desértico (Atacama)", "esdd": 0.06, "nsdd": 0.22},
        {"nombre": "Industrial", "esdd": 0.09, "nsdd": 0.14},
    ]
    graficar_mapa_clasificacion(escenarios_ejemplo,
                                 guardar_en="/home/claude/mapa_clasificacion.png")

    graficar_comparacion_lmin(un=110, lmin_basico=2464, lmin_corregido=2587,
                               linst=2200, nombre_caso="Aislador costero 110 kV",
                               guardar_en="/home/claude/comparacion_lmin.png")

    class _Mecanico:
        perfil_ok = False
        alerta_sp = True
        alerta_cf = False

    class _Suficiencia:
        suficiente = False

    graficar_alertas_mecanicas(_Mecanico(), _Suficiencia(),
                                nombre_caso="Aislador costero 110 kV",
                                guardar_en="/home/claude/alertas_mecanicas.png")

    print("Gráficos generados correctamente.")