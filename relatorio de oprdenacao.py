import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from pathlib import Path
from datetime import datetime

def human_format(value, _pos=None):
    """Formata valores dos eixos em português: mil, mi (milhão), bi (bilhão).
    Ex.: 10_000_000_000 -> "10 bi", 1_500_000 -> "1,5 mi", 500 -> "500"."""
    if value == 0:
        return "0"
    for div, suffix in ((1e9, " bi"), (1e6, " mi"), (1e3, " mil")):
        if abs(value) >= div:
            txt = f"{value / div:.1f}".rstrip("0").rstrip(".")
            return txt.replace(".", ",") + suffix
    txt = f"{value:.1f}".rstrip("0").rstrip(".")
    return txt.replace(".", ",")

HUMAN_FORMATTER = FuncFormatter(human_format)

# ============================================================
# CONFIGURAÇÃO
# ============================================================

INPUT_DIR = "output_ordenacao"
REPORTS_DIR = "relatorios"

GENERATE_GERAL = True
GERAL_OUTPUT_DIR = "graficos_geral"

GENERATE_NORMAL = True
NORMAL_OUTPUT_DIR = "graficos_ordenacao"

EXPORT_PNG = True
EXPORT_SVG = True
EXPORT_PDF = False

USE_LOG_SCALE = False

FIGSIZE = (18, 6)
DPI = 300

# ============================================================
# ESTRUTURAS - ORDEM DAS LINHAS
# ============================================================

ESTRUTURAS_ORDEM = [
    ("bubblesort", "Bubble Sort"),
    ("selectionsort", "Selection Sort"),
    ("insertionsort", "Insertion Sort"),
    ("shellsort", "Shell Sort"),
    ("heapsort", "Heap Sort"),
    ("mergesort", "Merge Sort"),
    ("quicksort", "Quick Sort"),
]

ESTRUTURAS = {k: v for k, v in ESTRUTURAS_ORDEM}
FILES = [k for k, _ in ESTRUTURAS_ORDEM]

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
    """Carrega CSV, remove linhas com 'FAIL' e converte tempo para ms"""
    path = Path(INPUT_DIR) / filename

    if not path.exists():
        return None, []

    try:
        df = pd.read_csv(path)
        
        # Registrar linhas com FAIL
        fail_rows = df[df.isin(["FAIL"]).any(axis=1)]
        fail_n_values = fail_rows['n'].tolist() if not fail_rows.empty else []

        for c in df.columns:
            df = df[df[c] != "FAIL"]

        df = df.apply(pd.to_numeric, errors='coerce')
        df = df.dropna()

        if "time_ns" in df.columns:
            df["time_ms"] = df["time_ns"] / 1e6
            df = df.drop(columns=["time_ns"])

        return (df if not df.empty else None), fail_n_values

    except Exception as e:
        print(f"Erro lendo {filename}: {e}")
        return None, []

# ============================================================
# CALCULA ÁREA ABAIXO DA CURVA
# ============================================================

def calcular_area_abaixo_curva(x, y):
    """
    Calcula a área abaixo da curva usando a regra dos trapézios.
    """
    indices = np.argsort(x)
    x_sorted = x[indices]
    y_sorted = y[indices]
    
    area = np.trapezoid(y_sorted, x_sorted)
    
    return area

# ============================================================
# CALCULA ESCALAS
# ============================================================

def calculate_global_limits():
    """Calcula os valores máximos para cada métrica em todos os dados"""
    print()
    print("=" * 70)
    print("CALCULANDO ESCALAS GLOBAIS")
    print("=" * 70)

    for algorithm in FILES:
        for dist, _, _ in DISTRIBUTIONS:
            filename = f"{algorithm}_{dist}.csv"
            df, _ = load_csv(filename)

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
# GERA ESTATÍSTICAS POR ALGORITMO
# ============================================================

def generate_statistics():
    """Gera estatísticas de todos os algoritmos e distribuições"""
    stats_list = []
    
    for algorithm in FILES:
        algo_name = ESTRUTURAS[algorithm]
        for dist, dist_name, _ in DISTRIBUTIONS:
            filename = f"{algorithm}_{dist}.csv"
            df, _ = load_csv(filename)
            
            if df is None:
                continue
            
            stats_dict = {
                'Algoritmo': algo_name,
                'Distribuição': dist_name,
                'n_max': int(df['n'].max()) if 'n' in df.columns else 0,
                'Comparações_min': f"{df['comparisons'].min():.0f}" if 'comparisons' in df.columns else "N/A",
                'Comparações_médio': f"{df['comparisons'].mean():.0f}" if 'comparisons' in df.columns else "N/A",
                'Comparações_max': f"{df['comparisons'].max():.0f}" if 'comparisons' in df.columns else "N/A",
                'Cópias_min': f"{df['copies'].min():.0f}" if 'copies' in df.columns else "N/A",
                'Cópias_médio': f"{df['copies'].mean():.0f}" if 'copies' in df.columns else "N/A",
                'Cópias_max': f"{df['copies'].max():.0f}" if 'copies' in df.columns else "N/A",
                'Tempo_min_ms': f"{df['time_ms'].min():.6f}" if 'time_ms' in df.columns else "N/A",
                'Tempo_médio_ms': f"{df['time_ms'].mean():.6f}" if 'time_ms' in df.columns else "N/A",
                'Tempo_max_ms': f"{df['time_ms'].max():.6f}" if 'time_ms' in df.columns else "N/A",
            }
            stats_list.append(stats_dict)
    
    return pd.DataFrame(stats_list)

# ============================================================
# SALVA TABELA EM TSV
# ============================================================

def save_table_tsv(df, filename):
    """Salva tabela em formato TSV"""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    path = Path(REPORTS_DIR) / filename
    
    df.to_csv(path, sep='\t', index=False, encoding='utf-8')
    print(f"[OK] Tabela salva em TSV: {path}")

# ============================================================
# GERA RELATÓRIO EM TEXTO
# ============================================================

def generate_text_report(fail_info):
    """Gera relatório em arquivo TXT"""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    with open(Path(REPORTS_DIR) / "relatorio.txt", "w", encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("RELATÓRIO DE ANÁLISE DE ALGORITMOS DE ORDENAÇÃO\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Data/Hora: {timestamp}\n")
        f.write(f"Diretório de entrada: {INPUT_DIR}\n\n")
        
        f.write("ESCALAS GLOBAIS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Máximo de Comparações: {GLOBAL_MAX['comparisons']:,.0f}\n")
        f.write(f"Máximo de Cópias:      {GLOBAL_MAX['copies']:,.0f}\n")
        f.write(f"Máximo de Tempo (ms):  {GLOBAL_MAX['time_ms']:,.6f}\n\n")
        
        f.write("ALGORITMOS ANALISADOS\n")
        f.write("-" * 80 + "\n")
        for algorithm in FILES:
            f.write(f"  • {ESTRUTURAS[algorithm]}\n")
        f.write("\n")
        
        f.write("DISTRIBUIÇÕES ANALISADAS\n")
        f.write("-" * 80 + "\n")
        for dist, dist_name, _ in DISTRIBUTIONS:
            f.write(f"  • {dist_name}\n")
        f.write("\n")
        
        if fail_info:
            f.write("FALHAS DETECTADAS\n")
            f.write("-" * 80 + "\n")
            for filename, info in fail_info.items():
                f.write(f"\n{info['estrutura']}:\n")
                f.write(f"  Falhas detectadas em n = {info['fail_points']}\n")
                f.write(f"  Primeiro ponto de falha: {info['fail_points'][0]}\n")
                f.write(f"  Total de pontos com falha: {len(info['fail_points'])}\n")
        
        f.write("\n\nESTATÍSTICAS DETALHADAS\n")
        f.write("-" * 80 + "\n\n")
        
        # Gera estatísticas por algoritmo
        for algorithm in FILES:
            algo_name = ESTRUTURAS[algorithm]
            f.write(f"\n{algo_name.upper()}\n")
            f.write("=" * 80 + "\n")
            
            for dist, dist_name, _ in DISTRIBUTIONS:
                filename = f"{algorithm}_{dist}.csv"
                df, _ = load_csv(filename)
                
                if df is None:
                    f.write(f"\n  {dist_name}: [Sem dados]\n")
                    continue
                
                f.write(f"\n  {dist_name}:\n")
                f.write(f"    Tamanho máximo (n):        {int(df['n'].max())}\n")
                
                if 'comparisons' in df.columns:
                    f.write(f"    Comparações - Mín:        {df['comparisons'].min():,.0f}\n")
                    f.write(f"    Comparações - Médio:      {df['comparisons'].mean():,.0f}\n")
                    f.write(f"    Comparações - Máx:        {df['comparisons'].max():,.0f}\n")
                
                if 'copies' in df.columns:
                    f.write(f"    Cópias - Mín:             {df['copies'].min():,.0f}\n")
                    f.write(f"    Cópias - Médio:           {df['copies'].mean():,.0f}\n")
                    f.write(f"    Cópias - Máx:             {df['copies'].max():,.0f}\n")
                
                if 'time_ms' in df.columns:
                    f.write(f"    Tempo (ms) - Mín:         {df['time_ms'].min():,.6f}\n")
                    f.write(f"    Tempo (ms) - Médio:       {df['time_ms'].mean():,.6f}\n")
                    f.write(f"    Tempo (ms) - Máx:         {df['time_ms'].max():,.6f}\n")
                    
                    # Calcula área abaixo da curva
                    if 'n' in df.columns:
                        area = calcular_area_abaixo_curva(df['n'].values, df['time_ms'].values)
                        f.write(f"    Área tempo (ms):          {area:,.6f}\n")
    
    print(f"[OK] Relatório TXT salvo: {Path(REPORTS_DIR) / 'relatorio.txt'}")

# ============================================================
# GERA COMPARATIVO RESUMIDO
# ============================================================

def generate_summary_table():
    """Gera tabela resumida com todas as combinações de distribuições e área"""
    summary_data = []
    fail_info = {}
    
    for algorithm in FILES:
        algo_name = ESTRUTURAS[algorithm]
        
        for dist, dist_name, _ in DISTRIBUTIONS:
            filename = f"{algorithm}_{dist}.csv"
            df, fail_n_values = load_csv(filename)
            
            if df is None:
                continue
            
            # Calcula área abaixo da curva para tempo
            area_tempo = calcular_area_abaixo_curva(df['n'].values, df['time_ms'].values)
            
            # Indicador de Stack Overflow
            stack_overflow = "SIM" if fail_n_values else "NÃO"
            primeiro_fail = fail_n_values[0] if fail_n_values else "-"
            
            summary_data.append({
                'Algoritmo': algo_name,
                'Distribuição': dist_name,
                'n_máximo': int(df['n'].max()) if 'n' in df.columns else 0,
                'Comparações_média': f"{df['comparisons'].mean():.0f}" if 'comparisons' in df.columns else "N/A",
                'Cópias_média': f"{df['copies'].mean():.0f}" if 'copies' in df.columns else "N/A",
                'Tempo_médio_ms': f"{df['time_ms'].mean():.6f}" if 'time_ms' in df.columns else "N/A",
                'Área_tempo': f"{area_tempo:.6f}",
                'Overflow': stack_overflow,
                'Falha_em_N': primeiro_fail
            })
            
            if fail_n_values:
                fail_key = f"{algorithm}_{dist}"
                fail_info[fail_key] = {
                    'estrutura': f"{algo_name} ({dist_name})",
                    'fail_points': fail_n_values
                }
            
            print(f"[OK] {algorithm} ({dist_name}) - Overflow: {stack_overflow}")
    
    df_summary = pd.DataFrame(summary_data)
    save_table_tsv(df_summary, "resumo_algoritmos.tsv")
    
    return df_summary, fail_info

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

def setup_axis(ax, ylabel, column, y_max_scale):
    """Configura rótulos e escala do eixo"""
    ax.set_xlabel("n")
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_major_formatter(HUMAN_FORMATTER)

    if USE_LOG_SCALE:
        ax.set_yscale("log")
        return

    if y_max_scale == "global":
        maximum = GLOBAL_MAX[column]
        if maximum > 0:
            ax.set_ylim(0, maximum * 1.1)

# ============================================================
# SALVAR FIGURA
# ============================================================

def save_figure(fig, output_dir, filename):
    """Salva figura nos formatos especificados"""
    os.makedirs(output_dir, exist_ok=True)
    path = Path(output_dir)

    if EXPORT_PNG:
        fig.savefig(path / f"{filename}.png", dpi=DPI, bbox_inches="tight")

    if EXPORT_SVG:
        fig.savefig(path / f"{filename}.svg", bbox_inches="tight")

    if EXPORT_PDF:
        fig.savefig(path / f"{filename}.pdf", bbox_inches="tight")

# ============================================================
# GERA GRAFICO DE UM ALGORITMO
# ============================================================

def plot_algorithm(algorithm, title, output_dir, y_max_scale):
    """Cria gráfico comparativo de um algoritmo em diferentes distribuições"""
    print()
    print("=" * 70)
    print(f"{title} -> {output_dir}")
    print("=" * 70)

    datasets = []

    for dist, label, color in DISTRIBUTIONS:
        filename = f"{algorithm}_{dist}.csv"
        df, _ = load_csv(filename)

        if df is not None:
            datasets.append((df, label, color))

    if not datasets:
        print("[AVISO] Nenhum dado encontrado para este algoritmo.")
        return

    fig, axes = create_figure(title)

    legend_handles = []
    legend_labels = []

    for df, label, color in datasets:
        for ax, (column, ylabel) in zip(axes, METRICS):

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

                setup_axis(ax, ylabel, column, y_max_scale)

                if label not in legend_labels:
                    legend_labels.append(label)
                    legend_handles.append(line)

            except Exception as e:
                print(f"[ERRO] Ao plotar {label} em {ylabel}: {e}")
                continue

    fig.legend(
        legend_handles,
        legend_labels,
        loc="lower center",
        ncol=len(legend_labels),
        fontsize=10
    )

    fig.tight_layout(rect=[0, 0.08, 1, 0.95])
    save_figure(fig, output_dir, algorithm)
    plt.close(fig)

    print(f"[OK] Gráfico salvo: {algorithm}")

# ============================================================
# MAIN
# ============================================================

def main():
    """Função principal"""
    print("=" * 70)
    print("GERADOR AUTOMÁTICO DE GRÁFICOS E RELATÓRIOS DE ORDENAÇÃO")
    print("=" * 70)
    if GENERATE_GERAL:
        print(f"Escala automática global: {GERAL_OUTPUT_DIR}")
    if GENERATE_NORMAL:
        print(f"Escala normal: {NORMAL_OUTPUT_DIR}")
    print("Relatórios: " + REPORTS_DIR)
    print("Unidade de tempo: milissegundos (ms)")
    print("=" * 70)

    # Calcula escalas globais
    calculate_global_limits()

    # Gera relatórios e tabelas
    print()
    print("#" * 70)
    print("# GERANDO RELATÓRIOS E TABELAS")
    print("#" * 70)
    
    print("\n[Processando] Gerando tabela resumida...")
    df_summary, fail_info = generate_summary_table()
    
    print("\n[Processando] Gerando estatísticas...")
    stats_df = generate_statistics()
    save_table_tsv(stats_df, "estatisticas_completas.tsv")
    
    print("[Processando] Gerando relatório TXT...")
    generate_text_report(fail_info)
    
    print("\n" + "=" * 160)
    print("RESUMO - ANÁLISE DE ALGORITMOS DE ORDENAÇÃO")
    print("=" * 160)
    print(df_summary.to_string(index=False))
    print("=" * 160)

    # Gera a versão com escala automática global
    if GENERATE_GERAL:
        print()
        print("#" * 70)
        print(f"# ESCALA AUTOMÁTICA GLOBAL -> {GERAL_OUTPUT_DIR}")
        print("#" * 70)

        for algorithm in FILES:
            title = ESTRUTURAS[algorithm]
            plot_algorithm(algorithm, title, GERAL_OUTPUT_DIR, "global")

    # Gera a versão com escala normal
    if GENERATE_NORMAL:
        print()
        print("#" * 70)
        print(f"# ESCALA NORMAL -> {NORMAL_OUTPUT_DIR}")
        print("#" * 70)

        for algorithm in FILES:
            title = ESTRUTURAS[algorithm]
            plot_algorithm(algorithm, title, NORMAL_OUTPUT_DIR, None)

    print()
    print("=" * 70)
    print("PROCESSAMENTO FINALIZADO")
    print("=" * 70)
    print()
    folders = [REPORTS_DIR]
    if GENERATE_GERAL:
        folders.append(GERAL_OUTPUT_DIR)
    if GENERATE_NORMAL:
        folders.append(NORMAL_OUTPUT_DIR)
    print("Resultados salvos em: " + ", ".join(folders))
    print()
    print("Arquivos gerados:")
    print(f"  • relatorio.txt")
    print(f"  • estatisticas_completas.tsv")
    print(f"  • resumo_algoritmos.tsv")

# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    main()