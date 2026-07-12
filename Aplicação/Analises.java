import java.util.ArrayList;
import java.util.List;

// consultas de análise sobre os dados da AVL. a árvore é chaveada pelo id,
// então busca por data/comprimento de onda percorre a árvore em-ordem
// contando comparações e o nível onde o resultado apareceu. os limites de
// data são exceção: como os ids do csv crescem em ordem cronológica, dá pra
// descer direto pelas bordas da árvore.
// cada operação devolve um registro de execução no formato pedido.
public class Analises {

    private final TArvoreAVL arvore;

    private long comps;
    private long visitados;
    private long achados;
    private double soma;

    private Registro melhor;
    private double melhorValor;
    private int melhorNivel;
    private double melhorDiff;

    private Registro melhorB;
    private double melhorValorB;
    private int melhorNivelB;

    public Analises(TArvoreAVL arvore) {
        this.arvore = arvore;
    }

    private interface Visita {
        void no(TArvoreAVL.TNodo t, int nivel);
    }

    private void percorre(TArvoreAVL.TNodo t, int nivel, Visita v) {
        if (t == null) return;
        percorre(t.esq, nivel + 1, v);
        v.no(t, nivel);
        percorre(t.dir, nivel + 1, v);
    }

    private void zera() {
        comps = 0; visitados = 0; achados = 0; soma = 0;
        melhor = null; melhorValor = 0; melhorNivel = 0;
        melhorDiff = Double.MAX_VALUE;
        melhorB = null; melhorValorB = 0; melhorNivelB = 0;
    }

    // 1) maior emissão de uma data
    public String maiorEmissaoNaData(String data) {
        zera();
        long inicio = System.nanoTime();

        percorre(arvore.T, 1, (t, nivel) -> {
            visitados++;
            comps++;
            if (data.equals(t.item.date)) {
                achados++;
                double irr = num(t.item.irradiance);
                if (!Double.isNaN(irr) && (melhor == null || irr > melhorValor)) {
                    melhor = t.item;
                    melhorValor = irr;
                    melhorNivel = nivel;
                }
            }
        });

        long tempo = System.nanoTime() - inicio;

        String resultado = melhor == null
                ? "nenhum registro para a data " + data + "."
                : String.format("comprimento de onda %s nm com irradiância %s W/m²/nm.",
                        melhor.minWavelength, melhor.irradiance);

        String nivel = melhor == null ? null
                : String.format("Encontrado no nível %d da AVL.", melhorNivel);

        return registro("maior emissão na data", "data = " + data, resultado, nivel, tempo);
    }

    // 2) data em que um comprimento de onda tem a maior emissão
    public String dataDeMaiorEmissao(double lambda) {
        zera();
        long inicio = System.nanoTime();

        percorre(arvore.T, 1, (t, nivel) -> {
            visitados++;
            comps++;
            double wl = num(t.item.minWavelength);
            double irr = num(t.item.irradiance);
            if (Double.isNaN(wl) || Double.isNaN(irr)) return;

            double diff = Math.abs(wl - lambda);
            if (diff < melhorDiff - 1e-9) {
                melhorDiff = diff;
                melhor = t.item;
                melhorValor = irr;
                melhorNivel = nivel;
            } else if (diff <= melhorDiff + 1e-9 && irr > melhorValor) {
                melhor = t.item;
                melhorValor = irr;
                melhorNivel = nivel;
            }
        });

        long tempo = System.nanoTime() - inicio;

        String resultado = melhor == null
                ? "nenhum registro no banco."
                : String.format("data %s com irradiância %s W/m²/nm (comprimento de onda mais próximo do informado: %s nm).",
                        melhor.date, melhor.irradiance, melhor.minWavelength);

        String nivel = melhor == null ? null
                : String.format("Encontrado no nível %d da AVL.", melhorNivel);

        return registro("data de maior emissão do comprimento de onda",
                String.format("comprimento de onda = %s nm", fmtNum(lambda)), resultado, nivel, tempo);
    }

    // 3) menor e maior data do banco
    public String limitesDeDatas() {
        zera();
        long inicio = System.nanoTime();

        if (arvore.T == null)
            return registro("menor e maior data do banco", "nenhum", "árvore vazia.", null, 0);

        TArvoreAVL.TNodo min = arvore.T;
        int nivelMin = 1;
        while (min.esq != null) {
            comps++;
            min = min.esq;
            nivelMin++;
        }
        comps++;

        TArvoreAVL.TNodo max = arvore.T;
        int nivelMax = 1;
        while (max.dir != null) {
            comps++;
            max = max.dir;
            nivelMax++;
        }
        comps++;

        long tempo = System.nanoTime() - inicio;

        String resultado = String.format("primeira data %s (ID %d), última data %s (ID %d).",
                min.item.date, min.chave, max.item.date, max.chave);

        String nivel = String.format("Nó mais à esquerda no nível %d, mais à direita no nível %d.",
                nivelMin, nivelMax);

        return registro("menor e maior data do banco", "nenhum", resultado, nivel, tempo);
    }

    // 4) menor e maior comprimento de onda do banco
    public String limitesDeLambda() {
        zera();
        long inicio = System.nanoTime();

        percorre(arvore.T, 1, (t, nivel) -> {
            visitados++;
            comps++;
            double wl = num(t.item.minWavelength);
            if (Double.isNaN(wl)) return;
            if (melhorB == null || wl < melhorValorB) {
                melhorB = t.item;
                melhorValorB = wl;
                melhorNivelB = nivel;
            }
            if (melhor == null || wl > melhorValor) {
                melhor = t.item;
                melhorValor = wl;
                melhorNivel = nivel;
            }
        });

        long tempo = System.nanoTime() - inicio;

        String resultado = melhor == null
                ? "nenhum registro no banco."
                : String.format("menor comprimento de onda %s nm, maior %s nm.",
                        melhorB.minWavelength, melhor.minWavelength);

        String nivel = melhor == null ? null
                : String.format("Menor no nível %d da AVL, maior no nível %d.",
                        melhorNivelB, melhorNivel);

        return registro("menor e maior comprimento de onda do banco", "nenhum", resultado, nivel, tempo);
    }

    // 5) média de emissão num intervalo de comprimento de onda de uma data
    public String mediaNoIntervalo(String data, double de, double ate) {
        zera();
        long inicio = System.nanoTime();

        percorre(arvore.T, 1, (t, nivel) -> {
            visitados++;
            comps++;
            if (data.equals(t.item.date)) {
                double wl = num(t.item.minWavelength);
                double irr = num(t.item.irradiance);
                if (!Double.isNaN(wl) && !Double.isNaN(irr) && wl >= de && wl <= ate) {
                    achados++;
                    soma += irr;
                }
            }
        });

        long tempo = System.nanoTime() - inicio;

        String resultado = achados == 0
                ? "nenhum registro da data " + data + " no intervalo."
                : String.format("média de irradiância %.6f W/m²/nm em %,d registros.",
                        soma / achados, achados);

        return registro("média de emissão no intervalo de comprimento de onda",
                String.format("data = %s, intervalo = %s a %s nm", data, fmtNum(de), fmtNum(ate)),
                resultado, null, tempo);
    }

    // 6) pesquisa genérica: data e/ou um campo qualquer do registro,
    // listando os que baterem. o limite evita estourar o log quando o
    // filtro casa com milhares de registros.
    private static final int MAX_LISTADOS = 200;

    public String pesquisaPorCampos(String data, String campo, String valor) {
        zera();
        long inicio = System.nanoTime();

        int idx = 0;
        for (int i = 0; i < Registro.COLUNAS.length; i++)
            if (Registro.COLUNAS[i].equals(campo)) idx = i;
        final int campoIdx = idx;

        final boolean filtraData = data != null && !data.isEmpty();
        final boolean filtraCampo = valor != null && !valor.isEmpty();
        final double valorNum = filtraCampo ? num(valor) : Double.NaN;

        StringBuilder lista = new StringBuilder();

        percorre(arvore.T, 1, (t, nivel) -> {
            visitados++;
            comps++;
            if (filtraData && !data.equals(t.item.date)) return;
            if (filtraCampo) {
                String v = String.valueOf(t.item.toRow()[campoIdx]);
                double vn = num(v);
                boolean igual = (!Double.isNaN(vn) && !Double.isNaN(valorNum))
                        ? vn == valorNum
                        : v.equalsIgnoreCase(valor);
                if (!igual) return;
            }
            achados++;
            if (achados <= MAX_LISTADOS)
                lista.append(String.format("  nível %d: ID=%d, date=%s, λ=%s nm, irradiância=%s%n",
                        nivel, t.item.id, t.item.date, t.item.minWavelength, t.item.irradiance));
        });

        long tempo = System.nanoTime() - inicio;

        if (achados > MAX_LISTADOS)
            lista.append(String.format("  (+%,d registros não exibidos)%n", achados - MAX_LISTADOS));

        String params = (filtraData ? "data = " + data : "")
                + (filtraData && filtraCampo ? ", " : "")
                + (filtraCampo ? campo + " = " + valor : "");

        String resultado = String.format("%,d registros encontrados.", achados);

        return registro("pesquisa por campos", params, resultado,
                achados == 0 ? null : lista.toString().stripTrailing(), tempo);
    }

    // 7) pontos (comprimento de onda, irradiância) de uma data pro gráfico.
    // o em-ordem por id já devolve os comprimentos de onda em ordem crescente
    // dentro da mesma data, do jeito que o csv é organizado.
    public static class Espectro {
        public final List<double[]> pontos = new ArrayList<>();
        public String registro;
    }

    public Espectro espectroDaData(String data) {
        zera();
        long inicio = System.nanoTime();

        Espectro e = new Espectro();
        percorre(arvore.T, 1, (t, nivel) -> {
            visitados++;
            comps++;
            if (data.equals(t.item.date)) {
                double wl = num(t.item.minWavelength);
                double irr = num(t.item.irradiance);
                if (!Double.isNaN(wl) && !Double.isNaN(irr))
                    e.pontos.add(new double[]{wl, irr});
            }
        });

        long tempo = System.nanoTime() - inicio;

        e.registro = registro("espectro de emissão da data", "data = " + data,
                String.format("%,d pontos (comprimento de onda × irradiância) para o gráfico.", e.pontos.size()),
                null, tempo);
        return e;
    }

    private String registro(String operacao, String params, String resultado, String nivel, long tempo) {
        return "Busca realizada: " + operacao + ".\n"
                + "Parâmetros: " + params + ".\n"
                + "Resultado: " + resultado + "\n"
                + (nivel == null ? "" : nivel + "\n")
                + "Comparações realizadas: " + String.format("%,d", comps) + ".\n"
                + "Tempo de execução: " + fmtNs(tempo) + ".\n"
                + "Altura da AVL: " + arvore.altura() + ".\n";
    }

    private static double num(String s) {
        try {
            return Double.parseDouble(s.trim());
        } catch (Exception e) {
            return Double.NaN;
        }
    }

    private static String fmtNum(double v) {
        return v == Math.rint(v) ? String.format("%.0f", v) : String.format("%.2f", v);
    }

    private static String fmtNs(long ns) {
        if (ns < 1_000L) return ns + " ns";
        if (ns < 1_000_000L) return String.format("%.1f µs", ns / 1e3);
        if (ns < 1_000_000_000L) return String.format("%.1f ms", ns / 1e6);
        return String.format("%.2f s", ns / 1e9);
    }
}
