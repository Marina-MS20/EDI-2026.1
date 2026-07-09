import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from pathlib import Path

def human_format(value, _pos=None):
    """Formata valores dos eixos em português: mil, mi (milhão), bi (bilhão).
    Ex.: 7_000_000 -> "7 mi", 1_500 -> "1,5 mil", 0.5 -> "0,5"."""
    if value == 0:
        return "0"
    for div, suffix in ((1e9, " bi"), (1e6, " mi"), (1e3, " mil")):
        if abs(value) >= div:
            txt = f"{value / div:.1f}".rstrip("0").rstrip(".")
            return txt.replace(".", ",") + suffix
    txt = f"{value:.2f}".rstrip("0").rstrip(".")
    return txt.replace(".", ",")

HUMAN_FORMATTER = FuncFormatter(human_format)

# ============================================================
# CONFIGURAÇÃO
# ============================================================

INPUT_DIR = "output 5 horas 7 MLHOS"
OUTPUT_DIR = "graficos_busca"

EXPORT_PNG = True
EXPORT_SVG = True
EXPORT_PDF = False

# Janela da mediana móvel usada para suavizar o tempo e remover os
# picos instantâneos de medição (GC, interrupções do SO etc.)
SMOOTH_WINDOW = 9

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

LINE_WIDTH = 2.5
MARKER_SIZE = 2.5

# ============================================================
# ESTRUTURAS DE BUSCA (arquivos conforme a pasta de dados)
# ============================================================

STRUCTURES = [
    ("seq", "Busca Sequencial", ["seq"]),
    ("bin", "Busca Binária", ["bin"]),
    ("abb", "ABB", ["bst_random", "bst_sorted", "bst_reverse"]),
    ("avl", "AVL", ["avl_random", "avl_sorted", "avl_reverse"]),
]

# ============================================================
# DISPOSIÇÕES (variantes de dados)
# ============================================================

DISPOSITIONS = {
    "seq": ("Aleatório", "green"),
    "bin": ("Ordenado", "blue"),
    "bst_random": ("Aleatório", "orange"),
    "bst_sorted": ("Ordenado", "purple"),
    "bst_reverse": ("Reverso", "brown"),
    "avl_random": ("Aleatório", "pink"),
    "avl_sorted": ("Ordenado", "cyan"),
    "avl_reverse": ("Reverso", "magenta"),
}

# ============================================================
# LEITURA DOS CSVs
# ============================================================

def load_csv(filename):
    """Carrega CSV, remove linhas com 'FAIL', converte tempo para ms e
    suaviza o tempo com mediana móvel para eliminar picos de medição."""
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

        if df.empty:
            return None

        df = df.sort_values("n")

        # Converte tempo de ns para ms
        if "time_ns" in df.columns:
            df["time_ms"] = df["time_ns"] / 1e6
            df = df.drop(columns=["time_ns"])

        # Suaviza o tempo: mediana móvel centrada — remove os "pipocos"
        # (picos instantâneos) sem distorcer a tendência real
        if "time_ms" in df.columns and len(df) >= SMOOTH_WINDOW:
            df["time_ms"] = (
                df["time_ms"]
                .rolling(window=SMOOTH_WINDOW, center=True, min_periods=1)
                .median()
            )

        return df

    except Exception as e:
        print(f"Erro lendo {filename}.csv: {e}")
        return None

# ============================================================
# UNIDADE DE TEMPO ADAPTATIVA
# ============================================================

def pick_time_unit(max_time_ms):
    """Escolhe a unidade de tempo real mais legível para o gráfico.
    Retorna (rótulo, fator multiplicador sobre o valor em ms)."""
    if max_time_ms >= 1:
        return "ms", 1
    if max_time_ms >= 1e-3:
        return "µs", 1e3
    return "ns", 1e6

# ============================================================
# CRIA FIGURA COMBINADA (Comparações + Tempo lado a lado)
# ============================================================

def create_figure(title):
    """Cria uma única figura com 2 subplots lado a lado:
    à esquerda Comparações, à direita Tempo."""
    fig, axes = plt.subplots(1, 2, figsize=FIGSIZE_COMBINED)
    fig.suptitle(title, fontsize=FONT_TITLE, fontweight="bold")
    return fig, axes

# ============================================================
# CONFIGURA EIXO (escala real, automática, sem notação 10^X)
# ============================================================

def setup_axis(ax, subtitle, ylabel):
    """Configura rótulos e fontes do eixo. A escala é a real dos dados
    plotados (automática) e os números são formatados como mil/mi/bi
    em vez de notação científica."""
    ax.set_title(subtitle, fontsize=FONT_SUBTITLE)
    ax.set_xlabel("n", fontsize=FONT_AXIS_LABEL)
    ax.set_ylabel(ylabel, fontsize=FONT_AXIS_LABEL)
    ax.tick_params(axis='both', which='major', labelsize=FONT_TICK_LABEL)
    ax.grid(True, alpha=0.3)

    ax.xaxis.set_major_formatter(HUMAN_FORMATTER)
    ax.yaxis.set_major_formatter(HUMAN_FORMATTER)
    ax.set_ylim(bottom=0)

# ============================================================
# LEGENDA PADRONIZADA
# ============================================================

def add_legend(fig, handles, labels, ncol):
    """Adiciona legenda no rodapé da figura com fonte ampliada."""
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
    lado na mesma imagem, em escala real."""

    for struct_id, struct_name, files in STRUCTURES:

        print()
        print("=" * 70)
        print(f"Gerando gráfico: {struct_name} (Comparações + Tempo)")
        print("=" * 70)

        datasets = []
        for filename in files:
            df = load_csv(filename)
            if df is None:
                print(f"[AVISO] Dados não encontrados para {filename}")
                continue
            datasets.append((filename, df))

        if not datasets:
            continue

        # Corta o eixo X no domínio comum: todas as curvas até o MENOR
        # n máximo entre as variantes. Sem isso, uma variante que falhou
        # cedo (ex.: ABB degenerada em n=24 mil) vira uma parede vertical
        # espremida no zero quando outra vai até 7 milhões.
        common_max_n = min(df["n"].max() for _, df in datasets)
        datasets = [(f, df[df["n"] <= common_max_n]) for f, df in datasets]
        print(f"Domínio comum: n até {common_max_n:,.0f}")

        # Unidade de tempo adaptativa: escolhida pelo maior tempo da estrutura
        max_time = max(df["time_ms"].max() for _, df in datasets if "time_ms" in df.columns)
        time_unit, time_factor = pick_time_unit(max_time)

        fig, (ax_comp, ax_time) = create_figure(struct_name)

        legend_handles = []
        legend_labels = []

        for filename, df in datasets:
            disposition_label, color = DISPOSITIONS.get(filename, (filename, "gray"))
            line_for_legend = None

            if "n" in df.columns and "comparisons" in df.columns:
                line, = ax_comp.plot(
                    df["n"],
                    df["comparisons"],
                    color=color,
                    linewidth=LINE_WIDTH,
                    marker="o",
                    markersize=MARKER_SIZE,
                    label=disposition_label
                )
                line_for_legend = line

            if "n" in df.columns and "time_ms" in df.columns:
                line2, = ax_time.plot(
                    df["n"],
                    df["time_ms"] * time_factor,
                    color=color,
                    linewidth=LINE_WIDTH,
                    marker="o",
                    markersize=MARKER_SIZE,
                    label=disposition_label
                )
                if line_for_legend is None:
                    line_for_legend = line2

            if line_for_legend is not None and disposition_label not in legend_labels:
                legend_labels.append(disposition_label)
                legend_handles.append(line_for_legend)

        setup_axis(ax_comp, "Comparações", "Comparações")
        setup_axis(ax_time, f"Tempo ({time_unit})", f"Tempo ({time_unit})")

        if legend_handles:
            add_legend(fig, legend_handles, legend_labels, ncol=len(legend_labels))
            fig.tight_layout(rect=[0, 0.13, 1, 0.90])

            save_figure(fig, f"{struct_id}_comparacoes_tempo")
            plt.close(fig)

            print(f"[OK] Gráfico salvo: {struct_id}_comparacoes_tempo (tempo em {time_unit})")
        else:
            plt.close(fig)

# ============================================================
# GERA GRÁFICO GLOBAL COMPARATIVO (Comparações + Tempo juntos)
# ============================================================

def plot_global_comparisons(struct_ids, title, out_filename):
    """Cria UM gráfico global comparando as estruturas indicadas, com
    Comparações e Tempo lado a lado, em escala real."""

    print()
    print("=" * 70)
    print(f"Gráfico Global: {title}")
    print("=" * 70)

    struct_colors = {
        "seq": "green",
        "bin": "blue",
        "abb": "orange",
        "avl": "red",
    }

    datasets = []
    for struct_id, struct_name, files in STRUCTURES:
        if struct_id not in struct_ids:
            continue
        df = load_csv(files[0])  # primeira variante de cada estrutura
        if df is None:
            print(f"[AVISO] Dados não encontrados para {files[0]}")
            continue
        datasets.append((struct_id, struct_name, df))

    if not datasets:
        return

    # Corta o eixo X no domínio comum entre as estruturas incluídas
    common_max_n = min(df["n"].max() for _, _, df in datasets)
    datasets = [(s, name, df[df["n"] <= common_max_n]) for s, name, df in datasets]
    print(f"Domínio comum: n até {common_max_n:,.0f}")

    max_time = max(df["time_ms"].max() for _, _, df in datasets if "time_ms" in df.columns)
    time_unit, time_factor = pick_time_unit(max_time)

    fig, (ax_comp, ax_time) = create_figure(title)

    legend_handles = []
    legend_labels = []

    for struct_id, struct_name, df in datasets:
        color = struct_colors.get(struct_id, "gray")
        line_for_legend = None

        if "n" in df.columns and "comparisons" in df.columns:
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
            line_for_legend = line

        if "n" in df.columns and "time_ms" in df.columns:
            line2, = ax_time.plot(
                df["n"],
                df["time_ms"] * time_factor,
                color=color,
                linewidth=LINE_WIDTH,
                marker="o",
                markersize=MARKER_SIZE,
                label=struct_name,
                alpha=0.8
            )
            if line_for_legend is None:
                line_for_legend = line2

        if line_for_legend is not None and struct_name not in legend_labels:
            legend_labels.append(struct_name)
            legend_handles.append(line_for_legend)

    setup_axis(ax_comp, "Comparações", "Comparações")
    setup_axis(ax_time, f"Tempo ({time_unit})", f"Tempo ({time_unit})")

    if legend_handles:
        add_legend(fig, legend_handles, legend_labels, ncol=len(legend_labels))
        fig.tight_layout(rect=[0, 0.13, 1, 0.90])
        save_figure(fig, out_filename)
        plt.close(fig)

        print(f"[OK] Gráfico salvo: {out_filename} (tempo em {time_unit})")
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
    print("Escala: real (automática por gráfico), sem notação 10^X")
    print(f"Suavização do tempo: mediana móvel (janela {SMOOTH_WINDOW})")
    print("Unidade de tempo: adaptativa (ns / µs / ms)")
    print("=" * 70)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    plot_by_structure()

    # Global com todas as estruturas: a sequencial (O(n)) domina a escala
    # e as demais ficam rentes ao zero — é a comparação honesta do panorama
    plot_global_comparisons(
        ["seq", "bin", "abb", "avl"],
        "Comparação Global (todas as estruturas)",
        "global_comparacoes_tempo",
    )

    # Global só com as estruturas rápidas (sem a sequencial), para dar
    # para enxergar a diferença entre binária, ABB e AVL
    plot_global_comparisons(
        ["bin", "abb", "avl"],
        "Comparação Global (sem busca sequencial)",
        "global_rapidas_comparacoes_tempo",
    )

    print()
    print("=" * 70)
    print("PROCESSAMENTO FINALIZADO")
    print("=" * 70)
    print()
    print(f"Gráficos salvos em: {OUTPUT_DIR}")

# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    main()
