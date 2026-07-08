import os
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================================
# CONFIGURAÇÃO
# ============================================================

INPUT_DIR = "output_ordenacao"
OUTPUT_DIR = "graficos_10a10"

EXPORT_PNG = True
EXPORT_SVG = True
EXPORT_PDF = False

USE_LOG_SCALE = False

FIGSIZE = (18, 6)
DPI = 300

# Escala Y máxima (1 * 10^7)
Y_MAX_SCALE = 1e10

# ============================================================
# ALGORITMOS
# ============================================================

ALGORITHMS = [
    ("bubblesort", "Bubble Sort"),
    ("selectionsort", "Selection Sort"),
    ("insertionsort", "Insertion Sort"),
    ("shellsort", "Shell Sort"),
    ("heapsort", "Heap Sort"),
    ("mergesort", "Merge Sort"),
    ("quicksort", "Quick Sort"),
]

# ============================================================
# DISTRIBUIÇÕES
# ============================================================

DISTRIBUTIONS = [
    ("random", "Aleatório", "yellow"),
    ("ascending", "Crescente", "blue"),
    ("descending", "Decrescente", "red"),
    ("near_ascending_pct", "Quase crescente", "black"),
    ("near_descending_pct", "Quase decrescente", "pink"),
]

# ============================================================
# MÉTRICAS
# ============================================================

METRICS = [
    ("comparisons", "Comparações"),
    ("copies", "Cópias"),
    ("time_ms", "Tempo (ms)"),
]

# ============================================================
# ESCALAS GLOBAIS
# ============================================================

GLOBAL_MAX = {
    "comparisons": 0,
    "copies": 0,
    "time_ms": 0
}

# ============================================================
# LEITURA DOS CSVs
# ============================================================

def load_csv(filename):
    """Carrega CSV e remove linhas com 'FAIL'"""
    path = Path(INPUT_DIR) / filename

    if not path.exists():
        print(f"[AVISO] Arquivo não encontrado: {filename}")
        return None

    try:
        df = pd.read_csv(path)

        # Remove linhas com "FAIL" em qualquer coluna
        for c in df.columns:
            df = df[df[c] != "FAIL"]

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
        print(f"Erro lendo {filename}: {e}")
        return None

# ============================================================
# CALCULA ESCALAS
# ============================================================

def calculate_global_limits():
    """Calcula os valores máximos para cada métrica em todos os dados"""
    print()
    print("=" * 70)
    print("CALCULANDO ESCALAS GLOBAIS")
    print("=" * 70)

    for algorithm, _ in ALGORITHMS:
        for dist, _, _ in DISTRIBUTIONS:
            filename = f"{algorithm}_{dist}.csv"
            df = load_csv(filename)

            if df is None:
                continue

            for column in GLOBAL_MAX:
                if column in df.columns:
                    value = df[column].max()
                    if value > GLOBAL_MAX[column]:
                        GLOBAL_MAX[column] = value

    print()
    print(f"Máximo Comparações : {GLOBAL_MAX['comparisons']:,.0f}")
    print(f"Máximo Cópias      : {GLOBAL_MAX['copies']:,.0f}")
    print(f"Máximo Tempo (ms)  : {GLOBAL_MAX['time_ms']:,.6f}")
    print()

# ============================================================
# CRIA FIGURA
# ============================================================

def create_figure(title):
    """Cria figura com 3 subplots (um para cada métrica)"""
    fig, axes = plt.subplots(1, 3, figsize=FIGSIZE)
    fig.suptitle(title, fontsize=16, fontweight="bold")
    return fig, axes

# ============================================================
# CONFIGURA EIXOS
# ============================================================

def setup_axis(ax, ylabel, maximum):
    """Configura rótulos e escalas do eixo com máximo de 1*10^7"""
    ax.set_xlabel("n")
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)

    if USE_LOG_SCALE:
        ax.set_yscale("log")
    else:
        # Define escala Y com limite máximo de 1*10^7
        if maximum > 0:
            y_limit = min(maximum * 1.1, Y_MAX_SCALE)
        else:
            y_limit = Y_MAX_SCALE
        
        ax.set_ylim(0, y_limit)
        
        # Formata eixo Y em notação científica
        ax.ticklabel_format(style='scientific', axis='y', scilimits=(0, 0))

# ============================================================
# SALVAR FIGURA
# ============================================================

def save_figure(fig, filename):
    """Salva figura nos formatos especificados"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = Path(OUTPUT_DIR)

    if EXPORT_PNG:
        fig.savefig(
            path / f"{filename}.png",
            dpi=DPI,
            bbox_inches="tight"
        )

    if EXPORT_SVG:
        fig.savefig(
            path / f"{filename}.svg",
            bbox_inches="tight"
        )

    if EXPORT_PDF:
        fig.savefig(
            path / f"{filename}.pdf",
            bbox_inches="tight"
        )

# ============================================================
# GERA GRAFICO DE UM ALGORITMO
# ============================================================

def plot_algorithm(algorithm, title):
    """Cria gráfico comparativo de um algoritmo em diferentes distribuições"""
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)

    datasets = []

    # Carrega dados de todas as distribuições
    for dist, label, color in DISTRIBUTIONS:
        filename = f"{algorithm}_{dist}.csv"
        df = load_csv(filename)

        if df is not None:
            datasets.append((df, label, color))

    if not datasets:
        print("[AVISO] Nenhum dado encontrado para este algoritmo.")
        return

    fig, axes = create_figure(title)

    legend_handles = []
    legend_labels = []

    # Plota dados em cada métrica
    for df, label, color in datasets:
        for ax, (column, ylabel) in zip(axes, METRICS):
            
            # Verifica se a coluna existe no DataFrame
            if "n" not in df.columns or column not in df.columns:
                print(f"[AVISO] Coluna faltante em {label}: {column}")
                continue

            try:
                line, = ax.plot(
                    df["n"],
                    df[column],
                    color=color,
                    linewidth=2,
                    marker="o",
                    markersize=3,
                    label=label
                )

                setup_axis(ax, ylabel, GLOBAL_MAX[column])

                # Adiciona à legenda apenas uma vez
                if label not in legend_labels:
                    legend_labels.append(label)
                    legend_handles.append(line)

            except Exception as e:
                print(f"[ERRO] Ao plotar {label} em {ylabel}: {e}")
                continue

    # Configura legenda e layout
    fig.legend(
        legend_handles,
        legend_labels,
        loc="lower center",
        ncol=len(legend_labels),
        fontsize=10
    )

    fig.tight_layout(rect=[0, 0.08, 1, 0.95])

    # Salva figura
    save_figure(fig, algorithm)
    plt.close(fig)

    print(f"[OK] Gráfico salvo: {algorithm}")

# ============================================================
# MAIN
# ============================================================

def main():
    """Função principal"""
    print("=" * 70)
    print("GERADOR AUTOMÁTICO DE GRÁFICOS DE ORDENAÇÃO")
    print("=" * 70)
    print(f"Escala Y máxima: {Y_MAX_SCALE:.0e}")
    print("Unidade de tempo: milissegundos (ms)")
    print("=" * 70)

    # Cria diretório de saída
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Calcula escalas globais
    calculate_global_limits()

    # Gera gráfico para cada algoritmo
    for algorithm, title in ALGORITHMS:
        plot_algorithm(algorithm, title)

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