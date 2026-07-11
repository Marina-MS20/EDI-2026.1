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
Y_MIN = 0.1  # Alterado para evitar log(0)
Y_MAX = 25000

# ======== ESCALA LOGARÍTMICA ========
USE_LOG_Y = True   # Ativa escala logarítmica apenas no eixo Y
# ====================================

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

def fit_models(x, y, use_log_y=False):
    results = []
    
    # Transformar apenas Y se usar logaritmo
    y_fit = np.log(y) if use_log_y else y

    for name, (model, param_count) in MODELS.items():
        try:
            # Ajustar no espaço transformado (X linear, Y possivelmente log)
            popt, _ = curve_fit(model, x, y_fit, maxfev=50000)
            prediction = model(x, *popt)

            results.append({
                "modelo": name,
                "parametros": popt,
                "r2": adjusted_r2(y_fit, prediction, param_count),
                "rmse": rmse(y_fit, prediction)
            })

        except Exception:
            pass

    return sorted(results, key=lambda x: x["r2"], reverse=True)

# ======================================================
# EQUAÇÕES
# ======================================================

def equation(name, p, use_log_y=False):
    log_y_str = "log(y)" if use_log_y else "y"
    
    if name == "Linear":
        return f"{log_y_str} = {p[0]:.6e}*n + {p[1]:.6f}"
    if name == "Logarithmic":
        return f"{log_y_str} = {p[0]:.6e}*ln(n) + {p[1]:.6f}"
    if name == "Quadratic":
        return f"{log_y_str} = {p[0]:.6e}*n² + {p[1]:.6e}*n + {p[2]:.6f}"
    if name == "Power":
        return f"{log_y_str} = {p[0]:.6e}*n^{p[1]:.6f}"
    if name == "NLogN":
        return f"{log_y_str} = {p[0]:.6e}*n*ln(n) + {p[1]:.6f}"

# ======================================================
# DERIVADAS SIMBÓLICAS
# ======================================================

def derivative(name, p, use_log_y=False):
    if use_log_y:
        prefix = "d(log y)/dn = "
    else:
        prefix = "dy/dn = "
    
    if name == "Linear":
        return f"{prefix}{p[0]:.6e}"
    if name == "Logarithmic":
        return f"{prefix}{p[0]:.6e}/n"
    if name == "Quadratic":
        return f"{prefix}{2*p[0]:.6e}*n + {p[1]:.6e}"
    if name == "Power":
        return f"{prefix}{p[0]*p[1]:.6e}*n^({p[1]-1:.6f})"
    if name == "NLogN":
        return f"{prefix}{p[0]:.6e}*(ln(n)+1)"

def derivative_value(name, p, n, use_log_y=False):
    if name == "Linear":
        return p[0]
    if name == "Logarithmic":
        return p[0]/n if n > 0 else 0
    if name == "Quadratic":
        return 2*p[0]*n+p[1]
    if name == "Power":
        return p[0]*p[1]*(n**(p[1]-1)) if n > 0 else 0
    if name == "NLogN":
        return p[0]*(np.log(n)+1) if n > 0 else 0

# ======================================================
# CORES E SIMBOLOS POR ESTRUTURA E DISPOSIÇÃO
# ======================================================

SIMBOLOS_POR_ESTRUTURA = {
    "seq": "D",        # losango
    "bin": "s",        # quadrado
    "abb": "o",        # círculo
    "avl": "^"         # triângulo para cima
}

CORES_POR_DISPOSICAO = {
    "random": "#1f77b4",      # azul
    "sorted": "#ff7f0e",      # laranja
    "reverse": "#2ca02c"      # verde
}

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
# FUNÇÃO PARA GERAR GRÁFICO ÚNICO COM Y LOGARÍTMICO
# ======================================================

def gerar_grafico_unico(dados_grafico, metrica, nome_grafico, 
                       x_min=None, x_max=None, y_min=None, y_max=None,
                       use_log_y=False):
    
    fig, ax = plt.subplots(figsize=(16, 9))
    
    for dados in dados_grafico:
        arquivo = dados['arquivo']
        x = dados['x']
        y = dados['y']
        modelo = dados['modelo']
        params = dados['params']
        r2 = dados['r2']
        
        nome_arquivo_limpo = arquivo.replace('.csv', '')
        cor = CORES.get(nome_arquivo_limpo, "#000000")
        marcador = MARCADORES.get(nome_arquivo_limpo, "o")
        
        ax.scatter(x, y, color=cor, s=60, alpha=0.6, 
                  label=f'{nome_arquivo_limpo}',
                  marker=marcador, zorder=3, edgecolors='black', linewidth=0.5)
        
        modelo_func, _ = MODELS[modelo]
        
        # Criar smooth line com X linear
        x_smooth = np.linspace(min(x), max(x), 300)
        y_smooth = modelo_func(x_smooth, *params)
        
        # Se Y foi transformado em log, reverter a transformação
        if use_log_y:
            y_smooth = np.exp(y_smooth)
        
        ax.plot(x_smooth, y_smooth, color=cor, linewidth=2.5, 
               linestyle='--', alpha=0.8, zorder=2)
    
    # Aplicar escala logarítmica apenas no Y
    if use_log_y:
        ax.set_yscale('log')
    
    if x_min is not None or x_max is not None:
        ax.set_xlim(x_min, x_max)
    if y_min is not None or y_max is not None:
        ax.set_ylim(y_min, y_max)
    
    # FONTES AUMENTADAS
    ax.set_xlabel('n', fontsize=18, fontweight='bold')
    ax.set_ylabel('Tempo (ms)' + (' - escala log' if use_log_y else ''), 
                 fontsize=18, fontweight='bold')
    
    titulo_suffix = " (escala log Y)" if use_log_y else ""
    ax.set_title(f'Tempo de Execução por n{titulo_suffix}', 
                fontsize=20, fontweight='bold', pad=20)
    
    # AUMENTAR FONTE DOS VALORES DOS EIXOS
    ax.tick_params(axis='both', which='major', labelsize=14)
    
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7, which='both')
    
    # AUMENTAR FONTE DA LEGENDA
    ax.legend(fontsize=19, loc='best', framealpha=0.95, ncol=2)
    
    suffix = "_logy" if use_log_y else ""
    caminho_grafico = os.path.join(GRAPHS_DIR, f"comparacao_tempo{suffix}.png")
    fig.savefig(caminho_grafico, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    print(f"OK Gráfico salvo: {caminho_grafico}")
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
        
        # Garantir valores positivos para logaritmo
        x = x[x > 0]
        y = y[y > 0]
        
        models = fit_models(x, y, use_log_y=USE_LOG_Y)
        
        if not models:
            continue
        
        best = models[0]
        modelo = best["modelo"]
        parametros = best["parametros"]
        
        eq = equation(modelo, parametros, USE_LOG_Y)
        deriv = derivative(modelo, parametros, USE_LOG_Y)
        n_final = max(x)
        taxa = derivative_value(modelo, parametros, n_final, USE_LOG_Y)
        
        print("\n==============================")
        print("Arquivo:", file)
        print("Tempo (ms)")
        print("Modelo:", modelo)
        print("Equação:", eq)
        print("Derivada:", deriv)
        print("n final:", n_final)
        print("Taxa variação:", taxa)
        print("R2:", best["r2"])
        print("RMSE:", best["rmse"])
        
        with open(REPORT_FILE, "a", encoding="utf-8") as report:
            report.write("\n==============================\n")
            report.write(f"Arquivo: {file}\n")
            report.write(f"Tempo (ms)\n")
            report.write(f"Modelo: {modelo}\n")
            report.write(f"Equação: {eq}\n")
            report.write(f"Derivada: {deriv}\n")
            report.write(f"n_final: {n_final}\n")
            report.write(f"Taxa_variação_final: {taxa:.8e}\n")
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
print("GERANDO GRÁFICOS")
print("="*50)

if "time_ms" in dados_por_metrica:
    try:
        gerar_grafico_unico(dados_por_metrica["time_ms"], "time_ms", "tempo", 
                           X_MIN, X_MAX, Y_MIN, Y_MAX, USE_LOG_Y)
    except Exception as e:
        print(f"ERRO ao gerar gráfico: {e}")
        import traceback
        traceback.print_exc()

resultado = pd.DataFrame(all_results)
resultado.to_csv(RESULT_FILE, index=False)

print("\n" + "="*50)
print("ANÁLISE CONCLUÍDA")
print("="*50)
print("Arquivos gerados:")
print(f"  - {RESULT_FILE}")
print(f"  - {REPORT_FILE}")
print(f"  - Gráfico em: {GRAPHS_DIR}/comparacao_tempo_logy.png")
print(f"\nConfiguração:")
print(f"  - Eixo X: LINEAR")
print(f"  - Eixo Y: {'LOGARÍTMICO' if USE_LOG_Y else 'LINEAR'}")