import java.io.*;
import java.util.*;

public class MainBusca {

    private static final String CSV_FILE = "solarradiation.csv";
    private static final int TEST_SIZE = 2000;

    // seed fixa e usada de forma determinística por n (ver gerarVariantes)
    private static final long BASE_SEED = 42L;

    private static final String OUTPUT_DIR = "output";
    private static final String REPORT_FILE = OUTPUT_DIR + "/fail_report.txt";

    enum Mode { FIXED_STEP, GROWTH_STEP }

    // modo ativo do experimento — troque aqui para alternar
    private static final Mode MODE = Mode.GROWTH_STEP;

    // ---- parâmetros do modo antigo (FIXED_STEP): incremento aditivo fixo ----
    private static final int FIXED_STEP = 10_000;
    private static final int FIXED_MAX_N = 7_000_000;
    private static final int FIXED_FINE_STEP = Math.max(FIXED_STEP / 10, 1000);

    // ---- parâmetros do modo novo (GROWTH_STEP): incremento multiplicativo ----
    // GROWTH_MAX_N reaproveita o mesmo teto do modo fixo (7.000.000) para
    // explorar a mesma faixa; ajuste se quiser outro teto.
    private static final int GROWTH_START_N = 10;
    private static final int GROWTH_MAX_N = FIXED_MAX_N;
    private static final double GROWTH_FACTOR = 1.15;
    private static final double GROWTH_FINE_FACTOR = 1.02;

    static Map<String, BufferedWriter> writers = new HashMap<>();

    static Set<String> activeBST = new HashSet<>();
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

        init("seq.csv");
        init("bin.csv");

        init("bst_random.csv");
        init("bst_sorted.csv");
        init("bst_reverse.csv");

        init("avl_random.csv");
        init("avl_sorted.csv");
        init("avl_reverse.csv");

        activeBST.add("bst_random");
        activeBST.add("bst_sorted");
        activeBST.add("bst_reverse");

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

                write("seq.csv", n, benchmarkSequential(v.base, v.testSet));
                write("bin.csv", n, benchmarkBinary(v.sorted, v.testSet));

                if (activeBST.contains("bst_random"))
                    safeRunBST("bst_random.csv", "bst_random", n, v.random, v.testSet, report);

                if (activeBST.contains("bst_sorted"))
                    safeRunBST("bst_sorted.csv", "bst_sorted", n, v.sorted, v.testSet, report);

                if (activeBST.contains("bst_reverse"))
                    safeRunBST("bst_reverse.csv", "bst_reverse", n, v.reverse, v.testSet, report);

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

                    boolean estourouDeNovo;

                    if (structure.startsWith("bst")) {
                        estourouDeNovo = !safeRunBST(structure + ".csv", structure, n, data, v.testSet, report, "FINE");
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

        Random testRandom = new Random(BASE_SEED + n);
        v.testSet = pickTestSet(v.base, testSize, testRandom);

        return v;
    }

    // ===================== SAFE RUN =====================

    static boolean safeRunBST(String file, String name, int n,
                               List<Long> data, List<Long> tests,
                               BufferedWriter report) throws IOException {
        return safeRunBST(file, name, n, data, tests, report, "COARSE");
    }

    static boolean safeRunBST(String file, String name, int n,
                               List<Long> data, List<Long> tests,
                               BufferedWriter report, String phase) throws IOException {

        try {
            BST t = buildBST(data);
            Result r = benchmarkBST(t, tests);
            write(file, n, r);

            if (phase.equals("COARSE")) lastSuccess.put(name, n);

            return true;

        } catch (Throwable e) {

            if (phase.equals("COARSE")) {
                failPoint.put(name, n);
                activeBST.remove(name);
            }

            writeFail(file, n);

            report.write("BST," + phase + "," + n + "," + e.getClass().getSimpleName());
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
            AVL t = buildAVL(data);
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

    static AVL buildAVL(List<Long> data) {
        AVL t = new AVL();
        for (long s : data) {
            t.insert(s);
        }
        return t;
    }

    static BST buildBST(List<Long> data) {
        BST t = new BST();
        for (long s : data) {
            t.insert(s);
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
    // BST e AVL usam o método de inserção REAL (recursivo). É proposital:
    // numa entrada ordenada ou em ordem inversa, a BST sem balanceamento
    // degenera numa lista ligada com profundidade O(n), e a inserção
    // recursiva consome uma frame de pilha por nível — para n grande o
    // suficiente, isso estoura a pilha (StackOverflowError) de verdade.
    // É exatamente esse estouro que a camada de experimento (safeRunBST/AVL)
    // captura, registra como failPoint e depois refina na fase fine.

    static class Node {
        long key;
        Node left, right;

        Node(long k) { key = k; }
    }

    static class BST {
        Node root;
        long comparisons = 0;

        void insert(long key) {
            root = insert(root, key);
        }

        Node insert(Node n, long key) {
            if (n == null) return new Node(key);

            comparisons++;

            if (key < n.key)
                n.left = insert(n.left, key);
            else
                n.right = insert(n.right, key);

            return n;
        }

        boolean search(long key) {
            Node c = root;

            while (c != null) {
                comparisons++;

                int cmp = Long.compare(key, c.key);

                if (cmp == 0) return true;
                else if (cmp < 0) c = c.left;
                else c = c.right;
            }

            return false;
        }
    }

    // ===================== AVL REAL =====================

    static class AVL {
        AVLNode root;
        long comparisons = 0;

        static class AVLNode {
            long key;
            int h;
            AVLNode l, r;

            AVLNode(long k) {
                key = k;
                h = 1;
            }
        }

        int h(AVLNode n) {
            return n == null ? 0 : n.h;
        }

        int balance(AVLNode n) {
            return n == null ? 0 : h(n.l) - h(n.r);
        }

        AVLNode rotateRight(AVLNode y) {
            AVLNode x = y.l;
            AVLNode t = x.r;

            x.r = y;
            y.l = t;

            y.h = Math.max(h(y.l), h(y.r)) + 1;
            x.h = Math.max(h(x.l), h(x.r)) + 1;

            return x;
        }

        AVLNode rotateLeft(AVLNode x) {
            AVLNode y = x.r;
            AVLNode t = y.l;

            y.l = x;
            x.r = t;

            x.h = Math.max(h(x.l), h(x.r)) + 1;
            y.h = Math.max(h(y.l), h(y.r)) + 1;

            return y;
        }

        void insert(long key) {
            root = insert(root, key);
        }

        AVLNode insert(AVLNode n, long key) {
            if (n == null) return new AVLNode(key);

            comparisons++;

            if (key < n.key)
                n.l = insert(n.l, key);
            else
                n.r = insert(n.r, key);

            n.h = Math.max(h(n.l), h(n.r)) + 1;

            int b = balance(n);

            if (b > 1 && key < n.l.key)
                return rotateRight(n);

            if (b < -1 && key > n.r.key)
                return rotateLeft(n);

            if (b > 1 && key > n.l.key) {
                n.l = rotateLeft(n.l);
                return rotateRight(n);
            }

            if (b < -1 && key < n.r.key) {
                n.r = rotateRight(n.r);
                return rotateLeft(n);
            }

            return n;
        }

        boolean search(long key) {
            AVLNode c = root;

            while (c != null) {
                comparisons++;

                int cmp = Long.compare(key, c.key);

                if (cmp == 0) return true;
                else if (cmp < 0) c = c.l;
                else c = c.r;
            }

            return false;
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

        long t = 0, c = 0;

        for (long x : tests) {
            long s = System.nanoTime();

            int comp = 0;
            for (long v : data) {
                comp++;
                if (v == x) break;
            }

            long e = System.nanoTime();

            t += (e - s);
            c += comp;
        }

        return new Result(t / tests.size(), c / tests.size());
    }

    static Result benchmarkBinary(List<Long> data, List<Long> tests) {

        long t = 0, c = 0;

        for (long x : tests) {

            long s = System.nanoTime();

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

            long e = System.nanoTime();

            t += (e - s);
            c += comp;
        }

        return new Result(t / tests.size(), c / tests.size());
    }

    static Result benchmarkBST(BST t, List<Long> tests) {

        long time = 0, comp = 0;

        for (long x : tests) {

            t.comparisons = 0;

            long s = System.nanoTime();
            t.search(x);
            long e = System.nanoTime();

            time += (e - s);
            comp += t.comparisons;
        }

        return new Result(time / tests.size(), comp / tests.size());
    }

    static Result benchmarkAVL(AVL t, List<Long> tests) {

        long time = 0, comp = 0;

        for (long x : tests) {

            t.comparisons = 0;

            long s = System.nanoTime();
            t.search(x);
            long e = System.nanoTime();

            time += (e - s);
            comp += t.comparisons;
        }

        return new Result(time / tests.size(), comp / tests.size());
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