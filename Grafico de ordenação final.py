import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from pathlib import Path

# ==================== CONFIGURAÇÕES ====================
INPUT_DIR = "output_ordenacao"
GRAFICOS_DIR = "graficos_ordenacao"

# Tamanhos de fonte (do código de inspiração)
FONTE_TITULO = 22
FONTE_LABEL = 18
FONTE_TICK = 14
FONTE_LEGENDA = 16

# Exportação
EXPORT_PNG = True
EXPORT_SVG = True
EXPORT_PDF = False
DPI = 300

# Figsize padrão
FIGSIZE_TRIPLO = (18, 6)
FIGSIZE_UNICO = (12, 8)

os.makedirs(GRAFICOS_DIR, exist_ok=True)

# ==================== ALGORITMOS ====================
ALGORITHMS = [
    ("bubblesort", "Bubble Sort"),
    ("selectionsort", "Selection Sort"),
    ("insertionsort", "Insertion Sort"),
    ("heapsort", "Heap Sort"),
    ("mergesort", "Merge Sort"),
    ("quicksort", "Quick Sort"),
]

# ==================== DISTRIBUIÇÕES ====================
DISTRIBUTIONS = [
    ("random", "Aleatório", "#FFD700"),
    ("ascending", "Crescente", "#0080FF"),
    ("descending", "Decrescente", "#FF0000"),
    ("near_ascending_pct", "Quase Crescente", "#000000"),
    ("near_descending_pct", "Quase Decrescente", "#FF69B4"),
]

# ==================== MÉTRICAS ====================
METRICS = [
    ("comparisons", "Comparações"),
    ("copies", "Cópias"),
    ("time_ms", "Tempo (ms)"),
]

# ==================== FORMATADOR HUMANO ====================
def human_format(value, _pos=None):
    """Formata valores: mil, mi (milhão), bi (bilhão)"""
    if value == 0:
        return "0"
    for div, suffix in ((1e9, " bi"), (1e6, " mi"), (1e3, " mil")):
        if abs(value) >= div:
            txt = f"{value / div:.1f}".rstrip("0").rstrip(".")
            return txt.replace(".", ",") + suffix
    txt = f"{value:.1f}".rstrip("0").rstrip(".")
    return txt.replace(".", ",")

HUMAN_FORMATTER = FuncFormatter(human_format)

# ==================== CARREGAMENTO DE DADOS ====================
def load_csv(filename):
    """Carrega CSV, remove linhas com 'FAIL' e converte tempo para ms"""
    path = Path(INPUT_DIR) / filename

    if not path.exists():
        return None

    try:
        df = pd.read_csv(path)

        # Remove linhas com "FAIL"
        for c in df.columns:
            df = df[df[c] != "FAIL"]

        # Converte para numéricas
        df = df.apply(pd.to_numeric, errors='coerce')
        df = df.dropna()

        # Converte tempo de ns para ms
        if "time_ns" in df.columns:
            df["time_ms"] = df["time_ns"] / 1e6
            df = df.drop(columns=["time_ns"])

        return df if not df.empty else None

    except Exception as e:
        print(f"Erro lendo {filename}: {e}")
        return None

# ==================== CALCULA LIMITES GLOBAIS ====================
def calculate_global_limits():
    """Calcula min/max globais para CADA MÉTRICA em cada escala"""
    global_limits = {
        "log": {"comparisons": [float('inf'), 0], 
                "copies": [float('inf'), 0], 
                "time_ms": [float('inf'), 0]},
        "linear": {"comparisons": [0, 0], 
                   "copies": [0, 0], 
                   "time_ms": [0, 0]}
    }
    
    print("\n" + "=" * 70)
    print("CALCULANDO ESCALAS GLOBAIS")
    print("=" * 70)
    
    for algorithm, _ in ALGORITHMS:
        for dist, _, _ in DISTRIBUTIONS:
            filename = f"{algorithm}_{dist}.csv"
            df = load_csv(filename)
            
            if df is not None:
                for column in ["comparisons", "copies", "time_ms"]:
                    if column in df.columns:
                        min_val = df[column].min()
                        max_val = df[column].max()
                        
                        # Log: sempre calcula
                        if min_val > 0:
                            global_limits["log"][column][0] = min(global_limits["log"][column][0], min_val)
                        global_limits["log"][column][1] = max(global_limits["log"][column][1], max_val)
                        
                        # Linear: máximo é suficiente
                        global_limits["linear"][column][1] = max(global_limits["linear"][column][1], max_val)
    
    print("\nEscala LOG:")
    print(f"  Comparações: [{global_limits['log']['comparisons'][0]:.2e}, {global_limits['log']['comparisons'][1]:.2e}]")
    print(f"  Cópias:      [{global_limits['log']['copies'][0]:.2e}, {global_limits['log']['copies'][1]:.2e}]")
    print(f"  Tempo (ms):  [{global_limits['log']['time_ms'][0]:.2e}, {global_limits['log']['time_ms'][1]:.2e}]")
    
    print("\nEscala LINEAR:")
    print(f"  Comparações: [0, {global_limits['linear']['comparisons'][1]:.2e}]")
    print(f"  Cópias:      [0, {global_limits['linear']['copies'][1]:.2e}]")
    print(f"  Tempo (ms):  [0, {global_limits['linear']['time_ms'][1]:.2e}]")
    print("=" * 70)
    
    return global_limits

GLOBAL_LIMITS = calculate_global_limits()

# ==================== CONFIGURAÇÃO DE EIXOS ====================
def setup_axis(ax, ylabel, column, use_log=True):
    """Configura eixos com formatação e escala GLOBAL IDÊNTICA"""
    ax.set_xlabel("n", fontsize=FONTE_LABEL, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=FONTE_LABEL, fontweight='bold')
    ax.yaxis.set_major_formatter(HUMAN_FORMATTER)
    ax.tick_params(axis='both', which='major', labelsize=FONTE_TICK)
    ax.grid(True, which='both', alpha=0.3, linestyle='--', linewidth=0.7)
    
    escala_tipo = "log" if use_log else "linear"
    
    if use_log:
        ax.set_yscale('log')
        ax.set_xscale('log')
        min_val, max_val = GLOBAL_LIMITS[escala_tipo][column]
        if min_val > 0 and max_val > min_val:
            ax.set_ylim(min_val * 0.9, max_val * 1.1)
    else:
        max_val = GLOBAL_LIMITS[escala_tipo][column][1]
        if max_val > 0:
            ax.set_ylim(0, max_val * 1.1)

# ==================== SALVAMENTO ====================
def save_figure(fig, filename):
    """Salva figura nos formatos especificados"""
    path = Path(GRAFICOS_DIR)
    
    if EXPORT_PNG:
        fig.savefig(path / f"{filename}.png", dpi=DPI, bbox_inches="tight")
    if EXPORT_SVG:
        fig.savefig(path / f"{filename}.svg", bbox_inches="tight")
    if EXPORT_PDF:
        fig.savefig(path / f"{filename}.pdf", bbox_inches="tight")
    
    print(f"✓ {filename}")

# ==================== TIPO 1: TRIPLO (3 GRÁFICOS) ====================
def plot_algorithm_triplo(algorithm, algo_label, use_log=True):
    """Cria 3 gráficos (Comparações, Cópias, Tempo) lado a lado"""
    
    datasets = []
    for dist, label, color in DISTRIBUTIONS:
        filename = f"{algorithm}_{dist}.csv"
        df = load_csv(filename)
        if df is not None:
            datasets.append((df, label, color))
    
    if not datasets:
        return
    
    fig, axes = plt.subplots(1, 3, figsize=FIGSIZE_TRIPLO)
    escala_txt = "" if use_log else " (Linear)"
    fig.suptitle(f"{algo_label}{escala_txt}", fontsize=FONTE_TITULO, fontweight='bold')
    
    legend_handles = []
    legend_labels = []
    
    for df, label, color in datasets:
        for ax, (column, ylabel) in zip(axes, METRICS):
            if "n" not in df.columns or column not in df.columns:
                continue
            
            line, = ax.plot(df["n"], df[column], color=color, linewidth=2.5,
                           marker='o', markersize=4, label=label, alpha=0.85)
            setup_axis(ax, ylabel, column, use_log=use_log)
            
            if label not in legend_labels:
                legend_labels.append(label)
                legend_handles.append(line)
    
    fig.legend(legend_handles, legend_labels, loc='lower center',
              ncol=5, fontsize=FONTE_LEGENDA, framealpha=0.95, 
              bbox_to_anchor=(0.5, -0.05))
    
    fig.tight_layout(rect=[0, 0.08, 1, 0.96])
    escala_sufixo = "_log" if use_log else "_linear"
    save_figure(fig, f"{algorithm}_triplo{escala_sufixo}")
    plt.close(fig)

# ==================== TIPO 2: GRÁFICOS INDIVIDUAIS ====================
def plot_algorithm_individual(algorithm, algo_label, use_log=True):
    """Cria 3 gráficos individuais (um por métrica)"""
    
    datasets = []
    for dist, label, color in DISTRIBUTIONS:
        filename = f"{algorithm}_{dist}.csv"
        df = load_csv(filename)
        if df is not None:
            datasets.append((df, label, color))
    
    if not datasets:
        return
    
    for column, ylabel in METRICS:
        fig, ax = plt.subplots(figsize=FIGSIZE_UNICO)
        escala_txt = "" if use_log else " (Linear)"
        fig.suptitle(f"{algo_label} - {ylabel}{escala_txt}", 
                    fontsize=FONTE_TITULO, fontweight='bold')
        
        legend_handles = []
        legend_labels = []
        
        for df, label, color in datasets:
            if "n" not in df.columns or column not in df.columns:
                continue
            
            line, = ax.plot(df["n"], df[column], color=color, linewidth=2.5,
                           marker='o', markersize=5, label=label, alpha=0.85)
            
            if label not in legend_labels:
                legend_labels.append(label)
                legend_handles.append(line)
        
        setup_axis(ax, ylabel, column, use_log=use_log)
        ax.legend(legend_handles, legend_labels, loc='upper left',
                 fontsize=FONTE_LEGENDA, framealpha=0.95)
        
        fig.tight_layout()
        col_name = column.replace("_", "").lower()
        escala_sufixo = "_log" if use_log else "_linear"
        save_figure(fig, f"{algorithm}_{col_name}{escala_sufixo}")
        plt.close(fig)

# ==================== TIPO 3: TODOS OS ALGORITMOS JUNTOS (ALEATÓRIO) ====================
def plot_all_algorithms_random(use_log=True):
    """Todos os algoritmos com distribuição aleatória em um gráfico"""
    
    colors_algo = {
        "bubblesort": "#000000",
        "selectionsort": "#303030",
        "insertionsort": "#515151",
        "heapsort": "#0080FF",
        "mergesort": "#ACB900",
        "quicksort": "#FF0000",
    }
    
    markers_algo = {
        "bubblesort": "D",
        "selectionsort": "s",
        "insertionsort": "o",
        "heapsort": "v",
        "mergesort": "p",
        "quicksort": "*",
    }
    
    datasets = []
    for algorithm, algo_label in ALGORITHMS:
        filename = f"{algorithm}_random.csv"
        df = load_csv(filename)
        if df is not None:
            datasets.append((df, algo_label, colors_algo[algorithm], 
                           markers_algo[algorithm]))
    
    if not datasets:
        return
    
    # Triplo: 3 métricas lado a lado
    fig, axes = plt.subplots(1, 3, figsize=FIGSIZE_TRIPLO)
    escala_txt = "" if use_log else " (Linear)"
    fig.suptitle(f"Comparação de Algoritmos - Distribuição Aleatória{escala_txt}", 
                fontsize=FONTE_TITULO, fontweight='bold')
    
    legend_handles = []
    legend_labels = []
    
    for df, algo_label, color, marker in datasets:
        for ax, (column, ylabel) in zip(axes, METRICS):
            if "n" not in df.columns or column not in df.columns:
                continue
            
            line, = ax.plot(df["n"], df[column], color=color, linewidth=2.5,
                           marker=marker, markersize=5, label=algo_label, alpha=0.85)
            setup_axis(ax, ylabel, column, use_log=use_log)
            
            if algo_label not in legend_labels:
                legend_labels.append(algo_label)
                legend_handles.append(line)
    
    fig.legend(legend_handles, legend_labels, loc='lower center',
              ncol=3, fontsize=FONTE_LEGENDA, framealpha=0.95,
              bbox_to_anchor=(0.5, -0.05))
    
    fig.tight_layout(rect=[0, 0.08, 1, 0.96])
    escala_sufixo = "_log" if use_log else "_linear"
    save_figure(fig, f"todos_aleatorio_triplo{escala_sufixo}")
    plt.close(fig)
    
    # Gráficos individuais
    for column, ylabel in METRICS:
        fig, ax = plt.subplots(figsize=FIGSIZE_UNICO)
        escala_txt = "" if use_log else " (Linear)"
        fig.suptitle(f"Comparação de Algoritmos - {ylabel} (Aleatório){escala_txt}",
                    fontsize=FONTE_TITULO, fontweight='bold')
        
        legend_handles = []
        legend_labels = []
        
        for df, algo_label, color, marker in datasets:
            if "n" not in df.columns or column not in df.columns:
                continue
            
            line, = ax.plot(df["n"], df[column], color=color, linewidth=2.5,
                           marker=marker, markersize=5, label=algo_label, alpha=0.85)
            
            if algo_label not in legend_labels:
                legend_labels.append(algo_label)
                legend_handles.append(line)
        
        setup_axis(ax, ylabel, column, use_log=use_log)
        ax.legend(legend_handles, legend_labels, loc='upper left',
                 fontsize=FONTE_LEGENDA, framealpha=0.95, ncol=2)
        
        fig.tight_layout()
        col_name = column.replace("_", "").lower()
        escala_sufixo = "_log" if use_log else "_linear"
        save_figure(fig, f"todos_aleatorio_{col_name}{escala_sufixo}")
        plt.close(fig)

# ==================== TIPO 4: DESTAQUE POR ALGORITMO (ALEATÓRIO) ====================
def plot_all_algorithms_random_destaque(use_log=True):
    """Todos os algoritmos aleatório com destaque individual - SEM LEGENDA REPETIDA"""
    
    colors_algo = {
        "bubblesort": "#000000",
        "selectionsort": "#303030",
        "insertionsort": "#515151",
        "heapsort": "#0080FF",
        "mergesort": "#ACB900",
        "quicksort": "#FF0000",
    }
    
    markers_algo = {
        "bubblesort": "D",
        "selectionsort": "s",
        "insertionsort": "o",
        "heapsort": "v",
        "mergesort": "p",
        "quicksort": "*",
    }
    
    # Carrega todos os dados
    all_datasets = []
    for algorithm, algo_label in ALGORITHMS:
        filename = f"{algorithm}_random.csv"
        df = load_csv(filename)
        if df is not None:
            all_datasets.append({
                'df': df,
                'algo_label': algo_label,
                'algorithm': algorithm,
                'color': colors_algo[algorithm],
                'marker': markers_algo[algorithm]
            })
    
    if not all_datasets:
        return
    
    # Cria versão com destaque para cada algoritmo
    for target_data in all_datasets:
        target_algorithm = target_data['algorithm']
        target_label = target_data['algo_label']
        
        fig, axes = plt.subplots(1, 3, figsize=FIGSIZE_TRIPLO)
        escala_txt = "" if use_log else " (Linear)"
        fig.suptitle(f"Destaque: {target_label} (Aleatório){escala_txt}",
                    fontsize=FONTE_TITULO, fontweight='bold')
        
        # Plota em cinza claro (background)
        for data in all_datasets:
            if data['algorithm'] != target_algorithm:
                df = data['df']
                marker = data['marker']
                
                for ax, (column, ylabel) in zip(axes, METRICS):
                    if "n" not in df.columns or column not in df.columns:
                        continue
                    ax.plot(df["n"], df[column], color='#CCCCCC', linewidth=1.5,
                           marker=marker, markersize=3, alpha=0.3)
                    setup_axis(ax, ylabel, column, use_log=use_log)
        
        # Plota em destaque (foreground)
        for data in all_datasets:
            if data['algorithm'] == target_algorithm:
                df = data['df']
                color = data['color']
                marker = data['marker']
                algo_label = data['algo_label']
                
                for ax, (column, ylabel) in zip(axes, METRICS):
                    if "n" not in df.columns or column not in df.columns:
                        continue
                    
                    ax.plot(df["n"], df[column], color=color, linewidth=3.5,
                           marker=marker, markersize=7, label=algo_label, alpha=0.95)
                    setup_axis(ax, ylabel, column, use_log=use_log)
        
        fig.tight_layout()
        escala_sufixo = "_log" if use_log else "_linear"
        save_figure(fig, f"destaque_{target_algorithm}_aleatorio{escala_sufixo}")
        plt.close(fig)

# ==================== TIPO 5: SEPARADO POR MÉTRICA ====================
def plot_metric_separate(use_log=True):
    """Todos os algoritmos e distribuições separados por métrica - LEGENDA ÚNICA"""
    
    colors_algo = {
        "bubblesort": "#000000",
        "selectionsort": "#303030",
        "insertionsort": "#515151",
        "heapsort": "#0080FF",
        "mergesort": "#ACB900",
        "quicksort": "#FF0000",
    }
    
    for column, ylabel in METRICS:
        fig, axes = plt.subplots(2, 3, figsize=(16, 10))
        axes = axes.flatten()
        
        escala_txt = "" if use_log else " (Linear)"
        fig.suptitle(f"{ylabel} - Todos os Algoritmos{escala_txt}",
                    fontsize=FONTE_TITULO, fontweight='bold')
        
        # Coleta todas as linhas para legenda única
        all_legend_handles = []
        all_legend_labels = []
        
        for idx, (algorithm, algo_label) in enumerate(ALGORITHMS):
            ax = axes[idx]
            
            for dist, dist_label, color in DISTRIBUTIONS:
                filename = f"{algorithm}_{dist}.csv"
                df = load_csv(filename)
                
                if df is not None and "n" in df.columns and column in df.columns:
                    line, = ax.plot(df["n"], df[column], color=color, linewidth=2,
                                   marker='o', markersize=3, label=dist_label, alpha=0.85)
                    
                    # Coleta para legenda única
                    if dist_label not in all_legend_labels:
                        all_legend_labels.append(dist_label)
                        all_legend_handles.append(line)
            
            ax.set_title(algo_label, fontsize=FONTE_LABEL, fontweight='bold')
            setup_axis(ax, ylabel, column, use_log=use_log)
        
        # Remove último subplot vazio
        if len(ALGORITHMS) < len(axes):
            fig.delaxes(axes[-1])
        
        # Legenda única embaixo
        fig.legend(all_legend_handles, all_legend_labels, loc='lower center',
                  ncol=5, fontsize=FONTE_LEGENDA, framealpha=0.95,
                  bbox_to_anchor=(0.5, -0.02))
        
        fig.tight_layout(rect=[0, 0.05, 1, 0.96])
        col_name = column.replace("_", "").lower()
        escala_sufixo = "_log" if use_log else "_linear"
        save_figure(fig, f"separado_metrica_{col_name}{escala_sufixo}")
        plt.close(fig)

# ==================== TIPO 6: COMPARAÇÃO POR DISTRIBUIÇÃO ====================
def plot_distribution_comparison(use_log=True):
    """Cada distribuição em um painel mostrando todos os algoritmos - LEGENDA ÚNICA"""
    
    colors_algo = {
        "bubblesort": "#000000",
        "selectionsort": "#303030",
        "insertionsort": "#515151",
        "heapsort": "#0080FF",
        "mergesort": "#ACB900",
        "quicksort": "#FF0000",
    }
    
    for dist_key, dist_label, _ in DISTRIBUTIONS:
        fig, axes = plt.subplots(1, 3, figsize=FIGSIZE_TRIPLO)
        escala_txt = "" if use_log else " (Linear)"
        fig.suptitle(f"Distribuição: {dist_label}{escala_txt}",
                    fontsize=FONTE_TITULO, fontweight='bold')
        
        legend_handles = []
        legend_labels = []
        
        for algorithm, algo_label in ALGORITHMS:
            filename = f"{algorithm}_{dist_key}.csv"
            df = load_csv(filename)
            
            if df is not None:
                for ax, (column, ylabel) in zip(axes, METRICS):
                    if "n" not in df.columns or column not in df.columns:
                        continue
                    
                    line, = ax.plot(df["n"], df[column], 
                                   color=colors_algo[algorithm], linewidth=2.5,
                                   marker='o', markersize=4, label=algo_label, alpha=0.85)
                    setup_axis(ax, ylabel, column, use_log=use_log)
                    
                    if algo_label not in legend_labels:
                        legend_labels.append(algo_label)
                        legend_handles.append(line)
        
        fig.legend(legend_handles, legend_labels, loc='lower center',
                  ncol=3, fontsize=FONTE_LEGENDA, framealpha=0.95,
                  bbox_to_anchor=(0.5, -0.05))
        
        fig.tight_layout(rect=[0, 0.08, 1, 0.96])
        escala_sufixo = "_log" if use_log else "_linear"
        save_figure(fig, f"distribuicao_{dist_key}{escala_sufixo}")
        plt.close(fig)

# ==================== TIPO 7: HEATMAP-STYLE (RESUMO) ====================
def plot_summary_overview(use_log=True):
    """Visão geral simplificada de todos os dados"""
    
    # Pega máximo de n e valor máximo para cada métrica
    for column, ylabel in METRICS:
        fig, ax = plt.subplots(figsize=(14, 8))
        
        data_points = []
        
        for algorithm, algo_label in ALGORITHMS:
            for dist_key, dist_label, dist_color in DISTRIBUTIONS:
                filename = f"{algorithm}_{dist_key}.csv"
                df = load_csv(filename)
                
                if df is not None and "n" in df.columns and column in df.columns:
                    max_n = df["n"].max()
                    max_val = df[column].max()
                    data_points.append({
                        'algo': algo_label,
                        'dist': dist_label,
                        'n': max_n,
                        'value': max_val,
                        'color': dist_color
                    })
        
        # Agrupa por algoritmo
        algos = sorted(set(d['algo'] for d in data_points))
        dists = sorted(set(d['dist'] for d in data_points))
        
        for algo in algos:
            algo_data = [d for d in data_points if d['algo'] == algo]
            algo_data.sort(key=lambda x: x['n'])
            
            colors_for_line = [d['color'] for d in algo_data]
            values = [d['value'] for d in algo_data]
            ns = [d['n'] for d in algo_data]
            
            ax.plot(range(len(algo_data)), values, marker='o', 
                   label=algo, linewidth=2, markersize=6, alpha=0.8)
        
        ax.set_xlabel("Distribuições", fontsize=FONTE_LABEL, fontweight='bold')
        ax.set_ylabel(ylabel, fontsize=FONTE_LABEL, fontweight='bold')
        escala_txt = "" if use_log else " (Linear)"
        ax.set_title(f"Resumo - {ylabel}{escala_txt}",
                    fontsize=FONTE_TITULO, fontweight='bold')
        ax.set_xticks(range(len(dists)))
        ax.set_xticklabels(dists, rotation=45, ha='right')
        ax.tick_params(axis='both', which='major', labelsize=FONTE_TICK)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=FONTE_LEGENDA-2, loc='best', ncol=2, framealpha=0.95)
        
        if use_log:
            ax.set_yscale('log')
        
        fig.tight_layout()
        col_name = column.replace("_", "").lower()
        escala_sufixo = "_log" if use_log else "_linear"
        save_figure(fig, f"resumo_{col_name}{escala_sufixo}")
        plt.close(fig)

# ==================== MAIN ====================
def main():
    print("=" * 70)
    print("GERADOR AUTOMÁTICO DE GRÁFICOS DE ORDENAÇÃO")
    print("=" * 70)
    print(f"Saída: {GRAFICOS_DIR}")
    
    escalas = [
        (True, "LOGARÍTMICA"),
        (False, "LINEAR")
    ]
    
    for use_log, escala_nome in escalas:
        print(f"\n{'#'*70}")
        print(f"# GERANDO VERSÃO {escala_nome}")
        print(f"{'#'*70}")
        
        # Tipo 1: Triplo para cada algoritmo
        print(f"\n[1/7] Gerando gráficos triplos ({escala_nome})...")
        for algorithm, algo_label in ALGORITHMS:
            plot_algorithm_triplo(algorithm, algo_label, use_log=use_log)
        
        # Tipo 2: Individual por métrica
        print(f"\n[2/7] Gerando gráficos individuais ({escala_nome})...")
        for algorithm, algo_label in ALGORITHMS:
            plot_algorithm_individual(algorithm, algo_label, use_log=use_log)
        
        # Tipo 3: Todos os algoritmos (aleatório)
        print(f"\n[3/7] Gerando comparativo todos os algoritmos ({escala_nome})...")
        plot_all_algorithms_random(use_log=use_log)
        
        # Tipo 4: Destaque
        print(f"\n[4/7] Gerando gráficos com destaque ({escala_nome})...")
        plot_all_algorithms_random_destaque(use_log=use_log)
        
        # Tipo 5: Separado por métrica
        print(f"\n[5/7] Gerando gráficos separados por métrica ({escala_nome})...")
        plot_metric_separate(use_log=use_log)
        
        # Tipo 6: Por distribuição
        print(f"\n[6/7] Gerando comparação por distribuição ({escala_nome})...")
        plot_distribution_comparison(use_log=use_log)
        
        # Tipo 7: Resumo
        print(f"\n[7/7] Gerando resumo visual ({escala_nome})...")
        plot_summary_overview(use_log=use_log)
    
    print("\n" + "=" * 70)
    print("✓ PROCESSAMENTO FINALIZADO")
    print(f"✓ Gráficos salvos em: {GRAFICOS_DIR}")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()