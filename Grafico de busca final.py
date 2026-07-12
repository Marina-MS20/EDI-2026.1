import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==================== CONFIGURAÇÕES ====================
DIRETORIO_SAIDA = "output"
DIRETORIO_GRAFICOS = "graficos"

# ==================== CONFIGURAÇÕES DE ESCALA ====================
# Para tempo (ms) - use escala linear
X_MIN_TEMPO = 10
X_MAX_TEMPO = None
Y_MIN_TEMPO = None
Y_MAX_TEMPO = None
ESCALA_LOG_TEMPO = False  # Mude para True se quiser log

# Para comparações - use escala log
X_MIN_COMP = 10
X_MAX_COMP = None
Y_MIN_COMP = 1
Y_MAX_COMP = None
ESCALA_LOG_COMP = True

# Para altura - use escala log
X_MIN_ALT = 10
X_MAX_ALT = None
Y_MIN_ALT = 1
Y_MAX_ALT = None
ESCALA_LOG_ALT = True

# ==================== CONFIGURAÇÕES DE FONTE ====================
FONTE_TITULO = 22
FONTE_LABEL = 18
FONTE_TICK = 14
FONTE_LEGENDA = 16

os.makedirs(DIRETORIO_GRAFICOS, exist_ok=True)

ARQUIVOS = [
    "seq_random.csv",
    "seq_sorted.csv",
    "seq_reverse.csv",
    "bin.csv",
    "abb_random.csv",
    "abb_sorted.csv",
    "abb_reverse.csv",
    "avl_random.csv",
    "avl_sorted.csv",
    "avl_reverse.csv"
]

# ==================== CORES E MARCADORES ====================
CORES = {
    "seq_random": "#000000",
    "seq_sorted": "#303030",
    "seq_reverse": "#515151",
    "bin": "#002252",
    "abb_random": "#0080FF",
    "abb_sorted": "#ACB900",
    "abb_reverse": "#fbff00",
    "avl_random": "#ff0000",
    "avl_sorted": "#960000",
    "avl_reverse": "#760000"
}

MARCADORES = {
    "seq_random": "D",
    "seq_sorted": "D",
    "seq_reverse": "D",
    "bin": "s",
    "abb_random": "o",
    "abb_sorted": "o",
    "abb_reverse": "o",
    "avl_random": "^",
    "avl_sorted": "^",
    "avl_reverse": "^"
}

# Nomes em português
NOMES_ESTRUTURAS = {
    "seq_random": "SEQ Aleatório",
    "seq_sorted": "SEQ Ordenado",
    "seq_reverse": "SEQ Reverso",
    "bin": "Busca Binária",
    "abb_random": "ABB Aleatório",
    "abb_sorted": "ABB Ordenado",
    "abb_reverse": "ABB Reverso",
    "avl_random": "AVL Aleatório",
    "avl_sorted": "AVL Ordenado",
    "avl_reverse": "AVL Reverso"
}

# ==================== FUNÇÃO: EXTRAIR TIPO DE ESTRUTURA ====================
def extrair_estrutura(nome_arquivo):
    """Retorna o tipo de estrutura (seq, bin, abb, avl) de um arquivo"""
    nome_limpo = nome_arquivo.replace('.csv', '')
    if 'seq' in nome_limpo:
        return 'seq'
    elif 'bin' in nome_limpo:
        return 'bin'
    elif 'abb' in nome_limpo:
        return 'abb'
    elif 'avl' in nome_limpo:
        return 'avl'
    return None

# ==================== GRÁFICOS: DISPERSÃO COM DESTAQUE ====================
def gerar_grafico_scatter_geral(dados_grafico, nome_metrica, x_min, x_max, y_min, y_max, escala_log):
    """Gráfico em pontos - GERAL (todas as estruturas)"""
    fig, ax = plt.subplots(figsize=(16, 9))
    
    for dados in dados_grafico:
        arquivo = dados['arquivo']
        x = dados['x']
        y = dados['y']
        
        nome_arquivo_limpo = arquivo.replace('.csv', '')
        cor = CORES.get(nome_arquivo_limpo, "#000000")
        marcador = MARCADORES.get(nome_arquivo_limpo, "o")
        nome_estrutura = NOMES_ESTRUTURAS.get(nome_arquivo_limpo, nome_arquivo_limpo)
        
        ax.scatter(x, y, color=cor, s=100, alpha=0.7, 
                  label=nome_estrutura,
                  marker=marcador, zorder=3, edgecolors='black', linewidth=0.8)
    
    if escala_log:
        ax.set_xscale('log')
        ax.set_yscale('log')
    
    if x_min is not None and x_max is not None:
        ax.set_xlim(x_min, x_max)
    if y_min is not None and y_max is not None:
        ax.set_ylim(y_min, y_max)
    
    ax.set_xlabel('n', fontsize=FONTE_LABEL, fontweight='bold')
    ax.set_ylabel(f'{nome_metrica}', fontsize=FONTE_LABEL, fontweight='bold')
    ax.set_title(f'{nome_metrica} vs n - Geral (Dispersão)', 
                fontsize=FONTE_TITULO, fontweight='bold', pad=20)
    
    ax.tick_params(axis='both', which='major', labelsize=FONTE_TICK)
    ax.grid(True, which='both', alpha=0.3, linestyle='--', linewidth=0.7)
    ax.legend(fontsize=FONTE_LEGENDA, loc='upper left', framealpha=0.95, ncol=2)
    
    nome_arquivo_saida = nome_metrica.lower().replace(' ', '_').replace('(', '').replace(')', '')
    escala_sufixo = "log" if escala_log else "linear"
    caminho = os.path.join(DIRETORIO_GRAFICOS, f"{nome_arquivo_saida}_geral_dispersao_{escala_sufixo}.png")
    fig.savefig(caminho, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"✓ {caminho}")
    return caminho

def gerar_grafico_scatter_destaque(dados_grafico, estrutura, nome_metrica, x_min, x_max, y_min, y_max, escala_log):
    """Gráfico em pontos com DESTAQUE para uma estrutura"""
    fig, ax = plt.subplots(figsize=(16, 9))
    
    # Dados em cinza (fundo)
    for dados in dados_grafico:
        arquivo = dados['arquivo']
        x = dados['x']
        y = dados['y']
        
        nome_arquivo_limpo = arquivo.replace('.csv', '')
        
        if extrair_estrutura(nome_arquivo_limpo) != estrutura:
            nome_estrutura = NOMES_ESTRUTURAS.get(nome_arquivo_limpo, nome_arquivo_limpo)
            ax.scatter(x, y, color='#CCCCCC', s=60, alpha=0.3, 
                      label=nome_estrutura,
                      marker='o', zorder=1, edgecolors='gray', linewidth=0.3)
    
    # Dados destacados
    for dados in dados_grafico:
        arquivo = dados['arquivo']
        x = dados['x']
        y = dados['y']
        
        nome_arquivo_limpo = arquivo.replace('.csv', '')
        
        if extrair_estrutura(nome_arquivo_limpo) == estrutura:
            cor = CORES.get(nome_arquivo_limpo, "#000000")
            marcador = MARCADORES.get(nome_arquivo_limpo, "o")
            nome_estrutura = NOMES_ESTRUTURAS.get(nome_arquivo_limpo, nome_arquivo_limpo)
            
            ax.scatter(x, y, color=cor, s=150, alpha=0.9, 
                      label=nome_estrutura,
                      marker=marcador, zorder=5, edgecolors='black', linewidth=1.2)
    
    if escala_log:
        ax.set_xscale('log')
        ax.set_yscale('log')
    
    if x_min is not None and x_max is not None:
        ax.set_xlim(x_min, x_max)
    if y_min is not None and y_max is not None:
        ax.set_ylim(y_min, y_max)
    
    ax.set_xlabel('n', fontsize=FONTE_LABEL, fontweight='bold')
    ax.set_ylabel(f'{nome_metrica}', fontsize=FONTE_LABEL, fontweight='bold')
    
    nomes_destaque = {'seq': 'SEQ', 'bin': 'Busca Binária', 'abb': 'ABB', 'avl': 'AVL'}
    nome_destaque = nomes_destaque.get(estrutura, estrutura.upper())
    
    ax.set_title(f'{nome_metrica} vs n - DESTAQUE {nome_destaque} (Dispersão)', 
                fontsize=FONTE_TITULO, fontweight='bold', pad=20)
    
    ax.tick_params(axis='both', which='major', labelsize=FONTE_TICK)
    ax.grid(True, which='both', alpha=0.3, linestyle='--', linewidth=0.7)
    ax.legend(fontsize=FONTE_LEGENDA, loc='upper left', framealpha=0.95, ncol=2)
    
    nome_arquivo_saida = nome_metrica.lower().replace(' ', '_').replace('(', '').replace(')', '')
    escala_sufixo = "log" if escala_log else "linear"
    caminho = os.path.join(DIRETORIO_GRAFICOS, f"{nome_arquivo_saida}_destaque_{estrutura}_dispersao_{escala_sufixo}.png")
    fig.savefig(caminho, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"✓ {caminho}")
    return caminho

# ==================== GRÁFICOS: LINHAS COM DESTAQUE ====================
def gerar_grafico_linha_geral(dados_grafico, nome_metrica, x_min, x_max, y_min, y_max, escala_log):
    """Gráfico em linhas - GERAL (todas as estruturas)"""
    fig, ax = plt.subplots(figsize=(16, 9))
    
    for dados in dados_grafico:
        arquivo = dados['arquivo']
        x = dados['x']
        y = dados['y']
        
        nome_arquivo_limpo = arquivo.replace('.csv', '')
        cor = CORES.get(nome_arquivo_limpo, "#000000")
        marcador = MARCADORES.get(nome_arquivo_limpo, "o")
        nome_estrutura = NOMES_ESTRUTURAS.get(nome_arquivo_limpo, nome_arquivo_limpo)
        
        ax.plot(x, y, color=cor, linewidth=2, alpha=0.7,
               label=nome_estrutura, marker=marcador, markersize=6, zorder=3)
    
    if escala_log:
        ax.set_xscale('log')
        ax.set_yscale('log')
    
    if x_min is not None and x_max is not None:
        ax.set_xlim(x_min, x_max)
    if y_min is not None and y_max is not None:
        ax.set_ylim(y_min, y_max)
    
    ax.set_xlabel('n', fontsize=FONTE_LABEL, fontweight='bold')
    ax.set_ylabel(f'{nome_metrica}', fontsize=FONTE_LABEL, fontweight='bold')
    ax.set_title(f'{nome_metrica} vs n - Geral (Linha)', 
                fontsize=FONTE_TITULO, fontweight='bold', pad=20)
    
    ax.tick_params(axis='both', which='major', labelsize=FONTE_TICK)
    ax.grid(True, which='both', alpha=0.3, linestyle='--', linewidth=0.7)
    ax.legend(fontsize=FONTE_LEGENDA, loc='upper left', framealpha=0.95, ncol=2)
    
    nome_arquivo_saida = nome_metrica.lower().replace(' ', '_').replace('(', '').replace(')', '')
    escala_sufixo = "log" if escala_log else "linear"
    caminho = os.path.join(DIRETORIO_GRAFICOS, f"{nome_arquivo_saida}_geral_linha_{escala_sufixo}.png")
    fig.savefig(caminho, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"✓ {caminho}")
    return caminho

def gerar_grafico_linha_destaque(dados_grafico, estrutura, nome_metrica, x_min, x_max, y_min, y_max, escala_log):
    """Gráfico em linhas com DESTAQUE para uma estrutura"""
    fig, ax = plt.subplots(figsize=(16, 9))
    
    # Linhas em cinza (fundo)
    for dados in dados_grafico:
        arquivo = dados['arquivo']
        x = dados['x']
        y = dados['y']
        
        nome_arquivo_limpo = arquivo.replace('.csv', '')
        
        if extrair_estrutura(nome_arquivo_limpo) != estrutura:
            nome_estrutura = NOMES_ESTRUTURAS.get(nome_arquivo_limpo, nome_arquivo_limpo)
            ax.plot(x, y, color='#CCCCCC', linewidth=1, alpha=0.3,
                   label=nome_estrutura, marker='o', markersize=3, zorder=1)
    
    # Linhas destacadas
    for dados in dados_grafico:
        arquivo = dados['arquivo']
        x = dados['x']
        y = dados['y']
        
        nome_arquivo_limpo = arquivo.replace('.csv', '')
        
        if extrair_estrutura(nome_arquivo_limpo) == estrutura:
            cor = CORES.get(nome_arquivo_limpo, "#000000")
            marcador = MARCADORES.get(nome_arquivo_limpo, "o")
            nome_estrutura = NOMES_ESTRUTURAS.get(nome_arquivo_limpo, nome_arquivo_limpo)
            
            ax.plot(x, y, color=cor, linewidth=3.5, alpha=0.9,
                   label=nome_estrutura, marker=marcador, markersize=8, zorder=5)
    
    if escala_log:
        ax.set_xscale('log')
        ax.set_yscale('log')
    
    if x_min is not None and x_max is not None:
        ax.set_xlim(x_min, x_max)
    if y_min is not None and y_max is not None:
        ax.set_ylim(y_min, y_max)
    
    ax.set_xlabel('n', fontsize=FONTE_LABEL, fontweight='bold')
    ax.set_ylabel(f'{nome_metrica}', fontsize=FONTE_LABEL, fontweight='bold')
    
    nomes_destaque = {'seq': 'SEQ', 'bin': 'Busca Binária', 'abb': 'ABB', 'avl': 'AVL'}
    nome_destaque = nomes_destaque.get(estrutura, estrutura.upper())
    
    ax.set_title(f'{nome_metrica} vs n - DESTAQUE {nome_destaque} (Linha)', 
                fontsize=FONTE_TITULO, fontweight='bold', pad=20)
    
    ax.tick_params(axis='both', which='major', labelsize=FONTE_TICK)
    ax.grid(True, which='both', alpha=0.3, linestyle='--', linewidth=0.7)
    ax.legend(fontsize=FONTE_LEGENDA, loc='upper left', framealpha=0.95, ncol=2)
    
    nome_arquivo_saida = nome_metrica.lower().replace(' ', '_').replace('(', '').replace(')', '')
    escala_sufixo = "log" if escala_log else "linear"
    caminho = os.path.join(DIRETORIO_GRAFICOS, f"{nome_arquivo_saida}_destaque_{estrutura}_linha_{escala_sufixo}.png")
    fig.savefig(caminho, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"✓ {caminho}")
    return caminho

# ==================== PROCESSAMENTO DE DADOS ====================
def processar_metrica(arquivos, coluna_metrica, nome_metrica, x_min, x_max, y_min, y_max, escala_log):
    """Carrega dados e gera todos os gráficos para uma métrica"""
    print(f"\n{'='*70}")
    print(f"  PROCESSANDO MÉTRICA: {nome_metrica}")
    print(f"{'='*70}")
    
    dados_metrica = []
    
    for arquivo in arquivos:
        caminho = os.path.join(DIRETORIO_SAIDA, arquivo)
        
        if not os.path.exists(caminho):
            print(f"⚠️  Arquivo não encontrado: {caminho}")
            continue
        
        df = pd.read_csv(caminho)
        
        if coluna_metrica not in df.columns:
            print(f"❌ Coluna '{coluna_metrica}' não encontrada em {arquivo}")
            continue
        
        dados = df.copy()
        dados[coluna_metrica] = pd.to_numeric(dados[coluna_metrica], errors="coerce")
        dados = dados.dropna(subset=["n", coluna_metrica])
        dados = dados[(dados["n"] > 0) & (dados[coluna_metrica] > 0)]
        
        if len(dados) < 2:
            print(f"⚠️  {arquivo} tem poucos dados ({len(dados)} < 2)")
            continue
        
        x = dados["n"].values
        y = dados[coluna_metrica].values
        
        # Converte tempo de nanosegundos para milissegundos
        if coluna_metrica == "time_ns":
            y = y / 1_000_000
        
        nome_arquivo_limpo = arquivo.replace('.csv', '')
        nome_estrutura = NOMES_ESTRUTURAS.get(nome_arquivo_limpo, nome_arquivo_limpo)
        
        print(f"✓ {nome_estrutura:<25} | n={len(x)} pontos | Y: [{y.min():.2e}, {y.max():.2e}]")
        
        dados_metrica.append({
            'arquivo': arquivo,
            'x': x,
            'y': y
        })
    
    # ==================== GERAÇÃO DE GRÁFICOS ====================
    if dados_metrica:
        print(f"\n{'='*70}")
        print(f"  GERANDO GRÁFICOS PARA: {nome_metrica}")
        print(f"{'='*70}")
        
        # SCATTER - GERAL
        gerar_grafico_scatter_geral(dados_metrica, nome_metrica, x_min, x_max, y_min, y_max, escala_log)
        
        # SCATTER - DESTAQUE
        for estrutura in ['seq', 'bin', 'abb', 'avl']:
            gerar_grafico_scatter_destaque(dados_metrica, estrutura, nome_metrica, x_min, x_max, y_min, y_max, escala_log)
        
        # LINHA - GERAL
        gerar_grafico_linha_geral(dados_metrica, nome_metrica, x_min, x_max, y_min, y_max, escala_log)
        
        # LINHA - DESTAQUE
        for estrutura in ['seq', 'bin', 'abb', 'avl']:
            gerar_grafico_linha_destaque(dados_metrica, estrutura, nome_metrica, x_min, x_max, y_min, y_max, escala_log)

# ==================== PROCESSAMENTO DE ALTURA (APENAS AVL E ABB) ====================
def processar_altura():
    """Processa altura da árvore (apenas para AVL e ABB)"""
    print(f"\n{'='*70}")
    print(f"  PROCESSANDO MÉTRICA: Altura da Árvore")
    print(f"{'='*70}")
    
    arquivos_altura = [f for f in ARQUIVOS if 'abb' in f or 'avl' in f]
    dados_altura = []
    
    for arquivo in arquivos_altura:
        caminho = os.path.join(DIRETORIO_SAIDA, arquivo)
        
        if not os.path.exists(caminho):
            continue
        
        df = pd.read_csv(caminho)
        
        if 'height' not in df.columns:
            print(f"⚠️  Coluna 'height' não encontrada em {arquivo}")
            continue
        
        dados = df.copy()
        dados['height'] = pd.to_numeric(dados['height'], errors="coerce")
        dados = dados.dropna(subset=["n", 'height'])
        dados = dados[(dados["n"] > 0) & (dados['height'] > 0)]
        
        if len(dados) < 2:
            continue
        
        x = dados["n"].values
        y = dados['height'].values
        
        nome_arquivo_limpo = arquivo.replace('.csv', '')
        nome_estrutura = NOMES_ESTRUTURAS.get(nome_arquivo_limpo, nome_arquivo_limpo)
        
        print(f"✓ {nome_estrutura:<25} | n={len(x)} pontos | Y: [{y.min():.0f}, {y.max():.0f}]")
        
        dados_altura.append({
            'arquivo': arquivo,
            'x': x,
            'y': y
        })
    
    # ==================== GERAÇÃO DE GRÁFICOS DE ALTURA ====================
    if dados_altura:
        print(f"\n{'='*70}")
        print(f"  GERANDO GRÁFICOS PARA: Altura da Árvore")
        print(f"{'='*70}")
        
        # SCATTER - GERAL
        gerar_grafico_scatter_geral(dados_altura, "Altura da Árvore", X_MIN_ALT, X_MAX_ALT, Y_MIN_ALT, Y_MAX_ALT, ESCALA_LOG_ALT)
        
        # SCATTER - DESTAQUE
        for estrutura in ['abb', 'avl']:
            gerar_grafico_scatter_destaque(dados_altura, estrutura, "Altura da Árvore", X_MIN_ALT, X_MAX_ALT, Y_MIN_ALT, Y_MAX_ALT, ESCALA_LOG_ALT)
        
        # LINHA - GERAL
        gerar_grafico_linha_geral(dados_altura, "Altura da Árvore", X_MIN_ALT, X_MAX_ALT, Y_MIN_ALT, Y_MAX_ALT, ESCALA_LOG_ALT)
        
        # LINHA - DESTAQUE
        for estrutura in ['abb', 'avl']:
            gerar_grafico_linha_destaque(dados_altura, estrutura, "Altura da Árvore", X_MIN_ALT, X_MAX_ALT, Y_MIN_ALT, Y_MAX_ALT, ESCALA_LOG_ALT)

# ==================== MAIN ====================
def main():
    print(f"\n{'='*70}")
    print(f"  INICIANDO GERAÇÃO DE GRÁFICOS")
    print(f"{'='*70}")
    
    # Processa Tempo de Execução
    processar_metrica(ARQUIVOS, "time_ns", "Tempo de Execução (ms)", 
                     X_MIN_TEMPO, X_MAX_TEMPO, Y_MIN_TEMPO, Y_MAX_TEMPO, ESCALA_LOG_TEMPO)
    
    # Processa Comparações
    processar_metrica(ARQUIVOS, "comparisons", "Comparações", 
                     X_MIN_COMP, X_MAX_COMP, Y_MIN_COMP, Y_MAX_COMP, ESCALA_LOG_COMP)
    
    # Processa Altura
    processar_altura()
    
    print(f"\n{'='*70}")
    print(f"  ✓ GERAÇÃO DE GRÁFICOS CONCLUÍDA")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()