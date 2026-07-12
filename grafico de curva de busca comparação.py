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
RESULT_FILE = "resultado_regressoes_comparacao.csv"
REPORT_FILE = "relatorio_regressoes_comparacao.txt"

# COLUNA CORRETA
COLUNA_METRICA = "comparisons"  # ✓ CORRETO

# LIMITES DOS EIXOS
X_MIN = 0
X_MAX = 20000
Y_MIN = 0
Y_MAX = 1000

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
# CORES E SÍMBOLOS
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
# FUNÇÃO PARA GERAR GRÁFICO
# ======================================================

def gerar_grafico_unico(dados_grafico, x_min=None, x_max=None, y_min=None, y_max=None):
    
    fig, ax = plt.subplots(figsize=(16, 9))
    
    for dados in dados_grafico:
        arquivo = dados['arquivo']
        x = dados['x']
        y = dados['y']
        modelo = dados['modelo']
        params = dados['params']
        
        nome_arquivo_limpo = arquivo.replace('.csv', '')
        cor = CORES.get(nome_arquivo_limpo, "#000000")
        marcador = MARCADORES.get(nome_arquivo_limpo, "o")
        
        ax.scatter(x, y, color=cor, s=60, alpha=0.6, 
                  label=f'{nome_arquivo_limpo}',
                  marker=marcador, zorder=3, edgecolors='black', linewidth=0.5)
        
        modelo_func, _ = MODELS[modelo]
        x_smooth = np.linspace(min(x), max(x), 300)
        y_smooth = modelo_func(x_smooth, *params)
        ax.plot(x_smooth, y_smooth, color=cor, linewidth=2.5, 
               linestyle='--', alpha=0.8, zorder=2)
    
    if x_min is not None or x_max is not None:
        ax.set_xlim(x_min, x_max)
    if y_min is not None or y_max is not None:
        ax.set_ylim(y_min, y_max)
    
    ax.set_xlabel('n', fontsize=18, fontweight='bold')
    ax.set_ylabel('Comparações', fontsize=18, fontweight='bold')
    ax.set_title(f'Número de comparações em relação a n', 
                fontsize=20, fontweight='bold', pad=20)
    
    ax.tick_params(axis='both', which='major', labelsize=14)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
    ax.legend(fontsize=19, loc='best', framealpha=0.95, ncol=2)
    
    caminho_grafico = os.path.join(GRAPHS_DIR, f"comparacao_buscas.png")
    fig.savefig(caminho_grafico, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    print(f"OK Grafico salvo: {caminho_grafico}")
    return caminho_grafico

# ======================================================
# EXECUÇÃO PRINCIPAL
# ======================================================

all_results = []
dados_por_metrica = []

open(REPORT_FILE, "w", encoding="utf-8").close()

for file in FILES:
    path = os.path.join(OUTPUT_DIR, file)
    
    if not os.path.exists(path):
        print(f"⚠️  Arquivo não encontrado: {path}")
        continue
    
    df = pd.read_csv(path)
    
    # Verificar se coluna existe
    if COLUNA_METRICA not in df.columns:
        print(f"❌ Coluna '{COLUNA_METRICA}' não encontrada em {file}")
        print(f"   Colunas disponíveis: {df.columns.tolist()}")
        continue
    
    data = df.copy()
    data[COLUNA_METRICA] = pd.to_numeric(data[COLUNA_METRICA], errors="coerce")
    data = data.dropna(subset=["n", COLUNA_METRICA])
    
    if len(data) < 5:
        print(f"⚠️  {file} tem poucos dados ({len(data)} < 5)")
        continue
    
    x = data["n"].values
    y = data[COLUNA_METRICA].values
    
    models = fit_models(x, y)
    
    if not models:
        print(f"❌ Nenhum modelo se ajustou a {file}")
        continue
    
    best = models[0]
    modelo = best["modelo"]
    parametros = best["parametros"]
    
    eq = equation(modelo, parametros)
    deriv = derivative(modelo, parametros)
    n_final = max(x)
    taxa = derivative_value(modelo, parametros, n_final)
    
    print("\n==============================")
    print("✓ Arquivo:", file)
    print("  Modelo:", modelo)
    print("  Equacao:", eq)
    print("  R2:", f"{best['r2']:.6f}")
    print("  RMSE:", f"{best['rmse']:.6f}")
    
    with open(REPORT_FILE, "a", encoding="utf-8") as report:
        report.write("\n==============================\n")
        report.write(f"Arquivo: {file}\n")
        report.write(f"Modelo: {modelo}\n")
        report.write(f"Equacao: {eq}\n")
        report.write(f"Derivada: {deriv}\n")
        report.write(f"n_final: {n_final}\n")
        report.write(f"Taxa_variacao_final: {taxa:.8e}\n")
        report.write(f"R2_ajustado: {best['r2']:.8f}\n")
        report.write(f"RMSE: {best['rmse']:.8f}\n")
    
    all_results.append({
        "arquivo": file,
        "modelo": modelo,
        "equacao": eq,
        "derivada": deriv,
        "n_final": n_final,
        "taxa_variacao_final": taxa,
        "r2_ajustado": best["r2"],
        "rmse": best["rmse"]
    })
    
    dados_por_metrica.append({
        'arquivo': file,
        'x': x,
        'y': y,
        'modelo': modelo,
        'params': parametros,
        'r2': best['r2']
    })

print("\n" + "="*50)
print("GERANDO GRÁFICO")
print("="*50)

if dados_por_metrica:
    try:
        gerar_grafico_unico(dados_por_metrica, X_MIN, X_MAX, Y_MIN, Y_MAX)
        print("✓ Gráfico gerado com sucesso!")
    except Exception as e:
        print(f"❌ ERRO ao gerar gráfico: {e}")

if all_results:
    resultado = pd.DataFrame(all_results)
    resultado.to_csv(RESULT_FILE, index=False)
    print(f"✓ Resultados salvos em: {RESULT_FILE}")
else:
    print("❌ Nenhum resultado para salvar")

print("\n" + "="*50)
print("ANÁLISE CONCLUÍDA")
print("="*50)