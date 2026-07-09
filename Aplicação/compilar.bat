@echo off
rem compila e gera o AplicacaoEDI.jar
cd /d "%~dp0"

set "JAR=jar"
where jar >nul 2>nul || set "JAR=C:\Program Files\Java\latest\bin\jar.exe"

javac -encoding UTF-8 *.java || goto :erro
"%JAR%" cfe AplicacaoEDI.jar AplicacaoFinal *.class || goto :erro

echo.
echo OK! Execute com:  java -jar AplicacaoEDI.jar
pause
exit /b 0

:erro
echo FALHOU.
pause
exit /b 1
