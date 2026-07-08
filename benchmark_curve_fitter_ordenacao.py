import os
import glob
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score, mean_squared_error


OUTPUT_DIR = "output_ordenacao"

OUTPUT_CSV = "resultado_regressoes_ordenacao.csv"
OUTPUT_TXT = "relatorio_regressoes_ordenacao.txt"


METRICS = [
    "comparisons",
    "copies",
    "time_ns"
]


# =====================================================
# MODELOS
# =====================================================

def constant(x, a):
    return np.full_like(x, a)


def logarithmic(x, a, b):
    return a*np.log(x)+b


def linear(x, a, b):
    return a*x+b


def nlogn(x, a, b):
    return a*x*np.log(x)+b


def quadratic(x, a, b, c):
    return a*x*x+b*x+c



MODELS = {

    "O(1)": (
        constant,
        1
    ),

    "O(log n)": (
        logarithmic,
        2
    ),

    "O(n)": (
        linear,
        2
    ),

    "O(n log n)": (
        nlogn,
        2
    ),

    "O(n²)": (
        quadratic,
        3
    )
}



# =====================================================
# DERIVADAS
# =====================================================

def derivative(model, params, n):

    if model == "O(1)":

        return 0


    elif model == "O(log n)":

        a = params[0]

        return a/n


    elif model == "O(n)":

        a = params[0]

        return a


    elif model == "O(n log n)":

        a = params[0]

        return a*(np.log(n)+1)


    elif model == "O(n²)":

        a,b,c = params

        return 2*a*n+b



# =====================================================
# MÉTRICAS
# =====================================================

def adjusted_r2(y, pred, k):

    n=len(y)

    r2=r2_score(
        y,
        pred
    )

    return 1-((1-r2)*(n-1))/(n-k-1)



def rmse(y,pred):

    return np.sqrt(
        mean_squared_error(
            y,
            pred
        )
    )



# =====================================================
# AJUSTE DOS MODELOS
# =====================================================

def fit_models(x,y):

    results=[]


    for name,(model,k) in MODELS.items():

        try:

            params,_ = curve_fit(
                model,
                x,
                y,
                maxfev=50000
            )


            prediction = model(
                x,
                *params
            )


            results.append({

                "modelo":name,

                "params":params,

                "r2":adjusted_r2(
                    y,
                    prediction,
                    k
                ),

                "rmse":rmse(
                    y,
                    prediction
                )

            })


        except Exception:

            pass


    return sorted(
        results,
        key=lambda x:x["r2"],
        reverse=True
    )



# =====================================================
# EQUAÇÃO
# =====================================================

def equation(name,p):

    if name=="O(1)":

        return (
            f"y = {p[0]:.6f}"
        )


    if name=="O(log n)":

        return (
            f"y = {p[0]:.6f}ln(n)"
            f" + {p[1]:.6f}"
        )


    if name=="O(n)":

        return (
            f"y = {p[0]:.6f}n"
            f" + {p[1]:.6f}"
        )


    if name=="O(n log n)":

        return (
            f"y = {p[0]:.6e}nln(n)"
            f" + {p[1]:.6f}"
        )


    if name=="O(n²)":

        return (
            f"y = {p[0]:.6e}n²"
            f" + {p[1]:.6f}n"
            f" + {p[2]:.6f}"
        )



# =====================================================
# EXECUÇÃO
# =====================================================

results=[]


files = glob.glob(
    os.path.join(
        OUTPUT_DIR,
        "*.csv"
    )
)


with open(
        OUTPUT_TXT,
        "w",
        encoding="utf-8"
) as report:


    for file in files:


        filename = os.path.basename(file)


        df=pd.read_csv(file)



        for metric in METRICS:


            temp=df.copy()


            temp[metric]=pd.to_numeric(
                temp[metric],
                errors="coerce"
            )


            temp=temp.dropna(
                subset=[
                    "n",
                    metric
                ]
            )


            if len(temp)<5:
                continue



            x=temp["n"].values
            y=temp[metric].values


            models=fit_models(
                x,
                y
            )


            if not models:
                continue



            best=models[0]


            n_final=max(x)


            eq=equation(
                best["modelo"],
                best["params"]
            )


            deriv=derivative(
                best["modelo"],
                best["params"],
                n_final
            )



            print(
                filename,
                metric,
                best["modelo"],
                best["r2"]
            )



            report.write(
                "\n============================\n"
            )

            report.write(
                f"Arquivo: {filename}\n"
            )

            report.write(
                f"Metrica: {metric}\n"
            )

            report.write(
                f"Modelo: {best['modelo']}\n"
            )

            report.write(
                f"Equacao: {eq}\n"
            )

            report.write(
                f"Derivada em n={n_final}: {deriv}\n"
            )

            report.write(
                f"R2 ajustado: {best['r2']}\n"
            )

            report.write(
                f"RMSE: {best['rmse']}\n"
            )



            results.append({

                "arquivo":filename,

                "metrica":metric,

                "modelo":best["modelo"],

                "equacao":eq,

                "derivada":deriv,

                "n_final":n_final,

                "taxa_variacao_final":deriv,

                "r2_ajustado":best["r2"],

                "rmse":best["rmse"]

            })



pd.DataFrame(
    results
).to_csv(
    OUTPUT_CSV,
    index=False
)


print("\nAnálise concluída.")
print("Gerados:")
print(OUTPUT_CSV)
print(OUTPUT_TXT)