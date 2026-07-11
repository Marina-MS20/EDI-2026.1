import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score, mean_squared_error

# ======================================================
# CONFIGURAÇÕES
# ======================================================

OUTPUT_DIR = "output"
GRAPHS_DIR = "graphs"
RESULT_FILE = "resultado_regressoes_busca.csv"
REPORT_FILE = "relatorio_regressoes_busca.txt"

# LIMITES DOS EIXOS (ajuste conforme necessário)
X_MIN = None
X_MAX = None
Y_MIN = 0
Y_MAX = 0.0005

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

# APENAS TIME_NS
METRICS = [
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
# CORES E SIMBOLOS POR ESTRUTURA E DISPOSIÇÃO
# ======================================================

CORES = {
    "seq_random": "#000000",      # preto
    "seq_sorted": "#303030",      # cinza escuro
    "seq_reverse": "#515151",     # cinza médio
    "bin": "#002252",             # azul escuro
    "abb_random": "#0080FF",      # azul claro
    "abb_sorted": "#ACB900",      # amarelo-verde
    "abb_reverse": "#fbff00",     # amarelo
    "avl_random": "#ff0000",      # vermelho
    "avl_sorted": "#960000",      # vermelho escuro
    "avl_reverse": "#760000"      # vermelho muito escuro
}

# ======================================================
# FUNÇÃO PARA GERAR GRÁFICO ÚNICO
# ======================================================

def gerar_grafico_unico(dados_grafico, metrica, nome_grafico, x_min=None, x_max=None, y_min=None, y_max=None):
    
    fig, ax = plt.subplots(figsize=(16, 9))
    
    # Primeiro, plotar todos os OUTROS grupos (sem destaque)
    for dados in dados_grafico:
        arquivo = dados['arquivo']
        x = dados['x']
        y = dados['y']
        
        nome_arquivo_limpo = arquivo.replace('.csv', '')
        cor = CORES.get(nome_arquivo_limpo, "#000000")
        
        # Verificar se é BIN
        eh_bin = arquivo == 'bin.csv'
        
        if not eh_bin:  # Se NÃO é BIN
            ax.plot(x, y, color=cor, linewidth=1.5, alpha=0.6, 
                   label=f'{nome_arquivo_limpo}', zorder=3)
    
    # Depois, plotar apenas BIN (destacado)
    for dados in dados_grafico:
        arquivo = dados['arquivo']
        x = dados['x']
        y = dados['y']
        
        nome_arquivo_limpo = arquivo.replace('.csv', '')
        cor = CORES.get(nome_arquivo_limpo, "#000000")
        
        eh_bin = arquivo == 'bin.csv'
        
        if eh_bin:  # Se é BIN
            # Linha de fundo (halo)
            ax.plot(x, y, color=cor, linewidth=5, alpha=0.15, zorder=4)
            
            # Linha principal destacada
            ax.plot(x, y, color=cor, linewidth=3, alpha=0.95, 
                   label=f'{nome_arquivo_limpo}', zorder=5)
    
    if x_min is not None or x_max is not None:
        ax.set_xlim(x_min, x_max)
    if y_min is not None or y_max is not None:
        ax.set_ylim(y_min, y_max)
    
    # FONTES AUMENTADAS
    ax.set_xlabel('n', fontsize=18, fontweight='bold')
    ax.set_ylabel('Tempo (ms) (x buscas)', fontsize=18, fontweight='bold')
    ax.set_title(f'Tempo de Execucao por n', 
                fontsize=20, fontweight='bold', pad=20)
    
    # AUMENTAR FONTE DOS VALORES DOS EIXOS
    ax.tick_params(axis='both', which='major', labelsize=14)
    
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
    
    # AUMENTAR FONTE DA LEGENDA
    ax.legend(fontsize=19, loc='best', framealpha=0.95, ncol=2)
    
    caminho_grafico = os.path.join(GRAPHS_DIR, f"comparacao_tempo.png")
    fig.savefig(caminho_grafico, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    print(f"OK Grafico salvo: {caminho_grafico}")
    return caminho_grafico

# ======================================================
# EXECUÇÃO PRINCIPAL
# ======================================================

all_results = []
dados_por_metrica = {}

open(REPORT_FILE, "w", encoding="utf-8").close()

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
        y = data[metric].values / 1_000_000  # Converter nanosegundos para milissegundos
        
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
        
        print("\n==============================")
        print("Arquivo:", file)
        print("Tempo (ms)")
        print("Modelo:", modelo)
        print("Equacao:", eq)
        print("Derivada:", deriv)
        print("n final:", n_final)
        print("Taxa variacao:", taxa)
        print("R2:", best["r2"])
        print("RMSE:", best["rmse"])
        
        with open(REPORT_FILE, "a", encoding="utf-8") as report:
            report.write("\n==============================\n")
            report.write(f"Arquivo: {file}\n")
            report.write(f"Tempo (ms)\n")
            report.write(f"Modelo: {modelo}\n")
            report.write(f"Equacao: {eq}\n")
            report.write(f"Derivada: {deriv}\n")
            report.write(f"n_final: {n_final}\n")
            report.write(f"Taxa_variacao_final: {taxa:.8e}\n")
            report.write(f"R2_ajustado: {best['r2']:.8f}\n")
            report.write(f"RMSE: {best['rmse']:.8f}\n")
        
        all_results.append({
            "arquivo": file,
            "metrica": "time_ms",
            "modelo": modelo,
            "equacao": eq,
            "derivada": deriv,
            "n_final": n_final,
            "taxa_variacao_final": taxa,
            "r2_ajustado": best["r2"],
            "rmse": best["rmse"]
        })
        
        if "time_ms" not in dados_por_metrica:
            dados_por_metrica["time_ms"] = []
        
        dados_por_metrica["time_ms"].append({
            'arquivo': file,
            'x': x,
            'y': y,
            'modelo': modelo,
            'params': parametros,
            'r2': best['r2']
        })

print("\n" + "="*50)
print("GERANDO GRAFICO")
print("="*50)

if "time_ms" in dados_por_metrica:
    try:
        gerar_grafico_unico(dados_por_metrica["time_ms"], "time_ms", "tempo", X_MIN, X_MAX, Y_MIN, Y_MAX)
    except Exception as e:
        print(f"ERRO ao gerar grafico: {e}")

resultado = pd.DataFrame(all_results)
resultado.to_csv(RESULT_FILE, index=False)

print("\n" + "="*50)
print("ANALISE CONCLUIDA")
print("="*50)
print("Arquivos gerados:")
print(f"  - {RESULT_FILE}")
print(f"  - {REPORT_FILE}")
print(f"  - Grafico em: {GRAPHS_DIR}/comparacao_tempo.png")
print("\nDica: Ajuste X_MIN, X_MAX, Y_MIN, Y_MAX no inicio do codigo")