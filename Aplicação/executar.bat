@echo off
rem Executa a aplicacao final.
rem Uso:  executar.bat [limite_de_registros] [caminho_do_csv]
rem Padrao: csv inteiro (~7 milhoes de registros), procurado em .\ e ..\solarradiation.csv
rem -Xmx4g: a base completa ocupa ~2GB de heap

cd /d "%~dp0"
java -Xmx4g -jar AplicacaoEDI.jar %*
