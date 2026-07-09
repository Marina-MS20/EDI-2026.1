import java.io.*;
import java.util.*;

// benchmark dos algoritmos de ordenação - EDI 2026.1
public class MainOrdenacao {

    private static final String CSV_FILE = "solarradiation.csv";
    private static final String OUTPUT_DIR = "output_ordenacao";
    private static final String REPORT_FILE = OUTPUT_DIR + "/fail_report.txt";

    private static final long BASE_SEED = 42L;

    private static final double NEAR_PCT = 0.3; // % de trocas pra simular "quase ordenado"

    enum Mode { FIXED_STEP, GROWTH_STEP }

    private static final Mode MODE = Mode.GROWTH_STEP; // mude aqui pra trocar o modo

    // parâmetros FIXED_STEP
    private static final int FIXED_STEP = 5_000;
    private static final int FIXED_MAX_N = 7_000_000;
    private static final int FIXED_FINE_STEP = Math.max(FIXED_STEP / 10, 1000);

    // parâmetros GROWTH_STEP
    private static final int GROWTH_START_N = 10;
    private static final int GROWTH_MAX_N = 500_000;
    private static final double GROWTH_FACTOR = 1.10;
    private static final double GROWTH_FINE_FACTOR = 1.02;

    static Map<String, BufferedWriter> writers = new HashMap<>();
    static Set<String> activeCombos = new LinkedHashSet<>();
    static Map<String, Integer> failPoint = new HashMap<>();
    static Map<String, Integer> lastSuccess = new HashMap<>();
    static Map<String, Combo> combosByKey = new LinkedHashMap<>();

    public static void main(String[] args) throws Exception {

        new File(OUTPUT_DIR).mkdirs();

        log("Modo de experimento: " + MODE);
        log("Carregando dataset de '" + CSV_FILE + "'...");
        List<Long> dataset = loadIds(CSV_FILE);
        log("Dataset carregado: " + dataset.size() + " registros.");

        Map<String, SortAlgorithm> algoritmos = buildAlgorithms();
        List<String> distribuicoes = List.of(
                "random", "ascending", "descending",
                "near_ascending_pct", "near_descending_pct"
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

            // fase coarse
            List<Integer> coarseSeq = buildCoarseSequence(dataset.size());
            log("Iniciando FASE COARSE — " + coarseSeq.size() + " pontos de n (de "
                    + coarseSeq.get(0) + " a " + coarseSeq.get(coarseSeq.size() - 1) + ")");

            for (int i = 0; i < coarseSeq.size(); i++) {

                int n = coarseSeq.get(i);
                double pct = ((i + 1) * 100.0) / coarseSeq.size();
                log(String.format("[COARSE %5.1f%%] processando n=%d", pct, n));

                Datasets d = gerarDistribuicoes(dataset, n);
                Map<String, List<Long>> distMap = d.asMap();

                for (Combo combo : combosByKey.values()) {
                    if (!activeCombos.contains(combo.key)) continue;

                    List<Long> base = distMap.get(combo.distribution);
                    SortAlgorithm algo = algoritmos.get(combo.algorithm);

                    safeRunSort(combo, n, base, algo, report, "COARSE");
                }
            }

            log(String.format("[COARSE 100.0%%] fase coarse concluída."));

            // fase fine - só roda pras combinações que estouraram
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
                    List<Long> base = d.asMap().get(combo.distribution);

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

    // cresce multiplicando por factor; includeStart=false pula o valor inicial (já testado antes)
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
            // janela muito estreita na fase fine, garante pelo menos um ponto
            seq.add(Math.min(max, lastAdded + 1));
        }

        return seq;
    }

    static class Datasets {
        List<Long> random;
        List<Long> ascending;
        List<Long> descending;
        List<Long> nearAscendingPct;
        List<Long> nearDescendingPct;

        Map<String, List<Long>> asMap() {
            Map<String, List<Long>> m = new HashMap<>();
            m.put("random", random);
            m.put("ascending", ascending);
            m.put("descending", descending);
            m.put("near_ascending_pct", nearAscendingPct);
            m.put("near_descending_pct", nearDescendingPct);
            return m;
        }
    }

    // seed derivada de n pra garantir que o mesmo n sempre gera os mesmos dados
    static Datasets gerarDistribuicoes(List<Long> dataset, int n) {

        Datasets d = new Datasets();

        List<Long> base = new ArrayList<>(dataset.subList(0, n));

        d.ascending = new ArrayList<>(base);
        Collections.sort(d.ascending);

        d.descending = new ArrayList<>(d.ascending);
        Collections.reverse(d.descending);

        d.random = new ArrayList<>(base);
        Collections.shuffle(d.random, new Random(BASE_SEED + n));

        int pctSwaps = Math.max(1, (int) Math.round(n * NEAR_PCT));

        d.nearAscendingPct  = perturb(d.ascending,  pctSwaps, new Random(BASE_SEED + n + 1));
        d.nearDescendingPct = perturb(d.descending, pctSwaps, new Random(BASE_SEED + n + 3));

        return d;
    }

    static List<Long> perturb(List<Long> sortedBase, int swaps, Random r) {
        List<Long> copy = new ArrayList<>(sortedBase);
        int size = copy.size();

        if (size < 2) return copy;

        for (int i = 0; i < swaps; i++) {
            int a = r.nextInt(size);
            int b = r.nextInt(size);
            Collections.swap(copy, a, b);
        }

        return copy;
    }

    static boolean safeRunSort(Combo combo, int n, List<Long> data,
                                SortAlgorithm algo, BufferedWriter report,
                                String phase) throws IOException {

        String file = combo.key + ".csv";

        try {
            long[] arr = new long[data.size()];
            for (int i = 0; i < arr.length; i++) arr[i] = data.get(i);
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

    interface SortAlgorithm {
        void sort(long[] arr, Counters c);
    }

    static class Counters {
        long comparisons = 0;
        long copies = 0;
    }

    static Map<String, SortAlgorithm> buildAlgorithms() {
        Map<String, SortAlgorithm> m = new LinkedHashMap<>();
        m.put("quicksort",     (arr, c) -> new Algoritmo(arr, c).quickSort());
        m.put("mergesort",     (arr, c) -> new Algoritmo(arr, c).mergeSort());
        m.put("heapsort",      (arr, c) -> new Algoritmo(arr, c).heapSort());
        m.put("shellsort",     (arr, c) -> new Algoritmo(arr, c).shellSort());
        m.put("insertionsort", (arr, c) -> new Algoritmo(arr, c).insertionSort());
        m.put("selectionsort", (arr, c) -> new Algoritmo(arr, c).selectionSort());
        m.put("bubblesort",    (arr, c) -> new Algoritmo(arr, c).bubbleSort());
        return m;
    }

    // le a primeira coluna como numero - se carregar como String a ordenacao
    // vira lexicografica (1, 10, 100, 2, 20...) e as distribuicoes
    // crescente/decrescente ficam erradas
    static List<Long> loadIds(String file) throws IOException {

        List<Long> ids = new ArrayList<>();

        try (BufferedReader br = new BufferedReader(new FileReader(file))) {
            br.readLine(); // pula cabeçalho

            String line;
            while ((line = br.readLine()) != null) {
                String[] v = line.split(",", -1);
                if (v.length > 0 && !v[0].isEmpty()) ids.add(Long.parseLong(v[0]));
            }
        }

        return ids;
    }

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

    static void log(String message) {
        System.out.println("[" + new Date() + "] " + message);
    }

    static class Algoritmo {

        private final long[] a;
        private final int nElems;
        private final Counters c;

        Algoritmo(long[] data, Counters counters) {
            this.a      = data;
            this.nElems = data.length;
            this.c      = counters;
        }

        private void swap(int one, int two) {
            long temp = a[one];
            a[one] = a[two];
            c.copies++;
            a[two] = temp;
            c.copies++;
        }

        //--------------------------------------------------------------
        public void bubbleSort()
        {
            int out, in;
            for(out=nElems-1; out>=1; out--)
                for(in=0; in<out; in++) {
                    c.comparisons++;
                    if( a[in] > a[in+1] )
                        swap(in, in+1);
                }
        }
        //--------------------------------------------------------------

        //--------------------------------------------------------------
        public void selectionSort() {
            int out, in, min;
            for(out=0; out<nElems-1; out++) {
                min = out;
                for(in=out+1; in<nElems; in++) {
                    c.comparisons++;
                    if(a[in] < a[min])
                        min = in;
                }
                swap(out, min);
            }
        }
        //--------------------------------------------------------------

        //--------------------------------------------------------------
        public void insertionSort() {
            int in, out;
            for(out=1; out<nElems; out++) {
                long temp = a[out];
                in = out;
                while(in>0) {
                    c.comparisons++;
                    if(a[in-1] >= temp) {
                        a[in] = a[in-1];
                        c.copies++;
                        --in;
                    } else break;
                }
                a[in] = temp;
                c.copies++;
            }
        }
        //--------------------------------------------------------------

        //--------------------------------------------------------------
        public void shellSort()
        {
            int inner, outer;
            long temp;
            int h = 1;
            while(h <= nElems/3)
                h = h*3 + 1;
            while(h>0)
            {
                for(outer=h; outer<nElems; outer++)
                {
                    temp = a[outer];
                    inner = outer;
                    while(inner > h-1) {
                        c.comparisons++;
                        if(a[inner-h] >= temp) {
                            a[inner] = a[inner-h];
                            c.copies++;
                            inner -= h;
                        } else break;
                    }
                    a[inner] = temp;
                    c.copies++;
                }
                h = (h-1) / 3;
            }
        }
        //--------------------------------------------------------------

        //--------------------------------------------------------------
        public void mergeSort()
        {
            long[] workSpace = new long[nElems];
            recMergeSort(workSpace, 0, nElems - 1);
        }

        private void recMergeSort(long[] workSpace, int lowerBound, int upperBound)
        {
            if(lowerBound == upperBound)
                return;
            else
            {
                int mid = (lowerBound + upperBound)/2;
                recMergeSort(workSpace, lowerBound, mid);
                recMergeSort(workSpace, mid + 1, upperBound);
                merge(workSpace, lowerBound, mid + 1, upperBound);
            }
        }

        private void merge(long[] workSpace, int lowPtr, int highPtr, int upperBound)
        {
            int j = 0;
            int lowerBound = lowPtr;
            int mid = highPtr - 1;
            int n = upperBound - lowerBound + 1;
            while(lowPtr <= mid && highPtr <= upperBound)
            {
                c.comparisons++;
                if(a[lowPtr] < a[highPtr])
                    workSpace[j++] = a[lowPtr++];
                else
                    workSpace[j++] = a[highPtr++];
                c.copies++;
            }
            while(lowPtr <= mid) {
                workSpace[j++] = a[lowPtr++];
                c.copies++;
            }
            while(highPtr <= upperBound) {
                workSpace[j++] = a[highPtr++];
                c.copies++;
            }
            for(j = 0; j < n; j++) {
                a[lowerBound + j] = workSpace[j];
                c.copies++;
            }
        }
        //--------------------------------------------------------------

        // heapsort
        public void heapSort() {
            for (int i = nElems / 2 - 1; i >= 0; i--)
                siftDown(nElems, i);
            for (int end = nElems - 1; end > 0; end--) {
                swap(0, end);
                siftDown(end, 0);
            }
        }

        private void siftDown(int size, int root) {
            int largest = root;
            int left  = 2 * root + 1;
            int right = 2 * root + 2;
            if (left < size) {
                c.comparisons++;
                if (a[left] > a[largest]) largest = left;
            }
            if (right < size) {
                c.comparisons++;
                if (a[right] > a[largest]) largest = right;
            }
            if (largest != root) {
                swap(root, largest);
                siftDown(size, largest);
            }
        }

        // quicksort com pivô no primeiro elemento - estoura pilha em entrada já ordenada
        public void quickSort() {
            quickSort(0, nElems - 1);
        }

        private void quickSort(int lo, int hi) {
            if (lo >= hi) return;
            int p = partition(lo, hi);
            quickSort(lo, p - 1);
            quickSort(p + 1, hi);
        }

        private int partition(int lo, int hi) {
            long pivot = a[lo];
            int i = lo + 1;
            int j = hi;
            while (true) {
                while (i <= hi) {
                    c.comparisons++;
                    if (a[i] > pivot) break;
                    i++;
                }
                while (j > lo) {
                    c.comparisons++;
                    if (a[j] < pivot) break;
                    j--;
                }
                if (i >= j) break;
                swap(i, j);
            }
            swap(lo, j);
            return j;
        }
    }
}
