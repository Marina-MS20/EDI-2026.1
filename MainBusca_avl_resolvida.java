import java.io.*;
import java.util.*;

public class MainBusca_avl_resolvida {

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
    private static final int FIXED_MAX_N = 2_000_000;
    private static final int FIXED_FINE_STEP = Math.max(FIXED_STEP / 10, 1000);

    // ---- parâmetros do modo novo (GROWTH_STEP): incremento multiplicativo ----
    // GROWTH_MAX_N reaproveita o mesmo teto do modo fixo (200.000) para
    // explorar a mesma faixa; ajuste se quiser outro teto.
    private static final int GROWTH_START_N = 10;
    private static final int GROWTH_MAX_N = FIXED_MAX_N;
    private static final double GROWTH_FACTOR = 1.10;
    private static final double GROWTH_FINE_FACTOR = 1.02;

    static Map<String, BufferedWriter> writers = new HashMap<>();

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

        init("avl_random.csv");
        init("avl_sorted.csv");
        init("avl_reverse.csv");

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

                if (activeAVL.contains("avl_random"))
                    safeRunAVL("avl_random.csv", "avl_random", n, v.random, v.testSet, report);

                if (activeAVL.contains("avl_sorted"))
                    safeRunAVL("avl_sorted.csv", "avl_sorted", n, v.sorted, v.testSet, report);

                if (activeAVL.contains("avl_reverse"))
                    safeRunAVL("avl_reverse.csv", "avl_reverse", n, v.reverse, v.testSet, report);
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

                    boolean estourouDeNovo =
                            !safeRunAVL(structure + ".csv", structure, n, data, v.testSet, report, "FINE");

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

    // ===================== ESTRUTURA =====================
    //
    // TArvoreAVL: AVL clássica por apontadores esq/dir, sem apontador para
    // o pai. A inserção é recursiva e devolve a nova raiz de cada subárvore
    // ("T.esq = insere(T.esq, chave)"), o que já religa a árvore ao subir
    // da recursão — dispensa o apontador de pai que a versão anterior usava
    // para caminhar de volta até a raiz e refazer o balanceamento. Cada nó
    // guarda sua própria altura; ao voltar de cada chamada recursiva ela é
    // recalculada em O(1) a partir da altura, já atualizada, dos dois
    // filhos — nunca por travessia da subárvore inteira (que era o defeito
    // da versão anterior: balanco() percorria a subárvore inteira a cada
    // inserção, tornando a construção O(n²)).
    //
    // Por ser uma AVL de verdade, a altura da árvore é sempre O(log n),
    // qualquer que seja a ordem de inserção (aleatória, ordenada ou
    // invertida): diferente de uma ABB sem balanceamento, ela nunca
    // degenera numa lista ligada. Isso também garante que a profundidade de
    // recursão de insere/pesquisa é O(log n), então não há mais risco de
    // StackOverflowError por entrada ordenada — o try/catch em safeRunAVL
    // continua como rede de segurança genérica (ex.: memória insuficiente
    // para n muito grande), mas deixou de ser necessário por causa de
    // desbalanceamento, e por isso o teto extra que a AVL tinha (o antigo
    // AVL_MAX_N) foi removido: ela agora percorre a mesma faixa de n que as
    // demais estruturas.

    static class TArvoreAVL {

        static class TNodo {
            TNodo esq;
            long chave;
            TNodo dir;
            int altura; // altura do nó: folha = 1, filho inexistente (null) = 0

            TNodo(long chave) {
                this.chave = chave;
                this.esq = null;
                this.dir = null;
                this.altura = 1;
            }
        }

        public TNodo T;
        long comparisons = 0;

        // ---- altura e fator de balanceamento em O(1) ----
        // Nunca por travessia: sempre lidos direto do campo 'altura' de
        // cada nó, que insere() mantém correto em toda chamada.

        private static int altura(TNodo t) {
            return t == null ? 0 : t.altura;
        }

        private static void atualizaAltura(TNodo t) {
            t.altura = 1 + Math.max(altura(t.esq), altura(t.dir));
        }

        private static int fatorBalanceamento(TNodo t) {
            return t == null ? 0 : altura(t.esq) - altura(t.dir);
        }

        // ---- rotações ----
        //
        // Em cada rotação, a altura do nó que desce é recalculada ANTES da
        // altura do nó que sobe, porque a altura de quem sobe depende da
        // altura já correta de quem desceu.

        private static TNodo rotacaoDireita(TNodo y) {
            TNodo x = y.esq;
            TNodo T2 = x.dir;

            x.dir = y;
            y.esq = T2;

            atualizaAltura(y);
            atualizaAltura(x);

            return x; // nova raiz da subárvore
        }

        private static TNodo rotacaoEsquerda(TNodo x) {
            TNodo y = x.dir;
            TNodo T2 = y.esq;

            y.esq = x;
            x.dir = T2;

            atualizaAltura(x);
            atualizaAltura(y);

            return y; // nova raiz da subárvore
        }

        // ---- inserção ----
        //
        // Recursiva no estilo clássico: cada chamada devolve a raiz
        // (possivelmente nova) da subárvore em que foi chamada, e quem
        // chamou religa o ponteiro ("t.esq = insere(t.esq, chave)"). Ao
        // voltar de cada nível da recursão, a altura do nó é recalculada e
        // o fator de balanceamento é conferido; se ultrapassar +-1, aplica-
        // se a rotação simples (LL/RR) ou dupla (LR/RL) apropriada — a
        // escolha é feita pelo sinal do fator de balanceamento do filho, o
        // critério padrão de livro-texto (não depende de comparar a chave
        // recém-inserida).
        public void insere(long chave) {
            T = insere(T, chave);
        }

        private TNodo insere(TNodo t, long chave) {
            if (t == null) {
                return new TNodo(chave);
            }

            comparisons++;
            if (chave < t.chave) {
                t.esq = insere(t.esq, chave);
            } else if (chave > t.chave) {
                t.dir = insere(t.dir, chave);
            } else {
                return t; // chave já existe: não reinsere, árvore não muda
            }

            atualizaAltura(t);

            int fb = fatorBalanceamento(t);

            if (fb > 1) {
                if (fatorBalanceamento(t.esq) < 0)
                    t.esq = rotacaoEsquerda(t.esq); // caso LR: reduz a LL
                return rotacaoDireita(t);           // caso LL
            }

            if (fb < -1) {
                if (fatorBalanceamento(t.dir) > 0)
                    t.dir = rotacaoDireita(t.dir);  // caso RL: reduz a RR
                return rotacaoEsquerda(t);          // caso RR
            }

            return t;
        }

        // ---- busca ----
        //
        // A altura O(log n) garantida pela AVL faz da busca uma descida de
        // no máximo O(log n) comparações no pior caso.
        public TNodo pesquisa(long chave) {
            return pesquisa(T, chave);
        }

        private TNodo pesquisa(TNodo t, long chave) {
            if (t == null) {
                return null;
            }

            comparisons++;
            if (chave == t.chave)
                return t;
            else if (chave < t.chave)
                return pesquisa(t.esq, chave);
            else
                return pesquisa(t.dir, chave);
        }
    }

    // ===================== TEST SET =====================

    static List<Long> pickTestSet(List<Long> data, int size, Random r) {
        List<Long> copy = new ArrayList<>(data);
        Collections.shuffle(copy, r);
        return new ArrayList<>(copy.subList(0, Math.min(size, copy.size())));
    }

    // ===================== BENCHMARK =====================

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