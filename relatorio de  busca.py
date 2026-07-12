import os
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# ======================================================
# CONFIGURAÇÕES
# ======================================================

INPUT_DIR = "output"
REPORTS_DIR = "relatorios"
RESULT_FILE = "resultado_busca.tsv"
FAIL_REPORT = "fail_report.txt"

os.makedirs(REPORTS_DIR, exist_ok=True)

# ======================================================
# ESTRUTURAS - ORDEM DAS LINHAS
# ======================================================

ESTRUTURAS_ORDEM = [
    ("seq_random", "Seq. Aleat."),
    ("seq_sorted", "Seq. Ord."),
    ("seq_reverse", "Seq. Inv."),
    ("bin", "B. Binária"),
    ("abb_random", "ABB Aleat."),
    ("abb_sorted", "ABB Ord."),
    ("abb_reverse", "ABB Inv."),
    ("avl_random", "AVL Aleat."),
    ("avl_sorted", "AVL Ord."),
    ("avl_reverse", "AVL Inv.")
]

ESTRUTURAS = {k: v for k, v in ESTRUTURAS_ORDEM}
FILES = [k for k, _ in ESTRUTURAS_ORDEM]

# ======================================================
# CARREGAR CSV
# ======================================================

def load_csv(filename):
    """Carrega CSV e remove linhas com 'FAIL'"""
    path = Path(INPUT_DIR) / f"{filename}.csv"

    if not path.exists():
        return None, []

    try:
        df = pd.read_csv(path)
        
        # Registrar linhas com FAIL
        fail_rows = df[df.isin(["FAIL"]).any(axis=1)]
        fail_n_values = fail_rows['n'].tolist() if not fail_rows.empty else []
        
        # Remove linhas com FAIL
        for c in df.columns:
            df = df[df[c] != "FAIL"]

        df = df.apply(pd.to_numeric, errors='coerce')
        df = df.dropna()

        return df if not df.empty else None, fail_n_values

    except Exception as e:
        print(f"Erro lendo {filename}.csv: {e}")
        return None, []

# ======================================================
# CALCULAR ÁREA ABAIXO DA CURVA (INTEGRAL)
# ======================================================

def calcular_area_abaixo_curva(x, y):
    """
    Calcula a área abaixo da curva usando a regra dos trapézios.
    """
    indices = np.argsort(x)
    x_sorted = x[indices]
    y_sorted = y[indices]
    
    area_ns = np.trapezoid(y_sorted, x_sorted)
    area_ms = area_ns / 1_000_000
    
    return area_ms

# ======================================================
# GERAR TABELA RESUMIDA (LINHAS: ESTRUTURAS, COLUNAS: MÉTRICAS)
# ======================================================

def generate_summary_table():
    """Gera tabela com estruturas nas linhas e métricas nas colunas"""
    
    summary_data = []
    fail_info = {}
    
    for filename in FILES:
        df, fail_n_values = load_csv(filename)
        
        if df is None or len(df) < 1:
            print(f"[AVISO] Sem dados: {filename}")
            continue
        
        estrutura_nome = ESTRUTURAS.get(filename, filename)
        
        x = df['n'].values
        y_tempo = df['time_ns'].values
        
        n_max = int(df['n'].max()) if 'n' in df.columns else 0
        comparacoes_media = df['comparisons'].mean() if 'comparisons' in df.columns else 0
        
        area_abaixo_curva = calcular_area_abaixo_curva(x, y_tempo)
        tempo_media = (df['time_ns'].mean() / 1_000_000) if 'time_ns' in df.columns else 0
        
        # Altura da árvore (apenas para ABB e AVL)
        altura_media = "-"
        altura_max = "-"
        if 'height' in df.columns:
            altura_media = f"{df['height'].mean():.2f}"
            altura_max = int(df['height'].max())
        
        # Indicador de Stack Overflow
        stack_overflow = "SIM" if fail_n_values else "NÃO"
        primeiro_fail = fail_n_values[0] if fail_n_values else "-"
        
        summary_data.append({
            'Estrutura': estrutura_nome,
            'N máximo': n_max,
            'Comp méd': f"{comparacoes_media:.0f}",
            't ms méd': f"{tempo_media:.6f}",
            'Área t': f"{area_abaixo_curva:.6f}",
            'Alt méd': altura_media,
            'Alt máx': altura_max,
            'Overflow': stack_overflow,
            'Falha em N': primeiro_fail
        })
        
        if fail_n_values:
            fail_info[filename] = {
                'estrutura': estrutura_nome,
                'fail_points': fail_n_values
            }
        
        print(f"[OK] {filename} - Overflow: {stack_overflow}")
    
    df_summary = pd.DataFrame(summary_data)
    
    # Salvar TSV
    path_tsv = Path(REPORTS_DIR) / RESULT_FILE
    df_summary.to_csv(path_tsv, sep='\t', index=False, encoding='utf-8')
    print(f"\n[OK] Tabela salva em TSV: {path_tsv}\n")
    
    # Exibir tabela
    print("=" * 180)
    print("RESUMO - ANÁLISE DE ALGORITMOS DE BUSCA")
    print("=" * 180)
    print(df_summary.to_string(index=False))
    print("=" * 180)
    
    return df_summary, fail_info

# ======================================================
# GERAR RELATÓRIO DE FALHAS
# ======================================================

def generate_fail_report(fail_info):
    """Gera relatório de falhas (Stack Overflow)"""
    
    path_report = Path(REPORTS_DIR) / FAIL_REPORT
    
    with open(path_report, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("RELATÓRIO DE FALHAS - STACK OVERFLOW\n")
        f.write("=" * 80 + "\n\n")
        
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        f.write(f"Data/Hora: {timestamp}\n")
        f.write(f"Diretório: {INPUT_DIR}\n\n")
        
        if not fail_info:
            f.write("Nenhuma falha detectada.\n")
        else:
            f.write("ESTRUTURAS COM STACK OVERFLOW\n")
            f.write("-" * 80 + "\n\n")
            
            for filename, info in fail_info.items():
                f.write(f"{info['estrutura']}:\n")
                f.write(f"  Falhas detectadas em n = {info['fail_points']}\n")
                f.write(f"  Primeiro ponto de falha: {info['fail_points'][0]}\n")
                f.write(f"  Total de pontos com falha: {len(info['fail_points'])}\n\n")
    
    print(f"[OK] Relatório de falhas: {path_report}")

# ======================================================
# GERAR RELATÓRIO DETALHADO (COM ALTURA)
# ======================================================

def generate_detailed_report(df_summary):
    """Gera relatório detalhado com informações de altura para ABB e AVL"""
    
    path_report = Path(REPORTS_DIR) / "relatorio_detalhado.txt"
    
    with open(path_report, "w", encoding="utf-8") as f:
        f.write("=" * 100 + "\n")
        f.write("RELATÓRIO DETALHADO - ANÁLISE DE ALGORITMOS DE BUSCA\n")
        f.write("=" * 100 + "\n\n")
        
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        f.write(f"Data/Hora: {timestamp}\n")
        f.write(f"Diretório entrada: {INPUT_DIR}\n")
        f.write(f"Diretório saída: {REPORTS_DIR}\n\n")
        
        # Tabela resumida em texto
        f.write("-" * 100 + "\n")
        f.write("TABELA RESUMIDA\n")
        f.write("-" * 100 + "\n\n")
        f.write(df_summary.to_string(index=False))
        f.write("\n\n")
        
        # Análise por estrutura
        f.write("=" * 100 + "\n")
        f.write("ANÁLISE DETALHADA POR ESTRUTURA\n")
        f.write("=" * 100 + "\n\n")
        
        for filename in FILES:
            df, fail_n_values = load_csv(filename)
            
            if df is None or len(df) < 1:
                continue
            
            estrutura_nome = ESTRUTURAS.get(filename, filename)
            
            f.write(f"\n{'-' * 100}\n")
            f.write(f"ESTRUTURA: {estrutura_nome.upper()}\n")
            f.write(f"{'-' * 100}\n\n")
            
            # Estatísticas gerais
            n_max = int(df['n'].max())
            n_min = int(df['n'].min())
            comp_min = df['comparisons'].min()
            comp_max = df['comparisons'].max()
            comp_media = df['comparisons'].mean()
            comp_std = df['comparisons'].std()
            
            tempo_min = df['time_ns'].min() / 1_000_000
            tempo_max = df['time_ns'].max() / 1_000_000
            tempo_media = df['time_ns'].mean() / 1_000_000
            tempo_std = df['time_ns'].std() / 1_000_000
            
            f.write(f"Intervalo de N: {n_min} a {n_max} ({len(df)} pontos)\n\n")
            
            f.write("COMPARAÇÕES:\n")
            f.write(f"  Mínimo: {comp_min:.0f}\n")
            f.write(f"  Máximo: {comp_max:.0f}\n")
            f.write(f"  Média: {comp_media:.2f}\n")
            f.write(f"  Desvio padrão: {comp_std:.2f}\n\n")
            
            f.write("TEMPO (ms):\n")
            f.write(f"  Mínimo: {tempo_min:.8f}\n")
            f.write(f"  Máximo: {tempo_max:.8f}\n")
            f.write(f"  Média: {tempo_media:.8f}\n")
            f.write(f"  Desvio padrão: {tempo_std:.8f}\n\n")
            
            # Altura (apenas para ABB e AVL)
            if 'height' in df.columns:
                altura_min = df['height'].min()
                altura_max = df['height'].max()
                altura_media = df['height'].mean()
                altura_std = df['height'].std()
                
                f.write("ALTURA DA ÁRVORE:\n")
                f.write(f"  Mínimo: {altura_min:.0f}\n")
                f.write(f"  Máximo: {altura_max:.0f}\n")
                f.write(f"  Média: {altura_media:.2f}\n")
                f.write(f"  Desvio padrão: {altura_std:.2f}\n\n")
            
            # Informações sobre falhas
            if fail_n_values:
                f.write(f"Stack Overflow: SIM\n")
                f.write(f"  Primeiro ponto de falha: {fail_n_values[0]}\n")
                f.write(f"  Total de falhas: {len(fail_n_values)}\n")
            else:
                f.write(f"Stack Overflow: NÃO\n")
            
            f.write("\n")
    
    print(f"[OK] Relatório detalhado: {path_report}")

# ======================================================
# MAIN
# ======================================================

def main():
    print("=" * 180)
    print("GERADOR DE TABELA RESUMIDA - ALGORITMOS DE BUSCA")
    print("=" * 180)
    print(f"Diretório entrada: {INPUT_DIR}")
    print(f"Diretório saída: {REPORTS_DIR}")
    print("=" * 180)
    print()
    
    # Gerar tabela resumida
    df_summary, fail_info = generate_summary_table()
    
    # Gerar relatório de falhas
    print()
    generate_fail_report(fail_info)
    
    # Gerar relatório detalhado
    print()
    generate_detailed_report(df_summary)
    
    print("\n" + "=" * 180)
    print("PROCESSAMENTO FINALIZADO")
    print("=" * 180)

if __name__ == "__main__":
    main()