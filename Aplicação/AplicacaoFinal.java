import javax.swing.*;
import javax.swing.table.DefaultTableModel;
import java.awt.*;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.List;

// aplicação final - EDI 2026.1
// GUI sobre o solarradiation.csv: os registros ficam na AVL do professor
// (busca, inserção e remoção) e a exibição ordenada usa o mergesort do
// benchmark. uso: java -jar AplicacaoEDI.jar [limite] [csv]
public class AplicacaoFinal {

    private static final int LIMITE_PADRAO = 100_000;

    private final TArvoreAVL arvore = new TArvoreAVL();
    private long totalRegistros = 0;

    private JFrame frame;
    private CardLayout cards;
    private JPanel raiz;
    private JProgressBar barra;
    private JLabel lblCarga;
    private JLabel lblStatus;

    private JTextField txtBuscaId;
    private JTextArea areaBusca;
    private JTextField[] txtInserir;
    private JTextField txtRemoveId;
    private JTextArea areaRemove;
    private JTable tabela;
    private JLabel lblOrdenacao;

    public static void main(String[] args) {
        int limite = LIMITE_PADRAO;
        String csv = null;

        if (args.length >= 1) limite = Integer.parseInt(args[0]);
        if (args.length >= 2) csv = args[1];

        if (csv == null) {
            // o csv fica na raiz do projeto, uma pasta acima
            if (new File("solarradiation.csv").exists()) csv = "solarradiation.csv";
            else csv = ".." + File.separator + "solarradiation.csv";
        }

        final int lim = limite;
        final String arquivo = csv;

        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) { }

        SwingUtilities.invokeLater(() -> new AplicacaoFinal().iniciar(arquivo, lim));
    }

    private void iniciar(String csv, int limite) {
        frame = new JFrame("EDI 2026.1 - Aplicação Final - Irradiância Solar");
        frame.setDefaultCloseOperation(WindowConstants.EXIT_ON_CLOSE);
        frame.setSize(1080, 720);
        frame.setLocationRelativeTo(null);

        cards = new CardLayout();
        raiz = new JPanel(cards);
        raiz.add(montarTelaCarga(), "carga");
        raiz.add(montarTelaApp(), "app");

        frame.setContentPane(raiz);
        frame.setVisible(true);

        carregarBase(csv, limite);
    }

    private JPanel montarTelaCarga() {
        JPanel p = new JPanel(new GridBagLayout());
        JPanel centro = new JPanel();
        centro.setLayout(new BoxLayout(centro, BoxLayout.Y_AXIS));

        JLabel titulo = new JLabel("Carregando a base e construindo a árvore AVL...");
        titulo.setFont(titulo.getFont().deriveFont(Font.BOLD, 16f));
        titulo.setAlignmentX(Component.CENTER_ALIGNMENT);

        lblCarga = new JLabel(" ");
        lblCarga.setAlignmentX(Component.CENTER_ALIGNMENT);

        barra = new JProgressBar(0, 100);
        barra.setStringPainted(true);
        barra.setPreferredSize(new Dimension(420, 28));
        barra.setMaximumSize(new Dimension(420, 28));
        barra.setAlignmentX(Component.CENTER_ALIGNMENT);

        centro.add(titulo);
        centro.add(Box.createVerticalStrut(12));
        centro.add(barra);
        centro.add(Box.createVerticalStrut(8));
        centro.add(lblCarga);

        p.add(centro);
        return p;
    }

    private JPanel montarTelaApp() {
        JPanel p = new JPanel(new BorderLayout());

        lblStatus = new JLabel(" ");
        lblStatus.setBorder(BorderFactory.createEmptyBorder(6, 10, 6, 10));
        lblStatus.setFont(lblStatus.getFont().deriveFont(Font.BOLD));
        p.add(lblStatus, BorderLayout.NORTH);

        JTabbedPane abas = new JTabbedPane();
        abas.addTab("Buscar", montarAbaBuscar());
        abas.addTab("Inserir", montarAbaInserir());
        abas.addTab("Remover", montarAbaRemover());
        abas.addTab("Exibição ordenada", montarAbaExibicao());
        p.add(abas, BorderLayout.CENTER);

        return p;
    }

    // carrega o csv numa thread separada pra não travar a janela,
    // atualizando a barra de progresso
    private void carregarBase(String csv, int limite) {
        SwingWorker<Long, Integer> worker = new SwingWorker<>() {

            long tempoNs;

            @Override
            protected Long doInBackground() throws Exception {
                long inicio = System.nanoTime();
                long lidos = 0;

                try (BufferedReader br = new BufferedReader(new FileReader(csv))) {
                    br.readLine(); // pula cabeçalho

                    String line;
                    while (lidos < limite && (line = br.readLine()) != null) {
                        Registro r = Registro.fromCsv(line);
                        if (r == null) continue;
                        arvore.insere(r.id, r);
                        lidos++;
                        if (lidos % 500 == 0) publish((int) (lidos * 100 / limite));
                    }
                }

                tempoNs = System.nanoTime() - inicio;
                return lidos;
            }

            @Override
            protected void process(List<Integer> chunks) {
                int pct = chunks.get(chunks.size() - 1);
                barra.setValue(pct);
                lblCarga.setText(String.format("%,d de %,d registros inseridos na AVL",
                        (long) pct * limite / 100, (long) limite));
            }

            @Override
            protected void done() {
                try {
                    totalRegistros = get();
                    atualizarStatus(String.format("Base carregada em %s.", fmtNs(tempoNs)));
                    cards.show(raiz, "app");
                } catch (Exception e) {
                    JOptionPane.showMessageDialog(frame,
                            "Erro ao carregar '" + csv + "':\n" + e.getCause(),
                            "Erro na carga", JOptionPane.ERROR_MESSAGE);
                    System.exit(1);
                }
            }
        };
        worker.execute();
    }

    private void atualizarStatus(String extra) {
        lblStatus.setText(String.format(
                "Registros na AVL: %,d      Altura da árvore: %d      %s",
                totalRegistros, arvore.altura(), extra == null ? "" : extra));
    }

    // ===================== ABA BUSCAR =====================

    private JPanel montarAbaBuscar() {
        JPanel p = new JPanel(new BorderLayout(8, 8));
        p.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        JPanel topo = new JPanel(new FlowLayout(FlowLayout.LEFT));
        topo.add(new JLabel("ID do registro:"));
        txtBuscaId = new JTextField(14);
        topo.add(txtBuscaId);
        JButton btn = new JButton("Buscar");
        topo.add(btn);
        p.add(topo, BorderLayout.NORTH);

        areaBusca = new JTextArea();
        areaBusca.setEditable(false);
        areaBusca.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 13));
        p.add(new JScrollPane(areaBusca), BorderLayout.CENTER);

        Runnable buscar = () -> {
            Long id = lerLong(txtBuscaId.getText());
            if (id == null) { areaBusca.setText("Informe um ID numérico."); return; }

            arvore.comparisons = 0;
            long inicio = System.nanoTime();
            TArvoreAVL.TNodo nodo = arvore.pesquisa(id);
            long tempo = System.nanoTime() - inicio;
            long comps = arvore.comparisons;

            StringBuilder sb = new StringBuilder();
            if (nodo == null) {
                sb.append("ID ").append(id).append(" NÃO encontrado.\n");
            } else {
                sb.append("Registro encontrado:\n\n");
                Object[] row = nodo.item.toRow();
                for (int i = 0; i < Registro.COLUNAS.length; i++)
                    sb.append(String.format("  %-24s %s%n", Registro.COLUNAS[i] + ":", row[i]));
            }
            sb.append("\n----------------------------------------\n");
            sb.append("Comparações: ").append(comps).append("\n");
            sb.append("Tempo de busca: ").append(fmtNs(tempo)).append("\n");
            areaBusca.setText(sb.toString());
        };

        btn.addActionListener(e -> buscar.run());
        txtBuscaId.addActionListener(e -> buscar.run());
        return p;
    }

    // ===================== ABA INSERIR =====================

    private JPanel montarAbaInserir() {
        JPanel p = new JPanel(new BorderLayout(8, 8));
        p.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        JPanel form = new JPanel(new GridBagLayout());
        GridBagConstraints g = new GridBagConstraints();
        g.insets = new Insets(4, 6, 4, 6);
        g.anchor = GridBagConstraints.WEST;

        txtInserir = new JTextField[Registro.COLUNAS.length];
        for (int i = 0; i < Registro.COLUNAS.length; i++) {
            g.gridx = 0; g.gridy = i;
            form.add(new JLabel(Registro.COLUNAS[i] + ":"), g);
            txtInserir[i] = new JTextField(24);
            g.gridx = 1;
            form.add(txtInserir[i], g);
        }

        JButton btn = new JButton("Inserir");
        g.gridx = 1; g.gridy = Registro.COLUNAS.length;
        form.add(btn, g);

        JPanel esquerda = new JPanel(new BorderLayout());
        esquerda.add(form, BorderLayout.NORTH);
        p.add(esquerda, BorderLayout.CENTER);

        btn.addActionListener(e -> {
            Long id = lerLong(txtInserir[0].getText());
            if (id == null) {
                JOptionPane.showMessageDialog(frame, "Informe um ID numérico.",
                        "Inserção", JOptionPane.WARNING_MESSAGE);
                return;
            }
            // o insere do professor ignora chave repetida, então avisa antes
            if (arvore.pesquisa(id) != null) {
                JOptionPane.showMessageDialog(frame,
                        "Já existe um registro com ID " + id + ".",
                        "Inserção", JOptionPane.WARNING_MESSAGE);
                return;
            }

            Registro r = new Registro(id,
                    txtInserir[1].getText().trim(), txtInserir[2].getText().trim(),
                    txtInserir[3].getText().trim(), txtInserir[4].getText().trim(),
                    txtInserir[5].getText().trim(), txtInserir[6].getText().trim(),
                    txtInserir[7].getText().trim(), txtInserir[8].getText().trim());

            long inicio = System.nanoTime();
            arvore.insere(r.id, r);
            long tempo = System.nanoTime() - inicio;

            totalRegistros++;
            atualizarStatus("Última operação: inserção do ID " + id + " em " + fmtNs(tempo) + ".");
            JOptionPane.showMessageDialog(frame,
                    "Registro " + id + " inserido em " + fmtNs(tempo)
                            + ".\nNova altura da árvore: " + arvore.altura(),
                    "Inserção", JOptionPane.INFORMATION_MESSAGE);
        });

        return p;
    }

    // ===================== ABA REMOVER =====================

    private JPanel montarAbaRemover() {
        JPanel p = new JPanel(new BorderLayout(8, 8));
        p.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        JPanel topo = new JPanel(new FlowLayout(FlowLayout.LEFT));
        topo.add(new JLabel("ID do registro:"));
        txtRemoveId = new JTextField(14);
        topo.add(txtRemoveId);
        JButton btn = new JButton("Remover");
        topo.add(btn);
        p.add(topo, BorderLayout.NORTH);

        areaRemove = new JTextArea();
        areaRemove.setEditable(false);
        areaRemove.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 13));
        p.add(new JScrollPane(areaRemove), BorderLayout.CENTER);

        Runnable remover = () -> {
            Long id = lerLong(txtRemoveId.getText());
            if (id == null) { areaRemove.setText("Informe um ID numérico."); return; }

            long inicio = System.nanoTime();
            boolean ok = arvore.remove(id);
            long tempo = System.nanoTime() - inicio;

            if (ok) {
                totalRegistros--;
                atualizarStatus("Última operação: remoção do ID " + id + " em " + fmtNs(tempo) + ".");
                areaRemove.setText("Registro " + id + " removido em " + fmtNs(tempo)
                        + ".\nNova altura da árvore: " + arvore.altura()
                        + "\nRegistros restantes: " + String.format("%,d", totalRegistros));
            } else {
                areaRemove.setText("ID " + id + " NÃO encontrado - nada foi removido.");
            }
        };

        btn.addActionListener(e -> remover.run());
        txtRemoveId.addActionListener(e -> remover.run());
        return p;
    }

    // ===================== ABA EXIBIÇÃO ORDENADA =====================

    private JPanel montarAbaExibicao() {
        JPanel p = new JPanel(new BorderLayout(8, 8));
        p.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        JPanel topo = new JPanel(new FlowLayout(FlowLayout.LEFT));
        JButton btnMerge = new JButton("Ordenar por ID (MergeSort)");
        JButton btnEmOrdem = new JButton("Exibir em-ordem (caminhamento da AVL)");
        topo.add(btnMerge);
        topo.add(btnEmOrdem);
        p.add(topo, BorderLayout.NORTH);

        tabela = new JTable();
        tabela.setAutoResizeMode(JTable.AUTO_RESIZE_OFF);
        p.add(new JScrollPane(tabela), BorderLayout.CENTER);

        lblOrdenacao = new JLabel(" ");
        lblOrdenacao.setBorder(BorderFactory.createEmptyBorder(4, 4, 4, 4));
        p.add(lblOrdenacao, BorderLayout.SOUTH);

        // coleta em pré-ordem (desordenado) e ordena com o mergesort
        btnMerge.addActionListener(e -> {
            List<Registro> lista = new ArrayList<>();
            arvore.preOrdem(lista);
            Registro[] arr = lista.toArray(new Registro[0]);

            Ordenacao.Counters c = new Ordenacao.Counters();
            long inicio = System.nanoTime();
            new Ordenacao(arr, c).mergeSort();
            long tempo = System.nanoTime() - inicio;

            preencherTabela(arr);
            lblOrdenacao.setText(String.format(
                    "MergeSort por ID - %,d registros ordenados em %s   |   comparações: %,d   |   cópias: %,d",
                    arr.length, fmtNs(tempo), c.comparisons, c.copies));
        });

        // em-ordem já sai ordenado, sem precisar ordenar
        btnEmOrdem.addActionListener(e -> {
            List<Registro> lista = new ArrayList<>();
            long inicio = System.nanoTime();
            arvore.emOrdem(lista);
            long tempo = System.nanoTime() - inicio;

            preencherTabela(lista.toArray(new Registro[0]));
            lblOrdenacao.setText(String.format(
                    "Caminhamento em-ordem - %,d registros visitados de forma ordenada em %s",
                    lista.size(), fmtNs(tempo)));
        });

        return p;
    }

    private void preencherTabela(Registro[] dados) {
        Object[][] linhas = new Object[dados.length][];
        for (int i = 0; i < dados.length; i++)
            linhas[i] = dados[i].toRow();

        tabela.setModel(new DefaultTableModel(linhas, Registro.COLUNAS) {
            @Override
            public boolean isCellEditable(int r, int c) { return false; }
        });
        for (int i = 0; i < Registro.COLUNAS.length; i++)
            tabela.getColumnModel().getColumn(i).setPreferredWidth(i == 0 ? 90 : 130);
    }

    // ===================== AUXILIARES =====================

    private static Long lerLong(String s) {
        try {
            return Long.parseLong(s.trim());
        } catch (Exception e) {
            return null;
        }
    }

    private static String fmtNs(long ns) {
        if (ns < 1_000L) return ns + " ns";
        if (ns < 1_000_000L) return String.format("%.1f µs", ns / 1e3);
        if (ns < 1_000_000_000L) return String.format("%.1f ms", ns / 1e6);
        return String.format("%.2f s", ns / 1e9);
    }
}
