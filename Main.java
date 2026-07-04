import java.io.*;
import java.util.*;

public class Main {

    private static final String CSV_FILE = "solarradiation.csv";
    private static final int STEP = 5_000;
    private static final int MAX_N = 500_000; // 7_000_000
    private static final int TEST_SIZE = 1000;

    // seed fixa e usada de forma determinística por n (ver gerarVariantes)
    private static final long BASE_SEED = 42L;

    private static final String OUTPUT_DIR = "output";
    private static final String REPORT_FILE = OUTPUT_DIR + "/fail_report.txt";

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

        log("Carregando dataset de '" + CSV_FILE + "'...");
        List<String> dataset = loadIds(CSV_FILE);
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

            int coarseLimit = Math.min(MAX_N, dataset.size());
            log("Iniciando FASE COARSE (step=" + STEP + ", limite n=" + coarseLimit + ")");

            for (int n = STEP; n <= coarseLimit; n += STEP) {

                double pct = (n * 100.0) / coarseLimit;
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

            log(String.format("[COARSE 100.0%%] fase coarse concluída (n=%d)", coarseLimit));

            // ===================== FASE FINE =====================
            //
            // Para cada estrutura que estourou na fase coarse, refaz a busca
            // exatamente com o mesmo pipeline de geração de dados (mesmo
            // slice, mesmo sort, mesmo shuffle com seed derivada de n),
            // porém em incrementos menores, partindo do último n que ainda
            // funcionou até o n onde a falha ocorreu — e para assim que
            // estourar de novo (não continua além disso).

            int fineStep = Math.max(STEP / 10, 1000);

            if (failPoint.isEmpty()) {
                log("Nenhuma estrutura estourou na fase coarse — FASE FINE não será executada.");
            } else {
                log("Iniciando FASE FINE (step=" + fineStep + ") para: " + failPoint.keySet());
            }

            for (String structure : new ArrayList<>(failPoint.keySet())) {

                int coarseFailN = failPoint.get(structure);
                int from = lastSuccess.getOrDefault(structure, 0) + fineStep;
                int totalSpan = Math.max(coarseFailN - from + fineStep, fineStep);

                log("[FINE] " + structure + ": refinando janela n=" + from + ".." + coarseFailN);

                for (int n = from; n <= coarseFailN; n += fineStep) {

                    double pct = ((n - from + fineStep) * 100.0) / totalSpan;
                    log(String.format("[FINE %s %5.1f%%] processando n=%d", structure, pct, n));

                    Variants v = gerarVariantes(dataset, n, TEST_SIZE);

                    List<String> data = structure.endsWith("random") ? v.random
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

    // ===================== GERAÇÃO DETERMINÍSTICA DE DADOS =====================

    static class Variants {
        List<String> base;
        List<String> sorted;
        List<String> reverse;
        List<String> random;
        List<String> testSet;
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
    static Variants gerarVariantes(List<String> dataset, int n, int testSize) {

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
                               List<String> data, List<String> tests,
                               BufferedWriter report) throws IOException {
        return safeRunBST(file, name, n, data, tests, report, "COARSE");
    }

    static boolean safeRunBST(String file, String name, int n,
                               List<String> data, List<String> tests,
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
                               List<String> data, List<String> tests,
                               BufferedWriter report) throws IOException {
        return safeRunAVL(file, name, n, data, tests, report, "COARSE");
    }

    static boolean safeRunAVL(String file, String name, int n,
                               List<String> data, List<String> tests,
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

    static AVL buildAVL(List<String> data) {
        AVL t = new AVL();
        for (String s : data) {
            t.insert(s);
        }
        return t;
    }

    static BST buildBST(List<String> data) {
        BST t = new BST();
        for (String s : data) {
            t.insert(s);
        }
        return t;
    }

    // ===================== LOAD =====================

    static List<String> loadIds(String file) throws IOException {

        List<String> ids = new ArrayList<>();

        try (BufferedReader br = new BufferedReader(new FileReader(file))) {
            br.readLine();

            String line;
            while ((line = br.readLine()) != null) {
                String[] v = line.split(",", -1);
                if (v.length > 0) ids.add(v[0]);
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
        String key;
        Node left, right;

        Node(String k) { key = k; }
    }

    static class BST {
        Node root;
        long comparisons = 0;

        void insert(String key) {
            root = insert(root, key);
        }

        Node insert(Node n, String key) {
            if (n == null) return new Node(key);

            comparisons++;

            if (key.compareTo(n.key) < 0)
                n.left = insert(n.left, key);
            else
                n.right = insert(n.right, key);

            return n;
        }

        boolean search(String key) {
            Node c = root;

            while (c != null) {
                comparisons++;

                int cmp = key.compareTo(c.key);

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
            String key;
            int h;
            AVLNode l, r;

            AVLNode(String k) {
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

        void insert(String key) {
            root = insert(root, key);
        }

        AVLNode insert(AVLNode n, String key) {
            if (n == null) return new AVLNode(key);

            comparisons++;

            if (key.compareTo(n.key) < 0)
                n.l = insert(n.l, key);
            else
                n.r = insert(n.r, key);

            n.h = Math.max(h(n.l), h(n.r)) + 1;

            int b = balance(n);

            if (b > 1 && key.compareTo(n.l.key) < 0)
                return rotateRight(n);

            if (b < -1 && key.compareTo(n.r.key) > 0)
                return rotateLeft(n);

            if (b > 1 && key.compareTo(n.l.key) > 0) {
                n.l = rotateLeft(n.l);
                return rotateRight(n);
            }

            if (b < -1 && key.compareTo(n.r.key) < 0) {
                n.r = rotateRight(n.r);
                return rotateLeft(n);
            }

            return n;
        }

        boolean search(String key) {
            AVLNode c = root;

            while (c != null) {
                comparisons++;

                int cmp = key.compareTo(c.key);

                if (cmp == 0) return true;
                else if (cmp < 0) c = c.l;
                else c = c.r;
            }

            return false;
        }
    }

    // ===================== TEST SET =====================

    static List<String> pickTestSet(List<String> data, int size, Random r) {
        List<String> copy = new ArrayList<>(data);
        Collections.shuffle(copy, r);
        return new ArrayList<>(copy.subList(0, Math.min(size, copy.size())));
    }

    // ===================== BENCHMARK =====================

    static Result benchmarkSequential(List<String> data, List<String> tests) {

        long t = 0, c = 0;

        for (String x : tests) {
            long s = System.nanoTime();

            int comp = 0;
            for (String v : data) {
                comp++;
                if (v.equals(x)) break;
            }

            long e = System.nanoTime();

            t += (e - s);
            c += comp;
        }

        return new Result(t / tests.size(), c / tests.size());
    }

    static Result benchmarkBinary(List<String> data, List<String> tests) {

        long t = 0, c = 0;

        for (String x : tests) {

            long s = System.nanoTime();

            int l = 0, r = data.size() - 1;
            int comp = 0;

            while (l <= r) {
                int m = (l + r) / 2;
                comp++;

                int cmp = data.get(m).compareTo(x);

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

    static Result benchmarkBST(BST t, List<String> tests) {

        long time = 0, comp = 0;

        for (String x : tests) {

            t.comparisons = 0;

            long s = System.nanoTime();
            t.search(x);
            long e = System.nanoTime();

            time += (e - s);
            comp += t.comparisons;
        }

        return new Result(time / tests.size(), comp / tests.size());
    }

    static Result benchmarkAVL(AVL t, List<String> tests) {

        long time = 0, comp = 0;

        for (String x : tests) {

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