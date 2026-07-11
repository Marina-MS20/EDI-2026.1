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
# ESTRUTURAS - ORDEM DAS COLUNAS
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
# LINHAS: MÉTRICAS NA ORDEM ESPECIFICADA
# ======================================================

METRICAS = [
    ("n_máximo", "N máximo"),
    ("comp_max", "Comp max"),
    ("t_ms", "t ms"),
    ("area_t", "Área t")
]

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
# GERAR TABELA RESUMIDA (FORMATO: MÉTRICAS x ESTRUTURAS)
# ======================================================

def generate_summary_table():
    """Gera tabela com métricas nas linhas e estruturas nas colunas"""
    
    dados_estruturas = {}
    fail_info = {}
    
    # Carregar dados de todas as estruturas
    for filename in FILES:
        df, fail_n_values = load_csv(filename)
        
        if df is None or len(df) < 1:
            print(f"[AVISO] Sem dados: {filename}")
            continue
        
        x = df['n'].values
        y = df['time_ns'].values
        
        n_max = int(df['n'].max()) if 'n' in df.columns else 0
        comparacoes_media = df['comparisons'].mean() if 'comparisons' in df.columns else 0
        tempo_media = (df['time_ns'].mean() / 1_000_000) if 'time_ns' in df.columns else 0
        area_abaixo_curva = calcular_area_abaixo_curva(x, y)
        
        stack_overflow = "SIM" if fail_n_values else "NÃO"
        primeiro_fail = fail_n_values[0] if fail_n_values else "-"
        
        # Armazenar dados
        dados_estruturas[filename] = {
            'n_máximo': n_max,
            'comp_max': f"{comparacoes_media:.0f}",
            't_ms': f"{tempo_media:.6f}",
            'area_t': f"{area_abaixo_curva:.6f}",
            'overflow': stack_overflow,
            'falha_em': primeiro_fail
        }
        
        if fail_n_values:
            fail_info[filename] = {
                'estrutura': ESTRUTURAS[filename],
                'fail_points': fail_n_values
            }
        
        print(f"[OK] {filename} - Overflow: {stack_overflow}")
    
    # Construir DataFrame com métricas nas linhas, estruturas nas colunas
    table_data = []
    
    for metrica_key, metrica_label in METRICAS:
        row = {'Métrica': metrica_label}
        
        for filename, _ in ESTRUTURAS_ORDEM:
            if filename in dados_estruturas:
                row[ESTRUTURAS[filename]] = dados_estruturas[filename][metrica_key]
            else:
                row[ESTRUTURAS[filename]] = "-"
        
        table_data.append(row)
    
    # Adicionar linha de Overflow
    row_overflow = {'Métrica': 'Overflow'}
    for filename, _ in ESTRUTURAS_ORDEM:
        if filename in dados_estruturas:
            row_overflow[ESTRUTURAS[filename]] = dados_estruturas[filename]['overflow']
        else:
            row_overflow[ESTRUTURAS[filename]] = "-"
    table_data.append(row_overflow)
    
    # Adicionar linha de Falha em N
    row_falha = {'Métrica': 'Falha em N'}
    for filename, _ in ESTRUTURAS_ORDEM:
        if filename in dados_estruturas:
            row_falha[ESTRUTURAS[filename]] = dados_estruturas[filename]['falha_em']
        else:
            row_falha[ESTRUTURAS[filename]] = "-"
    table_data.append(row_falha)
    
    df_summary = pd.DataFrame(table_data)
    
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
# MAIN
# ======================================================

def main():
    print("=" * 180)
    print("GERADOR DE TABELA RESUMIDA - ALGORITMOS DE BUSCA")
    print("=" * 180)
    print(f"Diretório entrada: {INPUT_DIR}")
    print(f"Diretório saída: {REPORTS_DIR}")
    print("Formato: Métricas (linhas) × Estruturas (colunas)")
    print("=" * 180)
    print()
    
    # Gerar tabela resumida
    df_summary, fail_info = generate_summary_table()
    
    # Gerar relatório de falhas
    print()
    generate_fail_report(fail_info)
    
    print("\n" + "=" * 180)
    print("PROCESSAMENTO FINALIZADO")
    print("=" * 180)

if __name__ == "__main__":
    main()