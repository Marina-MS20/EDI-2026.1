import os
import pandas as pd
import numpy as np

from scipy.optimize import curve_fit
from sklearn.metrics import r2_score, mean_squared_error


# ======================================================
# CONFIGURAÇÕES
# ======================================================

OUTPUT_DIR = "output"

RESULT_FILE = "resultado_regressoes_busca.csv"
REPORT_FILE = "relatorio_regressoes_busca.txt"


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


    "Linear":
    (
        linear,
        2
    ),


    "Logarithmic":
    (
        logarithmic,
        2
    ),


    "Quadratic":
    (
        quadratic,
        3
    ),


    "Power":
    (
        power,
        2
    ),


    "NLogN":
    (
        nlogn,
        2
    )

}






# ======================================================
# MÉTRICAS ESTATÍSTICAS
# ======================================================


def adjusted_r2(y, y_pred, params):

    n = len(y)

    r2 = r2_score(
        y,
        y_pred
    )


    return 1 - (
        ((1-r2)*(n-1))
        /
        (n-params-1)
    )




def rmse(y, y_pred):

    return np.sqrt(
        mean_squared_error(
            y,
            y_pred
        )
    )





# ======================================================
# AJUSTE DOS MODELOS
# ======================================================


def fit_models(x,y):

    results=[]


    for name,(model,param_count) in MODELS.items():


        try:


            popt,_ = curve_fit(

                model,
                x,
                y,
                maxfev=50000

            )



            prediction = model(

                x,
                *popt

            )



            results.append({

                "modelo":name,

                "parametros":popt,

                "r2":adjusted_r2(

                    y,
                    prediction,
                    param_count

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
# ======================================================
# EQUAÇÕES
# ======================================================


def equation(name,p):


    if name=="Linear":

        return (
            f"y = {p[0]:.6e}*n "
            f"+ {p[1]:.6f}"
        )



    if name=="Logarithmic":

        return (
            f"y = {p[0]:.6e}*ln(n) "
            f"+ {p[1]:.6f}"
        )



    if name=="Quadratic":

        return (
            f"y = {p[0]:.6e}*n² "
            f"+ {p[1]:.6e}*n "
            f"+ {p[2]:.6f}"
        )



    if name=="Power":

        return (
            f"y = {p[0]:.6e}*n^{p[1]:.6f}"
        )



    if name=="NLogN":

        return (
            f"y = {p[0]:.6e}*n*ln(n) "
            f"+ {p[1]:.6f}"
        )






# ======================================================
# DERIVADAS SIMBÓLICAS
# ======================================================


def derivative(name,p):


    if name=="Linear":

        return (
            f"dy/dn = {p[0]:.6e}"
        )



    if name=="Logarithmic":

        return (
            f"dy/dn = "
            f"{p[0]:.6e}/n"
        )



    if name=="Quadratic":

        return (

            f"dy/dn = "
            f"{2*p[0]:.6e}*n "
            f"+ {p[1]:.6e}"

        )



    if name=="Power":

        return (

            f"dy/dn = "
            f"{p[0]*p[1]:.6e}"
            f"*n^({p[1]-1:.6f})"

        )



    if name=="NLogN":

        return (

            f"dy/dn = "
            f"{p[0]:.6e}"
            f"*(ln(n)+1)"

        )






# ======================================================
# CALCULA VALOR DA DERIVADA NO PONTO FINAL
# ======================================================


def derivative_value(name,p,n):


    if name=="Linear":

        return p[0]



    if name=="Logarithmic":

        return (

            p[0]/n

        )



    if name=="Quadratic":

        return (

            2*p[0]*n+p[1]

        )



    if name=="Power":

        return (

            p[0]*p[1]*(n**(p[1]-1))

        )



    if name=="NLogN":

        return (

            p[0]*(np.log(n)+1)

        )




# ======================================================
# EXECUÇÃO PRINCIPAL
# ======================================================


all_results=[]



with open(

    REPORT_FILE,

    "w",

    encoding="utf-8"

) as report:



    for file in FILES:



        path=os.path.join(

            OUTPUT_DIR,

            file

        )



        if not os.path.exists(path):

            continue



        df=pd.read_csv(path)




        for metric in METRICS:



            data=df.copy()



            data[metric]=pd.to_numeric(

                data[metric],

                errors="coerce"

            )



            data=data.dropna(

                subset=[

                    "n",

                    metric

                ]

            )



            if len(data)<5:

                continue



            x=data["n"].values

            y=data[metric].values




            models=fit_models(

                x,

                y

            )



            if not models:

                continue



            best=models[0]



            modelo=best["modelo"]

            parametros=best["parametros"]



            eq=equation(

                modelo,

                parametros

            )



            deriv=derivative(

                modelo,

                parametros

            )



            n_final=max(x)



            taxa=derivative_value(

                modelo,

                parametros,

                n_final

            )
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

            report.write(
                "\n==============================\n"
            )

            report.write(
                f"Arquivo: {file}\n"
            )

            report.write(
                f"Metrica: {metric}\n"
            )

            report.write(
                f"Modelo: {modelo}\n"
            )

            report.write(
                f"Equacao: {eq}\n"
            )

            report.write(
                f"Derivada: {deriv}\n"
            )

            report.write(
                f"n_final: {n_final}\n"
            )

            report.write(
                f"Taxa_variacao_final: {taxa:.8e}\n"
            )

            report.write(
                f"R2_ajustado: {best['r2']:.8f}\n"
            )

            report.write(
                f"RMSE: {best['rmse']:.8f}\n"
            )




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





# ======================================================
# EXPORTAÇÃO FINAL
# ======================================================


resultado = pd.DataFrame(

    all_results

)



resultado.to_csv(

    RESULT_FILE,

    index=False

)



print("\n================================")
print("Análise concluída.")
print("Arquivos gerados:")
print(RESULT_FILE)
print(REPORT_FILE)