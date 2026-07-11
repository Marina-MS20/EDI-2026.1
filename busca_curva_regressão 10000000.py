import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from scipy.optimize import curve_fit
from sklearn.metrics import r2_score, mean_squared_error


# ======================================================
# CONFIGURAÇÕES
# ======================================================

OUTPUT_DIR = "output"
GRAPHS_DIR = "graphs"

RESULT_FILE = "resultado_regressoes_busca.csv"
REPORT_FILE = "relatorio_regressoes_busca.txt"

# ======================================================
# VARIÁVEIS DE AJUSTE DOS LIMITES DOS GRÁFICOS
# ======================================================

X_MIN = -100000
X_MAX = 10000000
Y_MIN = -100
Y_MAX = 25000000

os.makedirs(GRAPHS_DIR, exist_ok=True)

FILES = [
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

METRICS = [
    "comparisons",
    "time_ns"
]

# ======================================================
# MODELOS DE REGRESSÃO
# ======================================================

def linear(x, a, b):
    return a*x+b

def logarithmic(x, a, b):
    return a*np.log(x)+b

def quadratic(x, a, b, c):
    return a*x*x+b*x+c

def power(x, a, b):
    return a*(x**b)

def nlogn(x, a, b):
    return a*x*np.log(x)+b

MODELS = {
    "Linear": (linear, 2),
    "Logarithmic": (logarithmic, 2),
    "Quadratic": (quadratic, 3),
    "Power": (power, 2),
    "NLogN": (nlogn, 2)
}

# ======================================================
# MÉTRICAS ESTATÍSTICAS
# ======================================================

def adjusted_r2(y, y_pred, params):
    n = len(y)
    r2 = r2_score(y, y_pred)
    return 1 - (((1-r2)*(n-1))/(n-params-1))

def rmse(y, y_pred):
    return np.sqrt(mean_squared_error(y, y_pred))

# ======================================================
# AJUSTE DOS MODELOS
# ======================================================

def fit_models(x, y):
    results = []

    for name, (model, param_count) in MODELS.items():
        try:
            popt, _ = curve_fit(model, x, y, maxfev=50000)
            prediction = model(x, *popt)

            results.append({
                "modelo": name,
                "parametros": popt,
                "r2": adjusted_r2(y, prediction, param_count),
                "rmse": rmse(y, prediction)
            })

        except Exception:
            pass

    return sorted(results, key=lambda x: x["r2"], reverse=True)

# ======================================================
# EQUAÇÕES
# ======================================================

def equation(name, p):
    if name == "Linear":
        return f"y = {p[0]:.6e}*n + {p[1]:.6f}"
    if name == "Logarithmic":
        return f"y = {p[0]:.6e}*ln(n) + {p[1]:.6f}"
    if name == "Quadratic":
        return f"y = {p[0]:.6e}*n² + {p[1]:.6e}*n + {p[2]:.6f}"
    if name == "Power":
        return f"y = {p[0]:.6e}*n^{p[1]:.6f}"
    if name == "NLogN":
        return f"y = {p[0]:.6e}*n*ln(n) + {p[1]:.6f}"

# ======================================================
# DERIVADAS SIMBÓLICAS
# ======================================================

def derivative(name, p):
    if name == "Linear":
        return f"dy/dn = {p[0]:.6e}"
    if name == "Logarithmic":
        return f"dy/dn = {p[0]:.6e}/n"
    if name == "Quadratic":
        return f"dy/dn = {2*p[0]:.6e}*n + {p[1]:.6e}"
    if name == "Power":
        return f"dy/dn = {p[0]*p[1]:.6e}*n^({p[1]-1:.6f})"
    if name == "NLogN":
        return f"dy/dn = {p[0]:.6e}*(ln(n)+1)"

# ======================================================
# CALCULA VALOR DA DERIVADA NO PONTO FINAL
# ======================================================

def derivative_value(name, p, n):
    if name == "Linear":
        return p[0]
    if name == "Logarithmic":
        return p[0]/n
    if name == "Quadratic":
        return 2*p[0]*n+p[1]
    if name == "Power":
        return p[0]*p[1]*(n**(p[1]-1))
    if name == "NLogN":
        return p[0]*(np.log(n)+1)

# ======================================================
# CORES E MARCADORES
# ======================================================

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

# ======================================================
# FUNÇÃO PARA GERAR GRÁFICO ÚNICO
# ======================================================

def gerar_grafico_unico(dados_grafico, metrica, titulo_metrica, x_min, x_max, y_min, y_max):
    
    fig, ax = plt.subplots(figsize=(18, 10))
    
    for dados in dados_grafico:
        arquivo = dados['arquivo']
        modelo = dados['modelo']
        params = dados['params']
        
        nome_arquivo_limpo = arquivo.replace('.csv', '')
        cor = CORES.get(nome_arquivo_limpo, "#000000")
        
        # Linha de regressão
        modelo_func, _ = MODELS[modelo]
        x_smooth = np.linspace(x_min if x_min else 0, x_max if x_max else 10000000, 500)
        y_smooth = modelo_func(x_smooth, *params)
        
        # Converter para ms se for métrica de tempo
        if metrica == "time_ns":
            y_smooth = y_smooth / 1_000_000  # ns para ms
        
        # Destacar AVL
        if 'avl' in nome_arquivo_limpo:
            ax.plot(x_smooth, y_smooth, color=cor, linewidth=5.0, 
                   linestyle='-', alpha=0.9, zorder=5, label=nome_arquivo_limpo)
        else:
            ax.plot(x_smooth, y_smooth, color=cor, linewidth=2.5, 
                   linestyle='--', alpha=0.8, zorder=2, label=nome_arquivo_limpo)
    
    # Limites dos eixos
    ax.set_xlim(x_min, x_max)
    if metrica == "time_ns":
        ax.set_ylim(y_min / 1_000_000, y_max / 1_000_000)  # Converter limites para ms
    else:
        ax.set_ylim(y_min, y_max)
    
    # Formatação dos eixos
    ax.set_xlabel('n', fontsize=18, fontweight='bold')
    
    if metrica == "comparisons":
        ax.set_ylabel('Comparações', fontsize=18, fontweight='bold')
        titulo = 'Comparações por n'
        # Formatar y sem notação científica
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{int(x):,}'.replace(',', '.')))
    else:
        ax.set_ylabel('Tempo (ms)', fontsize=18, fontweight='bold')
        titulo = 'Tempo de Execução por n'
        # Formatar y sem notação científica
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x:.0f}'))
    
    # Formatar x sem notação científica
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{int(x):,}'.replace(',', '.')))
    
    ax.set_title(titulo, fontsize=22, fontweight='bold', pad=20)
    ax.tick_params(axis='both', which='major', labelsize=14)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
    
    # Legenda sem equações
    ax.legend(fontsize=19, loc='best', framealpha=0.95, ncol=2)
    
    # Salvar gráfico
    caminho_grafico = os.path.join(GRAPHS_DIR, f"grafico_{metrica}.png")
    fig.savefig(caminho_grafico, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    print(f"✓ Gráfico salvo: {caminho_grafico}")

# ======================================================
# EXECUÇÃO PRINCIPAL
# ======================================================

all_results = []
dados_por_metrica = {}

with open(REPORT_FILE, "w", encoding="utf-8") as report:

    for file in FILES:
        path = os.path.join(OUTPUT_DIR, file)
        
        if not os.path.exists(path):
            continue
        
        df = pd.read_csv(path)
        
        for metric in METRICS:
            data = df.copy()
            data[metric] = pd.to_numeric(data[metric], errors="coerce")
            data = data.dropna(subset=["n", metric])
            
            if len(data) < 5:
                continue
            
            x = data["n"].values
            y = data[metric].values
            
            models = fit_models(x, y)
            
            if not models:
                continue
            
            best = models[0]
            modelo = best["modelo"]
            parametros = best["parametros"]
            
            eq = equation(modelo, parametros)
            deriv = derivative(modelo, parametros)
            n_final = max(x)
            taxa = derivative_value(modelo, parametros, n_final)
            
            # ==========================================
            # SAÍDA NO TERMINAL
            # ==========================================
            print("\n==============================")
            print("Arquivo:", file)
            print("Métrica:", metric)
            print("Modelo:", modelo)
            print("Equação:", eq)
            print("Derivada:", deriv)
            print("n final:", n_final)
            print("Taxa variação:", taxa)
            print("R²:", best["r2"])
            print("RMSE:", best["rmse"])
            
            # ==========================================
            # RELATÓRIO TXT
            # ==========================================
            report.write("\n==============================\n")
            report.write(f"Arquivo: {file}\n")
            report.write(f"Metrica: {metric}\n")
            report.write(f"Modelo: {modelo}\n")
            report.write(f"Equacao: {eq}\n")
            report.write(f"Derivada: {deriv}\n")
            report.write(f"n_final: {n_final}\n")
            report.write(f"Taxa_variacao_final: {taxa:.8e}\n")
            report.write(f"R2_ajustado: {best['r2']:.8f}\n")
            report.write(f"RMSE: {best['rmse']:.8f}\n")
            
            # ==========================================
            # RESULTADO CSV
            # ==========================================
            all_results.append({
                "arquivo": file,
                "metrica": metric,
                "modelo": modelo,
                "equacao": eq,
                "derivada": deriv,
                "n_final": n_final,
                "taxa_variacao_final": taxa,
                "r2_ajustado": best["r2"],
                "rmse": best["rmse"]
            })
            
            # ==========================================
            # DADOS PARA GRÁFICO
            # ==========================================
            if metric not in dados_por_metrica:
                dados_por_metrica[metric] = []
            
            dados_por_metrica[metric].append({
                'arquivo': file,
                'modelo': modelo,
                'params': parametros
            })

# ======================================================
# GERAÇÃO DE GRÁFICOS
# ======================================================

print("\n" + "="*50)
print("GERANDO GRÁFICOS")
print("="*50)

for metrica, dados in dados_por_metrica.items():
    try:
        gerar_grafico_unico(dados, metrica, metrica, X_MIN, X_MAX, Y_MIN, Y_MAX)
    except Exception as e:
        print(f"✗ Erro ao gerar gráfico para {metrica}: {e}")

# ======================================================
# EXPORTAÇÃO FINAL
# ======================================================

resultado = pd.DataFrame(all_results)
resultado.to_csv(RESULT_FILE, index=False)

print("\n" + "="*50)
print("ANÁLISE CONCLUÍDA")
print("="*50)
print("Arquivos gerados:")
print(f"  - {RESULT_FILE}")
print(f"  - {REPORT_FILE}")
print(f"  - Gráfico comparisons: {GRAPHS_DIR}/grafico_comparisons.png")
print(f"  - Gráfico time_ns: {GRAPHS_DIR}/grafico_time_ns.png")