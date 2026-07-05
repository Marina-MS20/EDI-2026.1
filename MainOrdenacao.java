import java.io.*;
import java.util.*;

/**
 * Benchmark de algoritmos de ordenação.
 *
 * Arquitetura (mesmo espírito do projeto de estruturas de busca anterior):
 *  1) Carregamento: lê o dataset bruto (mesmo CSV de origem) e mantém a
 *     lista base imutável.
 *  2) Geração de distribuições: a partir do slice dataset[0..n], gera as
 *     variantes pedidas (aleatório, crescente, decrescente, quase-crescente
 *     e quase-decrescente — estes dois últimos em duas versões: perturbação
 *     percentual e perturbação de contagem fixa), tudo de forma
 *     determinística por n (seed derivada de BASE_SEED + n).
 *  3) Algoritmos: QuickSort (pivô ingênuo = primeiro elemento, recursivo de
 *     verdade — pode estourar a pilha em entradas já ordenadas/quase
 *     ordenadas, e é isso que queremos observar), MergeSort (recursivo,
 *     profundidade O(log n), não deve estourar), HeapSort (iterativo),
 *     InsertionSort, SelectionSort e BubbleSort (todos O(n²), iterativos).
 *     Cada um só ordena e conta comparações/cópias — nenhuma lógica de
 *     experimento aqui.
 *  4) Experimento: roda todas as combinações algoritmo × distribuição
 *     (6 × 7 = 42) ao longo de uma sequência de n crescente, no modo
 *     escolhido (GROWTH_STEP ou FIXED_STEP). Quando uma combinação
 *     estoura, registra o ponto como FAIL no CSV, marca o failPoint e,
 *     depois do coarse inteiro, refina só aquela combinação com um fator
 *     de crescimento menor até estourar de novo (ou não).
 */
public class MainOrdenacao {

    // ===================== CONFIG GERAL =====================

    private static final String CSV_FILE = "solarradiation.csv"; // ajuste o caminho se necessário
    private static final String OUTPUT_DIR = "output_ordenacao";  // pasta NOVA, não reaproveita a do projeto anterior
    private static final String REPORT_FILE = OUTPUT_DIR + "/fail_report.txt";

    private static final long BASE_SEED = 42L;

    // perturbação para "quase crescente" / "quase decrescente"
    private static final double NEAR_PCT = 0.05; // 5% de trocas aleatórias

    enum Mode { FIXED_STEP, GROWTH_STEP }

    // modo ativo do experimento — troque aqui para alternar
    private static final Mode MODE = Mode.GROWTH_STEP;

    // ---- parâmetros do modo antigo (FIXED_STEP) ----
    private static final int FIXED_STEP = 5_000;
    private static final int FIXED_MAX_N = 500_000;
    private static final int FIXED_FINE_STEP = Math.max(FIXED_STEP / 10, 1000);

    // ---- parâmetros do modo novo (GROWTH_STEP), confirmados ----
    private static final int GROWTH_START_N = 10;
    private static final int GROWTH_MAX_N = 30_000;
    private static final double GROWTH_FACTOR = 1.15;
    private static final double GROWTH_FINE_FACTOR = 1.02;

    // ===================== ESTADO DO EXPERIMENTO =====================

    static Map<String, BufferedWriter> writers = new HashMap<>();
    static Set<String> activeCombos = new LinkedHashSet<>();
    static Map<String, Integer> failPoint = new HashMap<>();
    static Map<String, Integer> lastSuccess = new HashMap<>();
    static Map<String, Combo> combosByKey = new LinkedHashMap<>();

    public static void main(String[] args) throws Exception {

        new File(OUTPUT_DIR).mkdirs();

        log("Modo de experimento: " + MODE);
        log("Carregando dataset de '" + CSV_FILE + "'...");
        List<String> dataset = loadIds(CSV_FILE);
        log("Dataset carregado: " + dataset.size() + " registros.");

        Map<String, SortAlgorithm> algoritmos = buildAlgorithms();
        List<String> distribuicoes = List.of(
                "random", "ascending", "descending",
                "near_ascending_pct", "near_ascending_fixed",
                "near_descending_pct", "near_descending_fixed"
        );

        for (String alg : algoritmos.keySet()) {
            for (String dist : distribuicoes) {
                Combo combo = new Combo(alg, dist);
                combosByKey.put(combo.key, combo);
                activeCombos.add(combo.key);
                init(combo.key + ".csv");
            }
        }

        try (BufferedWriter report = new BufferedWriter(new FileWriter(REPORT_FILE))) {

            report.write("COMBO,PHASE,N,ERROR");
            report.newLine();

            // ===================== FASE COARSE =====================

            List<Integer> coarseSeq = buildCoarseSequence(dataset.size());
            log("Iniciando FASE COARSE — " + coarseSeq.size() + " pontos de n (de "
                    + coarseSeq.get(0) + " a " + coarseSeq.get(coarseSeq.size() - 1) + ")");

            for (int i = 0; i < coarseSeq.size(); i++) {

                int n = coarseSeq.get(i);
                double pct = ((i + 1) * 100.0) / coarseSeq.size();
                log(String.format("[COARSE %5.1f%%] processando n=%d", pct, n));

                Datasets d = gerarDistribuicoes(dataset, n);
                Map<String, List<String>> distMap = d.asMap();

                for (Combo combo : combosByKey.values()) {
                    if (!activeCombos.contains(combo.key)) continue;

                    List<String> base = distMap.get(combo.distribution);
                    SortAlgorithm algo = algoritmos.get(combo.algorithm);

                    safeRunSort(combo, n, base, algo, report, "COARSE");
                }
            }

            log(String.format("[COARSE 100.0%%] fase coarse concluída."));

            // ===================== FASE FINE =====================

            if (failPoint.isEmpty()) {
                log("Nenhuma combinação estourou na fase coarse — FASE FINE não será executada.");
            } else {
                log("Iniciando FASE FINE para: " + failPoint.keySet());
            }

            for (String comboKey : new ArrayList<>(failPoint.keySet())) {

                Combo combo = combosByKey.get(comboKey);
                int failN = failPoint.get(comboKey);
                int fromN = lastSuccess.getOrDefault(comboKey, 0);

                List<Integer> fineSeq = buildFineSequence(fromN, failN);

                log("[FINE] " + comboKey + ": refinando janela n=" + fromN + ".." + failN
                        + " (" + fineSeq.size() + " pontos)");

                SortAlgorithm algo = algoritmos.get(combo.algorithm);

                for (int i = 0; i < fineSeq.size(); i++) {

                    int n = fineSeq.get(i);
                    double pct = ((i + 1) * 100.0) / fineSeq.size();
                    log(String.format("[FINE %s %5.1f%%] processando n=%d", comboKey, pct, n));

                    Datasets d = gerarDistribuicoes(dataset, n);
                    List<String> base = d.asMap().get(combo.distribution);

                    boolean ok = safeRunSort(combo, n, base, algo, report, "FINE");

                    if (!ok) {
                        log("[FINE " + comboKey + "] ESTOUROU DE NOVO em n=" + n
                                + " — encerrando refinamento desta combinação.");
                        break;
                    }
                }
            }

            log("Fase fine concluída.");
        }

        closeWriters();
        log("Benchmark concluído. Resultados em '" + OUTPUT_DIR + "'.");
    }

    // ===================== COMBO (algoritmo x distribuição) =====================

    static class Combo {
        final String algorithm;
        final String distribution;
        final String key;

        Combo(String algorithm, String distribution) {
            this.algorithm = algorithm;
            this.distribution = distribution;
            this.key = algorithm + "_" + distribution;
        }
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
        int lastAdded = -1;

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

    // ===================== GERAÇÃO DE DISTRIBUIÇÕES =====================

    static class Datasets {
        List<String> random;
        List<String> ascending;
        List<String> descending;
        List<String> nearAscendingPct;
        List<String> nearAscendingFixed;
        List<String> nearDescendingPct;
        List<String> nearDescendingFixed;

        Map<String, List<String>> asMap() {
            Map<String, List<String>> m = new HashMap<>();
            m.put("random", random);
            m.put("ascending", ascending);
            m.put("descending", descending);
            m.put("near_ascending_pct", nearAscendingPct);
            m.put("near_ascending_fixed", nearAscendingFixed);
            m.put("near_descending_pct", nearDescendingPct);
            m.put("near_descending_fixed", nearDescendingFixed);
            return m;
        }
    }

    /**
     * Gera todas as distribuições para um dado n, de forma determinística:
     * toda seed usada é derivada de (BASE_SEED, n, offset fixo), nunca de um
     * Random compartilhado mutando entre chamadas. Assim, gerar os dados
     * para um n específico dá sempre o mesmo resultado, seja na fase coarse
     * ou na fase fine.
     */
    static Datasets gerarDistribuicoes(List<String> dataset, int n) {

        Datasets d = new Datasets();

        List<String> base = new ArrayList<>(dataset.subList(0, n));

        d.ascending = new ArrayList<>(base);
        Collections.sort(d.ascending);

        d.descending = new ArrayList<>(d.ascending);
        Collections.reverse(d.descending);

        d.random = new ArrayList<>(base);
        Collections.shuffle(d.random, new Random(BASE_SEED + n));

        int pctSwaps = Math.max(1, (int) Math.round(n * NEAR_PCT));
        int fixedSwaps = Math.max(1, (int) Math.round(Math.sqrt(n)));

        d.nearAscendingPct = perturb(d.ascending, pctSwaps, new Random(BASE_SEED + n + 1));
        d.nearAscendingFixed = perturb(d.ascending, fixedSwaps, new Random(BASE_SEED + n + 2));

        d.nearDescendingPct = perturb(d.descending, pctSwaps, new Random(BASE_SEED + n + 3));
        d.nearDescendingFixed = perturb(d.descending, fixedSwaps, new Random(BASE_SEED + n + 4));

        return d;
    }

    static List<String> perturb(List<String> sortedBase, int swaps, Random r) {
        List<String> copy = new ArrayList<>(sortedBase);
        int size = copy.size();

        if (size < 2) return copy;

        for (int i = 0; i < swaps; i++) {
            int a = r.nextInt(size);
            int b = r.nextInt(size);
            Collections.swap(copy, a, b);
        }

        return copy;
    }

    // ===================== SAFE RUN =====================

    static boolean safeRunSort(Combo combo, int n, List<String> data,
                                SortAlgorithm algo, BufferedWriter report,
                                String phase) throws IOException {

        String file = combo.key + ".csv";

        try {
            String[] arr = data.toArray(new String[0]);
            Counters c = new Counters();

            long start = System.nanoTime();
            algo.sort(arr, c);
            long end = System.nanoTime();

            write(file, n, c.comparisons, c.copies, end - start);

            if (phase.equals("COARSE")) lastSuccess.put(combo.key, n);

            return true;

        } catch (Throwable e) {

            if (phase.equals("COARSE")) {
                failPoint.put(combo.key, n);
                activeCombos.remove(combo.key);
            }

            writeFail(file, n);

            report.write(combo.key + "," + phase + "," + n + "," + e.getClass().getSimpleName());
            report.newLine();

            return false;
        }
    }

    // ===================== ALGORITMOS DE ORDENAÇÃO =====================
    //
    // Cada algoritmo só ordena e conta comparações/cópias — nenhuma lógica
    // de experimento, falha ou fase entra aqui. O QuickSort usa pivô
    // ingênuo (primeiro elemento) e é recursivo de verdade: em entradas já
    // ordenadas ou quase ordenadas ele particiona de forma desbalanceada e
    // a profundidade de recursão vira O(n) — para n grande o suficiente,
    // isso estoura a pilha (StackOverflowError) de fato. É exatamente esse
    // estouro que a camada de experimento (safeRunSort) captura e registra.
    // MergeSort também é recursivo, mas sua divisão é sempre balanceada
    // (profundidade O(log n)), então não deve estourar nas faixas de n
    // usadas aqui.

    interface SortAlgorithm {
        void sort(String[] arr, Counters c);
    }

    static class Counters {
        long comparisons = 0;
        long copies = 0;
    }

    static Map<String, SortAlgorithm> buildAlgorithms() {
        Map<String, SortAlgorithm> m = new LinkedHashMap<>();
        m.put("quicksort", (arr, c) -> quickSort(arr, 0, arr.length - 1, c));
        m.put("mergesort", (arr, c) -> mergeSort(arr, 0, arr.length - 1, c));
        m.put("heapsort", MainOrdenacao::heapSort);
        m.put("insertionsort", MainOrdenacao::insertionSort);
        m.put("selectionsort", MainOrdenacao::selectionSort);
        m.put("bubblesort", MainOrdenacao::bubbleSort);
        return m;
    }

    static void swap(String[] arr, int i, int j, Counters c) {
        String tmp = arr[i];
        arr[i] = arr[j];
        c.copies++;
        arr[j] = tmp;
        c.copies++;
    }

    // ---- BubbleSort: O(n²), apenas para fins comparativos ----
    static void bubbleSort(String[] arr, Counters c) {
        int n = arr.length;
        for (int i = 0; i < n - 1; i++) {
            for (int j = 0; j < n - 1 - i; j++) {
                c.comparisons++;
                if (arr[j].compareTo(arr[j + 1]) > 0) {
                    swap(arr, j, j + 1, c);
                }
            }
        }
    }

    // ---- SelectionSort: O(n²) ----
    static void selectionSort(String[] arr, Counters c) {
        int n = arr.length;
        for (int i = 0; i < n - 1; i++) {
            int min = i;
            for (int j = i + 1; j < n; j++) {
                c.comparisons++;
                if (arr[j].compareTo(arr[min]) < 0) min = j;
            }
            if (min != i) swap(arr, i, min, c);
        }
    }

    // ---- InsertionSort: O(n²) no pior caso ----
    static void insertionSort(String[] arr, Counters c) {
        int n = arr.length;
        for (int i = 1; i < n; i++) {
            String key = arr[i];
            int j = i - 1;

            while (j >= 0) {
                c.comparisons++;
                if (arr[j].compareTo(key) > 0) {
                    arr[j + 1] = arr[j];
                    c.copies++;
                    j--;
                } else {
                    break;
                }
            }

            arr[j + 1] = key;
            c.copies++;
        }
    }

    // ---- HeapSort: O(n log n), iterativo (sift-down recursivo é O(log n), seguro) ----
    static void heapSort(String[] arr, Counters c) {
        int n = arr.length;

        for (int i = n / 2 - 1; i >= 0; i--) {
            siftDown(arr, n, i, c);
        }

        for (int end = n - 1; end > 0; end--) {
            swap(arr, 0, end, c);
            siftDown(arr, end, 0, c);
        }
    }

    static void siftDown(String[] arr, int size, int root, Counters c) {
        int largest = root;
        int left = 2 * root + 1;
        int right = 2 * root + 2;

        if (left < size) {
            c.comparisons++;
            if (arr[left].compareTo(arr[largest]) > 0) largest = left;
        }
        if (right < size) {
            c.comparisons++;
            if (arr[right].compareTo(arr[largest]) > 0) largest = right;
        }

        if (largest != root) {
            swap(arr, root, largest, c);
            siftDown(arr, size, largest, c);
        }
    }

    // ---- MergeSort: O(n log n), recursivo, profundidade O(log n) ----
    static void mergeSort(String[] arr, int lo, int hi, Counters c) {
        if (lo >= hi) return;

        int mid = (lo + hi) / 2;
        mergeSort(arr, lo, mid, c);
        mergeSort(arr, mid + 1, hi, c);
        merge(arr, lo, mid, hi, c);
    }

    static void merge(String[] arr, int lo, int mid, int hi, Counters c) {
        String[] left = Arrays.copyOfRange(arr, lo, mid + 1);
        String[] right = Arrays.copyOfRange(arr, mid + 1, hi + 1);

        int i = 0, j = 0, k = lo;

        while (i < left.length && j < right.length) {
            c.comparisons++;
            if (left[i].compareTo(right[j]) <= 0) {
                arr[k++] = left[i++];
            } else {
                arr[k++] = right[j++];
            }
            c.copies++;
        }

        while (i < left.length) {
            arr[k++] = left[i++];
            c.copies++;
        }
        while (j < right.length) {
            arr[k++] = right[j++];
            c.copies++;
        }
    }

    // ---- QuickSort: O(n log n) caso médio, pivô ingênuo (primeiro elemento) ----
    // Recursivo de verdade: em entradas já ordenadas/quase ordenadas, o
    // particionamento é desbalanceado e a profundidade de recursão cresce
    // linearmente com n — é essa a exposição de pior caso que se quer medir.
    static void quickSort(String[] arr, int lo, int hi, Counters c) {
        if (lo >= hi) return;

        int p = partition(arr, lo, hi, c);

        quickSort(arr, lo, p - 1, c);
        quickSort(arr, p + 1, hi, c);
    }

    static int partition(String[] arr, int lo, int hi, Counters c) {
        String pivot = arr[lo]; // pivô ingênuo: primeiro elemento

        int i = lo + 1;
        int j = hi;

        while (true) {
            while (i <= hi) {
                c.comparisons++;
                if (arr[i].compareTo(pivot) > 0) break;
                i++;
            }
            while (j > lo) {
                c.comparisons++;
                if (arr[j].compareTo(pivot) < 0) break;
                j--;
            }
            if (i >= j) break;
            swap(arr, i, j, c);
        }

        swap(arr, lo, j, c);
        return j;
    }

    // ===================== LOAD =====================

    static List<String> loadIds(String file) throws IOException {

        List<String> ids = new ArrayList<>();

        try (BufferedReader br = new BufferedReader(new FileReader(file))) {
            br.readLine(); // cabeçalho

            String line;
            while ((line = br.readLine()) != null) {
                String[] v = line.split(",", -1);
                if (v.length > 0) ids.add(v[0]);
            }
        }

        return ids;
    }

    // ===================== CSV =====================

    static void init(String f) throws IOException {
        BufferedWriter bw = new BufferedWriter(new FileWriter(OUTPUT_DIR + "/" + f));
        bw.write("n,comparisons,copies,time_ns");
        bw.newLine();
        writers.put(f, bw);
    }

    static void write(String f, int n, long comparisons, long copies, long timeNs) throws IOException {
        BufferedWriter bw = writers.get(f);
        bw.write(n + "," + comparisons + "," + copies + "," + timeNs);
        bw.newLine();
    }

    static void writeFail(String f, int n) throws IOException {
        BufferedWriter bw = writers.get(f);
        bw.write(n + ",FAIL,FAIL,FAIL");
        bw.newLine();
    }

    static void closeWriters() throws IOException {
        for (BufferedWriter bw : writers.values()) {
            bw.close();
        }
    }

    // ===================== LOG SERIAL =====================

    static void log(String message) {
        System.out.println("[" + new Date() + "] " + message);
    }
}