import java.io.*;
import java.util.*;

// uso: java GerarDistribuicoes <n>
// gera as 7 distribuicoes pra um n e salva em CSV pra visualizar como os dados ficam antes de ordenar
public class GerarDistribuicoes {

    private static final String CSV_FILE    = "solarradiation.csv";
    private static final String OUTPUT_FILE = "output_distribuicoes.csv";
    private static final long   BASE_SEED   = 42L;
    private static final double NEAR_PCT    = 0.05;

    public static void main(String[] args) throws Exception {
        int n = args.length > 0 ? Integer.parseInt(args[0]) : 20;

        List<String> dataset = loadIds(CSV_FILE);

        if (n > dataset.size()) {
            System.out.println("n=" + n + " maior que o dataset (" + dataset.size() + "), usando " + dataset.size());
            n = dataset.size();
        }

        Datasets d = gerarDistribuicoes(dataset, n);
        exportar(d, n);

        System.out.println("Exportado: " + OUTPUT_FILE + " (n=" + n + ")");
    }

    static void exportar(Datasets d, int n) throws IOException {
        try (BufferedWriter bw = new BufferedWriter(new FileWriter(OUTPUT_FILE))) {
            bw.write("index,random,ascending,descending," +
                     "near_ascending_pct,near_ascending_fixed," +
                     "near_descending_pct,near_descending_fixed");
            bw.newLine();

            for (int i = 0; i < n; i++) {
                bw.write(i
                    + "," + d.random.get(i)
                    + "," + d.ascending.get(i)
                    + "," + d.descending.get(i)
                    + "," + d.nearAscendingPct.get(i)
                    + "," + d.nearAscendingFixed.get(i)
                    + "," + d.nearDescendingPct.get(i)
                    + "," + d.nearDescendingFixed.get(i));
                bw.newLine();
            }
        }
    }

    static class Datasets {
        List<String> random;
        List<String> ascending;
        List<String> descending;
        List<String> nearAscendingPct;
        List<String> nearAscendingFixed;
        List<String> nearDescendingPct;
        List<String> nearDescendingFixed;
    }

    // seed derivada de n pra garantir reproducibilidade
    static Datasets gerarDistribuicoes(List<String> dataset, int n) {
        Datasets d = new Datasets();

        List<String> base = new ArrayList<>(dataset.subList(0, n));

        d.ascending = new ArrayList<>(base);
        Collections.sort(d.ascending);

        d.descending = new ArrayList<>(d.ascending);
        Collections.reverse(d.descending);

        d.random = new ArrayList<>(base);
        Collections.shuffle(d.random, new Random(BASE_SEED + n));

        int pctSwaps   = Math.max(1, (int) Math.round(n * NEAR_PCT));
        int fixedSwaps = Math.max(1, (int) Math.round(Math.sqrt(n)));

        d.nearAscendingPct    = perturb(d.ascending,  pctSwaps,   new Random(BASE_SEED + n + 1));
        d.nearAscendingFixed  = perturb(d.ascending,  fixedSwaps, new Random(BASE_SEED + n + 2));
        d.nearDescendingPct   = perturb(d.descending, pctSwaps,   new Random(BASE_SEED + n + 3));
        d.nearDescendingFixed = perturb(d.descending, fixedSwaps, new Random(BASE_SEED + n + 4));

        return d;
    }

    static List<String> perturb(List<String> sortedBase, int swaps, Random r) {
        List<String> copy = new ArrayList<>(sortedBase);
        if (copy.size() < 2) return copy;
        for (int i = 0; i < swaps; i++) {
            int a = r.nextInt(copy.size());
            int b = r.nextInt(copy.size());
            Collections.swap(copy, a, b);
        }
        return copy;
    }

    static List<String> loadIds(String file) throws IOException {
        List<String> ids = new ArrayList<>();
        try (BufferedReader br = new BufferedReader(new FileReader(file))) {
            br.readLine(); // pula cabeçalho
            String line;
            while ((line = br.readLine()) != null) {
                String[] v = line.split(",", -1);
                if (v.length > 0) ids.add(v[0]);
            }
        }
        return ids;
    }
}
