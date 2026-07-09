@echo off
rem Executa a aplicacao final.
rem Uso:  executar.bat [limite_de_registros] [caminho_do_csv]
rem Padrao: 100000 registros, CSV procurado em .\ e ..\solarradiation.csv

cd /d "%~dp0"
java -jar AplicacaoEDI.jar %*
