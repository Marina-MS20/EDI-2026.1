import java.io.*;
import java.util.*;

public class MainBusca {

    private static final String CSV_FILE = "solarradiation.csv";
    private static final int TEST_SIZE = 2000;

    // ---- medição de tempo ----
    // Uma busca individual leva de ~100 ns a poucos µs — rápido demais para
    // cronometrar uma a uma: o overhead do System.nanoTime() e o ruído do
    // JIT/SO dominam a medida e o resultado oscila. Em vez disso, mede-se o
    // lote inteiro de TEST_SIZE buscas num ÚNICO bloco de nanoTime, e o lote
    // é repetido até acumular pelo menos MIN_MEASURE_NS de tempo medido.
    // O tempo gravado no CSV é normalizado para REFERENCE_SEARCHES buscas,
    // colocando a escala em milissegundos e comparável entre estruturas.
    private static final long MIN_MEASURE_NS = 25_000_000L; // mede no mínimo 25 ms
    // Teto de segurança apenas: o laço para ao atingir MIN_MEASURE_NS, mas
    // lotes minúsculos (n pequeno -> poucas buscas) precisam de milhares de
    // repetições para acumular tempo suficiente e sair da zona de ruído.
    private static final int  MAX_REPEATS = 1_000_000;
    private static final int  REFERENCE_SEARCHES = 10_000;  // tempo reportado = p/ 10 mil buscas

    // Buscas de aquecimento executadas SEM medição antes do cronômetro:
    // os primeiros lotes rodam em código ainda não compilado pelo JIT e
    // saem inflados (pico artificial nos primeiros pontos de n).
    private static final int  WARMUP_SEARCHES = 1000;

    // seed fixa e usada de forma determinística por n (ver gerarVariantes)
    private static final long BASE_SEED = 42L;

    private static final String OUTPUT_DIR = "output";
    private static final String REPORT_FILE = OUTPUT_DIR + "/fail_report.txt";

    enum Mode { FIXED_STEP, GROWTH_STEP }

    // modo ativo do experimento — troque aqui para alternar
    private static final Mode MODE = Mode.GROWTH_STEP;

    // ---- parâmetros do modo antigo (FIXED_STEP): incremento aditivo fixo ----
    private static final int FIXED_STEP = 10_000;
    private static final int FIXED_MAX_N = 200_000;
    private static final int FIXED_FINE_STEP = Math.max(FIXED_STEP / 10, 1000);

    // ---- parâmetros do modo novo (GROWTH_STEP): incremento multiplicativo ----
    // GROWTH_MAX_N reaproveita o mesmo teto do modo fixo (7.000.000) para
    // explorar a mesma faixa; ajuste se quiser outro teto.
    private static final int GROWTH_START_N = 10;
    private static final int GROWTH_MAX_N = FIXED_MAX_N;
    private static final double GROWTH_FACTOR = 1.10;
    private static final double GROWTH_FINE_FACTOR = 1.02;

    // teto separado para a AVL: o balanco() recalcula as alturas
    // percorrendo as subárvores inteiras a cada inserção (O(n) por inserção,
    // O(n²) no total) — medido ~28s para construir com n=100.000. Acima disso
    // a construção fica inviável para o benchmark.
    private static final int AVL_MAX_N = 100_000;

    static Map<String, BufferedWriter> writers = new HashMap<>();

    static Set<String> activeABB = new HashSet<>();
    static Set<String> activeAVL = new HashSet<>();

    // n onde cada estrutura estourou na fase coarse (o "ponto de falha" bruto)
    static Map<String, Integer> failPoint = new HashMap<>();

    // último n em que cada estrutura ainda funcionou na fase coarse
    // (usado para limitar a janela de busca da fase fine)
    static Map<String, Integer> lastSuccess = new HashMap<>();

    public static void main(String[] args) throws Exception {

        new File(OUTPUT_DIR).mkdirs();

        log("Modo de experimento: " + MODE);
        log("Carregando dataset de '" + CSV_FILE + "'...");
        List<Long> dataset = loadIds(CSV_FILE);
        log("Dataset carregado: " + dataset.size() + " registros.");

        init("seq_random.csv");
        init("seq_sorted.csv");
        init("seq_reverse.csv");
        init("bin.csv");

        init("abb_random.csv");
        init("abb_sorted.csv");
        init("abb_reverse.csv");

        init("avl_random.csv");
        init("avl_sorted.csv");
        init("avl_reverse.csv");

        activeABB.add("abb_random");
        activeABB.add("abb_sorted");
        activeABB.add("abb_reverse");

        activeAVL.add("avl_random");
        activeAVL.add("avl_sorted");
        activeAVL.add("avl_reverse");

        try (BufferedWriter report =
                     new BufferedWriter(new FileWriter(REPORT_FILE))) {

            report.write("STRUCTURE,PHASE,N,ERROR\n");
            report.newLine();

            // ===================== FASE COARSE =====================

            List<Integer> coarseSeq = buildCoarseSequence(dataset.size());
            log("Iniciando FASE COARSE — " + coarseSeq.size() + " pontos de n (de "
                    + coarseSeq.get(0) + " a " + coarseSeq.get(coarseSeq.size() - 1) + ")");

            for (int i = 0; i < coarseSeq.size(); i++) {

                int n = coarseSeq.get(i);
                double pct = ((i + 1) * 100.0) / coarseSeq.size();
                log(String.format("[COARSE %5.1f%%] processando n=%d", pct, n));

                Variants v = gerarVariantes(dataset, n, TEST_SIZE);

                write("seq_random.csv", n, benchmarkSequential(v.random, v.testSet));
                write("seq_sorted.csv", n, benchmarkSequential(v.sorted, v.testSet));
                write("seq_reverse.csv", n, benchmarkSequential(v.reverse, v.testSet));
                write("bin.csv", n, benchmarkBinary(v.sorted, v.testSet));

                if (activeABB.contains("abb_random"))
                    safeRunABB("abb_random.csv", "abb_random", n, v.random, v.testSet, report);

                if (activeABB.contains("abb_sorted"))
                    safeRunABB("abb_sorted.csv", "abb_sorted", n, v.sorted, v.testSet, report);

                if (activeABB.contains("abb_reverse"))
                    safeRunABB("abb_reverse.csv", "abb_reverse", n, v.reverse, v.testSet, report);

                // AVL tem teto próprio: construção O(n²) (ver AVL_MAX_N)
                if (n <= AVL_MAX_N) {
                    if (activeAVL.contains("avl_random"))
                        safeRunAVL("avl_random.csv", "avl_random", n, v.random, v.testSet, report);

                    if (activeAVL.contains("avl_sorted"))
                        safeRunAVL("avl_sorted.csv", "avl_sorted", n, v.sorted, v.testSet, report);

                    if (activeAVL.contains("avl_reverse"))
                        safeRunAVL("avl_reverse.csv", "avl_reverse", n, v.reverse, v.testSet, report);
                }
            }

            log(String.format("[COARSE 100.0%%] fase coarse concluída."));

            // ===================== FASE FINE =====================
            //
            // Para cada estrutura que estourou na fase coarse, refaz a busca
            // exatamente com o mesmo pipeline de geração de dados (mesmo
            // slice, mesmo sort, mesmo shuffle com seed derivada de n),
            // porém em incrementos menores, partindo do último n que ainda
            // funcionou até o n onde a falha ocorreu — e para assim que
            // estourar de novo (não continua além disso).

            if (failPoint.isEmpty()) {
                log("Nenhuma estrutura estourou na fase coarse — FASE FINE não será executada.");
            } else {
                log("Iniciando FASE FINE para: " + failPoint.keySet());
            }

            for (String structure : new ArrayList<>(failPoint.keySet())) {

                int coarseFailN = failPoint.get(structure);
                int fromN = lastSuccess.getOrDefault(structure, 0);

                List<Integer> fineSeq = buildFineSequence(fromN, coarseFailN);

                log("[FINE] " + structure + ": refinando janela n=" + fromN + ".." + coarseFailN
                        + " (" + fineSeq.size() + " pontos)");

                for (int i = 0; i < fineSeq.size(); i++) {

                    int n = fineSeq.get(i);
                    double pct = ((i + 1) * 100.0) / fineSeq.size();
                    log(String.format("[FINE %s %5.1f%%] processando n=%d", structure, pct, n));

                    Variants v = gerarVariantes(dataset, n, TEST_SIZE);

                    List<Long> data = structure.endsWith("random") ? v.random
                            : structure.endsWith("sorted") ? v.sorted
                            : v.reverse;

                    boolean estourouDeNovo;

                    if (structure.startsWith("abb")) {
                        estourouDeNovo = !safeRunABB(structure + ".csv", structure, n, data, v.testSet, report, "FINE");
                    } else {
                        estourouDeNovo = !safeRunAVL(structure + ".csv", structure, n, data, v.testSet, report, "FINE");
                    }

                    if (estourouDeNovo) {
                        log("[FINE " + structure + "] ESTOUROU DE NOVO em n=" + n + " — encerrando refinamento desta estrutura.");
                        break; // para de buscar para essa estrutura
                    }
                }
            }

            log("Fase fine concluída.");
        }

        closeWriters();
        log("Benchmark concluído. Resultados em '" + OUTPUT_DIR + "'.");
    }

    // ===================== SEQUÊNCIAS DE n =====================

    static List<Integer> buildCoarseSequence(int datasetSize) {
        if (MODE == Mode.FIXED_STEP) {
            int limit = Math.min(FIXED_MAX_N, datasetSize);
            List<Integer> seq = new ArrayList<>();
            for (int n = FIXED_STEP; n <= limit; n += FIXED_STEP) seq.add(n);
            return seq;
        } else {
            int limit = Math.min(GROWTH_MAX_N, datasetSize);
            return buildGrowthSequence(GROWTH_START_N, limit, GROWTH_FACTOR, true);
        }
    }

    static List<Integer> buildFineSequence(int fromN, int toN) {
        if (MODE == Mode.FIXED_STEP) {
            List<Integer> seq = new ArrayList<>();
            for (int n = fromN + FIXED_FINE_STEP; n <= toN; n += FIXED_FINE_STEP) seq.add(n);
            return seq;
        } else {
            return buildGrowthSequence(Math.max(fromN, 1), toN, GROWTH_FINE_FACTOR, false);
        }
    }

    /**
     * Gera uma sequência de n crescendo multiplicativamente por 'factor',
     * partindo de 'start' até 'max' (inclusive). Se includeStart=false, o
     * valor 'start' em si é excluído do resultado (usado na fase fine,
     * onde 'start' já foi testado com sucesso na fase anterior).
     */
    static List<Integer> buildGrowthSequence(double start, int max, double factor, boolean includeStart) {
        List<Integer> seq = new ArrayList<>();

        double cur = start;
        int lastAdded;

        int firstN = (int) Math.round(cur);
        if (includeStart && firstN <= max) {
            seq.add(firstN);
            lastAdded = firstN;
        } else {
            lastAdded = firstN;
        }

        cur = Math.max(cur * factor, lastAdded + 1);

        while (true) {
            int n = (int) Math.round(cur);
            if (n <= lastAdded) n = lastAdded + 1;
            if (n > max) break;

            seq.add(n);
            lastAdded = n;
            cur = Math.max(n * factor, n + 1);
        }

        if (seq.isEmpty()) {
            // garante ao menos um ponto (ex.: janela fine muito estreita)
            seq.add(Math.min(max, lastAdded + 1));
        }

        return seq;
    }

    // ===================== GERAÇÃO DETERMINÍSTICA DE DADOS =====================

    static class Variants {
        List<Long> base;
        List<Long> sorted;
        List<Long> reverse;
        List<Long> random;
        List<Long> testSet;
    }

    /**
     * Gera, de forma 100% determinística, base/sorted/reverse/random/testSet
     * para um dado n. A seed usada é derivada de (BASE_SEED, n), e não de um
     * Random compartilhado que vai mudando de estado a cada chamada — por
     * isso, gerar os dados para um n específico dá sempre exatamente o mesmo
     * resultado, seja na fase coarse ou, mais tarde, na fase fine para o
     * mesmo n. Sem isso, a fase fine não reproduziria os mesmos dados que a
     * coarse produziu, e o "ponto de falha" refinado não seria confiável.
     */
    static Variants gerarVariantes(List<Long> dataset, int n, int testSize) {

        Variants v = new Variants();

        v.base = new ArrayList<>(dataset.subList(0, n));

        v.sorted = new ArrayList<>(v.base);
        Collections.sort(v.sorted);

        v.reverse = new ArrayList<>(v.sorted);
        Collections.reverse(v.reverse);

        Random shuffleRandom = new Random(BASE_SEED + n);
        v.random = new ArrayList<>(v.base);
        Collections.shuffle(v.random, shuffleRandom);

        // offset +1 pra não reusar a seed do shuffle acima: com a mesma seed,
        // Collections.shuffle produz a mesma permutação de índices sobre uma
        // lista do mesmo tamanho, então o testSet saía sempre igual aos
        // primeiros 'testSize' elementos de v.random — os alvos ficavam
        // sempre nas mesmas posições baixas, travando as comparações da
        // busca sequencial num valor quase constante, independente de n.
        Random testRandom = new Random(BASE_SEED + n + 1);
        v.testSet = pickTestSet(v.base, testSize, testRandom);

        return v;
    }

    // ===================== SAFE RUN =====================

    static boolean safeRunABB(String file, String name, int n,
                               List<Long> data, List<Long> tests,
                               BufferedWriter report) throws IOException {
        return safeRunABB(file, name, n, data, tests, report, "COARSE");
    }

    static boolean safeRunABB(String file, String name, int n,
                               List<Long> data, List<Long> tests,
                               BufferedWriter report, String phase) throws IOException {

        try {
            TArvore t = buildABB(data);
            Result r = benchmarkABB(t, tests);
            write(file, n, r);

            if (phase.equals("COARSE")) lastSuccess.put(name, n);

            return true;

        } catch (Throwable e) {

            if (phase.equals("COARSE")) {
                failPoint.put(name, n);
                activeABB.remove(name);
            }

            writeFail(file, n);

            report.write("ABB," + phase + "," + n + "," + e.getClass().getSimpleName());
            report.newLine();

            return false;
        }
    }

    static boolean safeRunAVL(String file, String name, int n,
                               List<Long> data, List<Long> tests,
                               BufferedWriter report) throws IOException {
        return safeRunAVL(file, name, n, data, tests, report, "COARSE");
    }

    static boolean safeRunAVL(String file, String name, int n,
                               List<Long> data, List<Long> tests,
                               BufferedWriter report, String phase) throws IOException {

        try {
            TArvoreAVL t = buildAVL(data);
            Result r = benchmarkAVL(t, tests);
            write(file, n, r);

            if (phase.equals("COARSE")) lastSuccess.put(name, n);

            return true;

        } catch (Throwable e) {

            if (phase.equals("COARSE")) {
                failPoint.put(name, n);
                activeAVL.remove(name);
            }

            writeFail(file, n);

            report.write("AVL," + phase + "," + n + "," + e.getClass().getSimpleName());
            report.newLine();

            return false;
        }
    }

    static TArvoreAVL buildAVL(List<Long> data) {
        TArvoreAVL t = new TArvoreAVL();
        for (long s : data) {
            t.insere(s);
        }
        return t;
    }

    static TArvore buildABB(List<Long> data) {
        TArvore t = new TArvore();
        for (long s : data) {
            t.insere(s);
        }
        return t;
    }

    // ===================== LOAD =====================

    // le a primeira coluna como numero - se carregar como String a ordenacao
    // vira lexicografica (1, 10, 100, 2, 20...) e sorted/reverse ficam errados
    static List<Long> loadIds(String file) throws IOException {

        List<Long> ids = new ArrayList<>();

        try (BufferedReader br = new BufferedReader(new FileReader(file))) {
            br.readLine();

            String line;
            while ((line = br.readLine()) != null) {
                String[] v = line.split(",", -1);
                if (v.length > 0 && !v[0].isEmpty()) ids.add(Long.parseLong(v[0]));
            }
        }

        return ids;
    }

    // ===================== ESTRUTURAS =====================
    //
    // TArvore (ABB) e TArvoreAVL seguem a implementação por apontadores do
    // prof. Alcides (NA03/NA04): nodos com esq/dir/pai, insere recursivo com
    // parâmetro pai, pesquisa recursiva, e na AVL o rebalanceamento AVL(p)
    // subindo pelos pais com balanco/balpreOrdem e rotacao_esquerda/direita.
    // Adaptações do benchmark: chave long direto no nodo (sem TInfo/nome),
    // contador de comparações e sem prints por inserção/rotação.
    //
    // A inserção recursiva é proposital: numa entrada ordenada ou em ordem
    // inversa, a ABB sem balanceamento degenera numa lista ligada com
    // profundidade O(n), e a recursão consome uma frame de pilha por nível —
    // para n grande o suficiente, isso estoura a pilha (StackOverflowError)
    // de verdade. É esse estouro que safeRunABB/AVL captura e registra.

    static class TArvore {

        static class TNodo {
            TNodo esq;
            long chave;
            TNodo dir;
            TNodo pai;

            TNodo(long chave, TNodo pai) {
                this.chave = chave;
                this.esq = null;
                this.dir = null;
                this.pai = pai;
            }
        }

        public TNodo T;
        long comparisons = 0;

        public void insere(long chave) {
            T = insere(T, chave, null);
        }

        public TNodo insere(TNodo T, long chave, TNodo pai) {
            if (T == null) {
                T = new TNodo(chave, pai);
            } else {
                pai = T;
                comparisons++;
                if (chave < T.chave)
                    T.esq = insere(T.esq, chave, pai);
                else if (chave > T.chave)
                    T.dir = insere(T.dir, chave, pai);
            }
            return T;
        }

        public TNodo pesquisa(long chave) {
            return pesquisa(T, chave);
        }

        public TNodo pesquisa(TNodo T, long chave) {
            if (T == null) {
                return T;
            } else {
                comparisons++;
                if (chave == T.chave)
                    return T;
                else
                    if (chave < T.chave)
                        T = pesquisa(T.esq, chave);
                    else
                        T = pesquisa(T.dir, chave);
            }
            return T;
        }
    }

    // ===================== AVL =====================

    static class TArvoreAVL {

        static class TNodo {
            TNodo esq;
            long chave;
            TNodo dir;
            TNodo pai;
            int bal = 0;
            int hesq = 0;
            int hdir = 0;

            TNodo(long chave, TNodo pai) {
                this.chave = chave;
                this.esq = null;
                this.dir = null;
                this.pai = pai;
            }
        }

        public TNodo T;
        private int h;
        private TNodo p;
        long comparisons = 0;

        public void insere(long chave) {
            T = insere(T, chave, null);
            AVL(p);
        }

        public TNodo insere(TNodo T, long chave, TNodo pai) {
            if (T == null) {
                T = new TNodo(chave, pai);
                this.p = T;
            } else {
                pai = T;
                comparisons++;
                if (chave < T.chave)
                    T.esq = insere(T.esq, chave, pai);
                else if (chave > T.chave)
                    T.dir = insere(T.dir, chave, pai);
            }
            return T;
        }

        public void AVL(TNodo T) {
            if (T != null) {
                T.bal = balanco(T);
                if (T.bal < 2) {
                    AVL(T.pai);
                } else {

                    if (T.hesq >= T.hdir)
                        if (T.esq.hesq >= T.esq.hdir) {
                            rotacao_direita(T);
                        }
                        else {
                            rotacao_esquerda(T.esq);
                            rotacao_direita(T);
                        }

                    if (T.hdir >= T.hesq)
                        if (T.dir.hdir >= T.dir.hesq) {
                            rotacao_esquerda(T);
                        }
                        else {
                            rotacao_direita(T.dir);
                            rotacao_esquerda(T);
                        }
                }
            }
        }

        public int balanco(TNodo T) {
            h = 0; balpreOrdem(T.esq, 0); T.hesq = h;
            h = 0; balpreOrdem(T.dir, 0); T.hdir = h;
            return Math.abs(T.hesq - T.hdir);
        }

        public void balpreOrdem(TNodo T, int v) {
            if (T != null) {
                v++;
                balpreOrdem(T.esq, v);
                balpreOrdem(T.dir, v);
            } else
                if (v > h) h = v;
        }

        public void rotacao_esquerda(TNodo T) {
            TNodo apu = T.dir;
            T.dir = apu.esq;
            if (apu.esq != null) apu.esq.pai = T;
            apu.pai = T.pai;
            apu.esq = T; T.pai = apu;
            T.bal = 0;
            if (apu.pai == null)
                this.T = apu;
            else {
                if (apu.chave < apu.pai.chave)
                    apu.pai.esq = apu;
                else
                    apu.pai.dir = apu;
            }
        }

        public void rotacao_direita(TNodo T) {
            TNodo apu = T.esq;
            T.esq = apu.dir;
            if (apu.dir != null) apu.dir.pai = T;
            apu.pai = T.pai;
            apu.dir = T; T.pai = apu;
            T.bal = 0;
            if (apu.pai == null)
                this.T = apu;
            else {
                if (apu.chave < apu.pai.chave)
                    apu.pai.esq = apu;
                else
                    apu.pai.dir = apu;
            }
        }

        public TNodo pesquisa(long chave) {
            return pesquisa(T, chave);
        }

        public TNodo pesquisa(TNodo T, long chave) {
            if (T == null) {
                return T;
            } else {
                comparisons++;
                if (chave == T.chave)
                    return T;
                else
                    if (chave < T.chave)
                        T = pesquisa(T.esq, chave);
                    else
                        T = pesquisa(T.dir, chave);
            }
            return T;
        }
    }

    // ===================== TEST SET =====================

    static List<Long> pickTestSet(List<Long> data, int size, Random r) {
        List<Long> copy = new ArrayList<>(data);
        Collections.shuffle(copy, r);
        return new ArrayList<>(copy.subList(0, Math.min(size, copy.size())));
    }

    // ===================== BENCHMARK =====================

    static Result benchmarkSequential(List<Long> data, List<Long> tests) {

        // aquecimento (não medido)
        int w = Math.min(WARMUP_SEARCHES, tests.size());
        for (int i = 0; i < w; i++) {
            long x = tests.get(i);
            for (long v : data) {
                if (v == x) break;
            }
        }

        long comps = 0;
        long total = 0;
        int repeats = 0;

        while (repeats == 0 || (total < MIN_MEASURE_NS && repeats < MAX_REPEATS)) {

            long s = System.nanoTime();

            for (long x : tests) {
                int comp = 0;
                for (long v : data) {
                    comp++;
                    if (v == x) break;
                }
                comps += comp;
            }

            total += System.nanoTime() - s;
            repeats++;
        }

        long searches = (long) repeats * tests.size();
        long timeRef = Math.round((double) total / searches * REFERENCE_SEARCHES);

        return new Result(timeRef, comps / searches);
    }

    static Result benchmarkBinary(List<Long> data, List<Long> tests) {

        // aquecimento (não medido)
        int w = Math.min(WARMUP_SEARCHES, tests.size());
        for (int i = 0; i < w; i++) {
            long x = tests.get(i);
            int l = 0, r = data.size() - 1;
            while (l <= r) {
                int m = (l + r) / 2;
                int cmp = Long.compare(data.get(m), x);
                if (cmp == 0) break;
                else if (cmp < 0) l = m + 1;
                else r = m - 1;
            }
        }

        long comps = 0;
        long total = 0;
        int repeats = 0;

        while (repeats == 0 || (total < MIN_MEASURE_NS && repeats < MAX_REPEATS)) {

            long s = System.nanoTime();

            for (long x : tests) {

                int l = 0, r = data.size() - 1;
                int comp = 0;

                while (l <= r) {
                    int m = (l + r) / 2;
                    comp++;

                    int cmp = Long.compare(data.get(m), x);

                    if (cmp == 0) break;
                    else if (cmp < 0) l = m + 1;
                    else r = m - 1;
                }

                comps += comp;
            }

            total += System.nanoTime() - s;
            repeats++;
        }

        long searches = (long) repeats * tests.size();
        long timeRef = Math.round((double) total / searches * REFERENCE_SEARCHES);

        return new Result(timeRef, comps / searches);
    }

    static Result benchmarkABB(TArvore t, List<Long> tests) {

        // aquecimento (não medido)
        int w = Math.min(WARMUP_SEARCHES, tests.size());
        for (int i = 0; i < w; i++) {
            t.pesquisa(tests.get(i));
        }

        t.comparisons = 0;
        long total = 0;
        int repeats = 0;

        while (repeats == 0 || (total < MIN_MEASURE_NS && repeats < MAX_REPEATS)) {

            long s = System.nanoTime();

            for (long x : tests) {
                t.pesquisa(x);
            }

            total += System.nanoTime() - s;
            repeats++;
        }

        long searches = (long) repeats * tests.size();
        long timeRef = Math.round((double) total / searches * REFERENCE_SEARCHES);

        return new Result(timeRef, t.comparisons / searches);
    }

    static Result benchmarkAVL(TArvoreAVL t, List<Long> tests) {

        // aquecimento (não medido)
        int w = Math.min(WARMUP_SEARCHES, tests.size());
        for (int i = 0; i < w; i++) {
            t.pesquisa(tests.get(i));
        }

        t.comparisons = 0;
        long total = 0;
        int repeats = 0;

        while (repeats == 0 || (total < MIN_MEASURE_NS && repeats < MAX_REPEATS)) {

            long s = System.nanoTime();

            for (long x : tests) {
                t.pesquisa(x);
            }

            total += System.nanoTime() - s;
            repeats++;
        }

        long searches = (long) repeats * tests.size();
        long timeRef = Math.round((double) total / searches * REFERENCE_SEARCHES);

        return new Result(timeRef, t.comparisons / searches);
    }

    // ===================== CSV =====================

    static class Result {
        long time;
        long comp;

        Result(long t, long c) {
            time = t;
            comp = c;
        }
    }

    static void init(String f) throws IOException {
        BufferedWriter bw = new BufferedWriter(
                new FileWriter(OUTPUT_DIR + "/" + f));
        bw.write("n,comparisons,time_ns\n");
        bw.newLine();
        writers.put(f, bw);
    }

    static void write(String f, int n, Result r) throws IOException {
        BufferedWriter bw = writers.get(f);
        bw.write(n + "," + r.comp + "," + r.time);
        bw.newLine();
    }

    static void writeFail(String f, int n) throws IOException {
        BufferedWriter bw = writers.get(f);
        bw.write(n + ",FAIL,FAIL");
        bw.newLine();
    }

    static void closeWriters() throws IOException {
        for (BufferedWriter bw : writers.values()) {
            bw.close();
        }
    }

    // ===================== LOG SERIAL =====================

    /**
     * Log serial simples: timestamp + mensagem, sempre em uma única linha,
     * para acompanhar em tempo real o que o benchmark está fazendo e em
     * que percentual da análise ele está.
     */
    static void log(String message) {
        System.out.println("[" + new Date() + "] " + message);
    }
}