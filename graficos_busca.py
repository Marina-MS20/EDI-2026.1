import os
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def scientific_name(value):
    exp = int(f"{value:.0e}".split("e")[1])
    return f"10a{exp}"

# ============================================================
# CONFIGURAÇÃO
# ============================================================

# Escalas Y máximas individuais (SEMPRE respeitadas — o eixo Y de cada
# gráfico vai de 0 até este valor, independente do valor máximo real dos
# dados. Isso garante que todos os gráficos fiquem na mesma escala.)
Y_MAX_COMPARISONS = 1e4
Y_MAX_TIME_MS = 1e4


INPUT_DIR = "output"

OUTPUT_DIR = (
    "graficos_busca_cm_"
    + scientific_name(Y_MAX_COMPARISONS)
    + "_t_"
    + scientific_name(Y_MAX_TIME_MS)
)

EXPORT_PNG = True
EXPORT_SVG = True
EXPORT_PDF = False

USE_LOG_SCALE = False

FIGSIZE = (12, 6)
FIGSIZE_COMBINED = (FIGSIZE[0] * 1.7, FIGSIZE[1])
DPI = 300


# ============================================================
# FONTES (ampliadas para os gráficos ficarem legíveis quando
# reduzidos, ex.: 6 gráficos numa única slide)
# ============================================================

FONT_TITLE = 22
FONT_SUBTITLE = 18
FONT_AXIS_LABEL = 18
FONT_TICK_LABEL = 15
FONT_LEGEND = 17
LEGEND_MARKERSCALE = 1.4

LINE_WIDTH = 3.0
MARKER_SIZE = 6

# ============================================================
# ESTRUTURAS DE BUSCA
# ============================================================

STRUCTURES = [
    ("seq", "Busca Sequencial", ["seq_random", "seq_sorted", "seq_reverse"]),
    ("bin", "Busca Binária", ["bin"]),
    ("abb", "ABB", ["abb_random", "abb_sorted", "abb_reverse"]),
    ("avl", "AVL", ["avl_random", "avl_sorted", "avl_reverse"]),
]

# ============================================================
# DISPOSIÇÕES (variantes de dados)
# ============================================================

DISPOSITIONS = {
    "seq_random": ("Aleatório", "yellow"),
    "seq_sorted": ("Ordenado", "blue"),
    "seq_reverse": ("Reverso", "red"),
    "bin": ("Ordenado", "green"),
    "abb_random": ("Aleatório", "orange"),
    "abb_sorted": ("Ordenado", "purple"),
    "abb_reverse": ("Reverso", "brown"),
    "avl_random": ("Aleatório", "pink"),
    "avl_sorted": ("Ordenado", "cyan"),
    "avl_reverse": ("Reverso", "magenta"),
}

# ============================================================
# ESCALAS GLOBAIS (apenas para fins de diagnóstico/print — não
# influenciam mais o limite do eixo Y, que agora é sempre fixo)
# ============================================================

GLOBAL_MAX = {
    "comparisons": 0,
    "time_ms": 0
}

# ============================================================
# LEITURA DOS CSVs
# ============================================================

def load_csv(filename):
    """Carrega CSV e remove linhas com 'FAIL'"""
    path = Path(INPUT_DIR) / f"{filename}.csv"

    if not path.exists():
        print(f"[AVISO] Arquivo não encontrado: {filename}.csv")
        return None

    try:
        df = pd.read_csv(path)

        # Remove linhas com "FAIL" em qualquer coluna
        df = df[(df != "FAIL").all(axis=1)]

        # Converte todas as colunas para numéricas
        df = df.apply(pd.to_numeric, errors='coerce')

        # Remove linhas com NaN após conversão
        df = df.dropna()

        # Converte tempo de ns para ms (divide por 1.000.000)
        if "time_ns" in df.columns:
            df["time_ms"] = df["time_ns"] / 1e6
            df = df.drop(columns=["time_ns"])

        return df if not df.empty else None

    except Exception as e:
        print(f"Erro lendo {filename}.csv: {e}")
        return None

# ============================================================
# CALCULA ESCALAS GLOBAIS PARA TODAS AS ESTRUTURAS (diagnóstico)
# ============================================================

def calculate_global_limits():
    """Calcula os valores máximos para cada métrica em TODAS as estruturas.
    Usado apenas para o print de diagnóstico comparando dado real x teto
    configurado — não é mais usado para definir o limite do eixo Y."""
    print()
    print("=" * 70)
    print("CALCULANDO ESCALAS GLOBAIS (apenas diagnóstico)")
    print("=" * 70)

    for _, _, files in STRUCTURES:
        for filename in files:
            df = load_csv(filename)

            if df is None:
                continue

            for column in GLOBAL_MAX:
                if column in df.columns:
                    value = df[column].max()
                    if value > GLOBAL_MAX[column]:
                        GLOBAL_MAX[column] = value

    print()
    print(f"Máximo real nos dados — Comparações : {GLOBAL_MAX['comparisons']:,.0f}")
    print(f"Máximo real nos dados — Tempo (ms)  : {GLOBAL_MAX['time_ms']:,.6f}")
    print()
    print(f"Escala Y fixa — Comparações         : {Y_MAX_COMPARISONS:.0e}")
    print(f"Escala Y fixa — Tempo (ms)          : {Y_MAX_TIME_MS:.0e}")
    print()

# ============================================================
# CRIA FIGURA COMBINADA (Comparações + Tempo lado a lado)
# ============================================================

def create_figure(title):
    """Cria uma única figura com 2 subplots lado a lado:
    à esquerda Comparações, à direita Tempo (ms)."""
    fig, axes = plt.subplots(1, 2, figsize=FIGSIZE_COMBINED)
    fig.suptitle(title, fontsize=FONT_TITLE, fontweight="bold")
    return fig, axes

# ============================================================
# CONFIGURA EIXO COM ESCALA FIXA (SEMPRE RESPEITADA)
# ============================================================

def setup_axis(ax, subtitle, ylabel, y_max_scale):
    """Configura rótulos, fontes e escala do eixo.

    A escala Y é SEMPRE fixada em (0, y_max_scale) — não é recalculada a
    partir do valor máximo encontrado nos dados. Isso é o que garante que
    Y_MAX_COMPARISONS / Y_MAX_TIME_MS sejam de fato respeitados em todos
    os gráficos.
    """
    ax.set_title(subtitle, fontsize=FONT_SUBTITLE)
    ax.set_xlabel("n", fontsize=FONT_AXIS_LABEL)
    ax.set_ylabel(ylabel, fontsize=FONT_AXIS_LABEL)
    ax.tick_params(axis='both', which='major', labelsize=FONT_TICK_LABEL)
    ax.grid(True, alpha=0.3)

    if USE_LOG_SCALE:
        # Escala log não aceita 0 como limite inferior; fixamos só o topo.
        ax.set_yscale("log")
        ax.set_ylim(top=y_max_scale)
    else:
        ax.set_ylim(0, y_max_scale)
        # Formata eixo Y em notação científica
        ax.ticklabel_format(style='scientific', axis='y', scilimits=(0, 0))
        ax.yaxis.get_offset_text().set_fontsize(FONT_TICK_LABEL)

# ============================================================
# LEGENDA PADRONIZADA (fonte ampliada, com moldura para destacar)
# ============================================================

def add_legend(fig, handles, labels, ncol):
    """Adiciona legenda no rodapé da figura com fonte ampliada, para
    continuar legível quando vários gráficos forem reduzidos numa slide."""
    return fig.legend(
        handles,
        labels,
        loc="lower center",
        ncol=ncol,
        fontsize=FONT_LEGEND,
        markerscale=LEGEND_MARKERSCALE,
        handlelength=2.5,
        frameon=True,
        framealpha=0.95,
        edgecolor="gray",
        borderpad=0.8,
    )

# ============================================================
# SALVAR FIGURA
# ============================================================

def save_figure(fig, filename):
    """Salva figura nos formatos especificados"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = Path(OUTPUT_DIR)

    if EXPORT_PNG:
        fig.savefig(path / f"{filename}.png", dpi=DPI, bbox_inches="tight")

    if EXPORT_SVG:
        fig.savefig(path / f"{filename}.svg", bbox_inches="tight")

    if EXPORT_PDF:
        fig.savefig(path / f"{filename}.pdf", bbox_inches="tight")

# ============================================================
# GERA GRÁFICOS POR ESTRUTURA (Comparações + Tempo juntos)
# ============================================================

def plot_by_structure():
    """Cria UM gráfico por estrutura, com Comparações e Tempo lado a
    lado na mesma imagem."""

    for struct_id, struct_name, files in STRUCTURES:

        print()
        print("=" * 70)
        print(f"Gerando gráfico: {struct_name} (Comparações + Tempo)")
        print("=" * 70)

        fig, (ax_comp, ax_time) = create_figure(struct_name)

        legend_handles = []
        legend_labels = []

        for filename in files:
            df = load_csv(filename)

            if df is None:
                print(f"[AVISO] Dados não encontrados para {filename}")
                continue

            disposition_label, color = DISPOSITIONS.get(filename, (filename, "gray"))

            line_for_legend = None

            if "n" in df.columns and "comparisons" in df.columns:
                try:
                    line, = ax_comp.plot(
                        df["n"],
                        df["comparisons"],
                        color=color,
                        linewidth=LINE_WIDTH,
                        marker="o",
                        markersize=MARKER_SIZE,
                        label=disposition_label
                    )
                    setup_axis(ax_comp, "Comparações", "Comparações", Y_MAX_COMPARISONS)
                    line_for_legend = line
                except Exception as e:
                    print(f"[ERRO] Ao plotar comparações de {filename}: {e}")
            else:
                print(f"[AVISO] Coluna 'comparisons' faltante em {filename}")

            if "n" in df.columns and "time_ms" in df.columns:
                try:
                    line2, = ax_time.plot(
                        df["n"],
                        df["time_ms"],
                        color=color,
                        linewidth=LINE_WIDTH,
                        marker="o",
                        markersize=MARKER_SIZE,
                        label=disposition_label
                    )
                    setup_axis(ax_time, "Tempo (ms)", "Tempo (ms)", Y_MAX_TIME_MS)
                    if line_for_legend is None:
                        line_for_legend = line2
                except Exception as e:
                    print(f"[ERRO] Ao plotar tempo de {filename}: {e}")
            else:
                print(f"[AVISO] Coluna 'time_ms' faltante em {filename}")

            if line_for_legend is not None and disposition_label not in legend_labels:
                legend_labels.append(disposition_label)
                legend_handles.append(line_for_legend)

        if legend_handles:
            add_legend(fig, legend_handles, legend_labels, ncol=len(legend_labels))
            fig.tight_layout(rect=[0, 0.13, 1, 0.90])

            save_figure(fig, f"{struct_id}_comparacoes_tempo")
            plt.close(fig)

            print(f"[OK] Gráfico salvo: {struct_id}_comparacoes_tempo")
        else:
            plt.close(fig)

# ============================================================
# GERA GRÁFICO GLOBAL COMPARATIVO (Comparações + Tempo juntos)
# ============================================================

def plot_global_comparisons():
    """Cria UM gráfico global comparando todas as estruturas, com
    Comparações e Tempo lado a lado na mesma imagem."""

    print()
    print("=" * 70)
    print("Gráfico Global: Comparações + Tempo (todas as estruturas)")
    print("=" * 70)

    fig, (ax_comp, ax_time) = create_figure("Comparação Global (todas as estruturas)")

    legend_handles = []
    legend_labels = []

    struct_colors = {
        "seq": "green",
        "bin": "blue",
        "abb": "orange",
        "avl": "red",
    }

    for struct_id, struct_name, files in STRUCTURES:
        filename = files[0]  # Pega a primeira variante
        df = load_csv(filename)

        if df is None:
            print(f"[AVISO] Dados não encontrados para {filename}")
            continue

        color = struct_colors.get(struct_id, "gray")
        line_for_legend = None

        if "n" in df.columns and "comparisons" in df.columns:
            try:
                line, = ax_comp.plot(
                    df["n"],
                    df["comparisons"],
                    color=color,
                    linewidth=LINE_WIDTH,
                    marker="o",
                    markersize=MARKER_SIZE,
                    label=struct_name,
                    alpha=0.8
                )
                setup_axis(ax_comp, "Comparações", "Comparações", Y_MAX_COMPARISONS)
                line_for_legend = line
            except Exception as e:
                print(f"[ERRO] Ao plotar comparações de {filename}: {e}")

        if "n" in df.columns and "time_ms" in df.columns:
            try:
                line2, = ax_time.plot(
                    df["n"],
                    df["time_ms"],
                    color=color,
                    linewidth=LINE_WIDTH,
                    marker="o",
                    markersize=MARKER_SIZE,
                    label=struct_name,
                    alpha=0.8
                )
                setup_axis(ax_time, "Tempo (ms)", "Tempo (ms)", Y_MAX_TIME_MS)
                if line_for_legend is None:
                    line_for_legend = line2
            except Exception as e:
                print(f"[ERRO] Ao plotar tempo de {filename}: {e}")

        if line_for_legend is not None and struct_name not in legend_labels:
            legend_labels.append(struct_name)
            legend_handles.append(line_for_legend)

    if legend_handles:
        add_legend(fig, legend_handles, legend_labels, ncol=4)
        fig.tight_layout(rect=[0, 0.13, 1, 0.90])
        save_figure(fig, "global_comparacoes_tempo")
        plt.close(fig)

        print(f"[OK] Gráfico salvo: global_comparacoes_tempo")
    else:
        plt.close(fig)

# ============================================================
# MAIN
# ============================================================

def main():
    """Função principal"""
    print("=" * 70)
    print("GERADOR AUTOMÁTICO DE GRÁFICOS DE BUSCA")
    print("=" * 70)
    print(f"Escala Y fixa Comparações: {Y_MAX_COMPARISONS:.0e}")
    print(f"Escala Y fixa Tempo (ms): {Y_MAX_TIME_MS:.0e}")
    print("Unidade de tempo: milissegundos (ms)")
    print("=" * 70)

    # Cria diretório de saída
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Calcula escalas globais (apenas diagnóstico/print)
    calculate_global_limits()

    # Gera um gráfico por estrutura (Comparações + Tempo juntos)
    plot_by_structure()

    # Gera o gráfico global comparativo (Comparações + Tempo juntos)
    plot_global_comparisons()

    print()
    print("=" * 70)
    print("PROCESSAMENTO FINALIZADO")
    print("=" * 70)
    print()
    print(f"Gráficos salvos em: {OUTPUT_DIR}")
    print()
    print("Gráficos gerados:")
    print("  - seq_comparacoes_tempo.png")
    print("  - bin_comparacoes_tempo.png")
    print("  - abb_comparacoes_tempo.png")
    print("  - avl_comparacoes_tempo.png")
    print("  - global_comparacoes_tempo.png")

# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    main()
