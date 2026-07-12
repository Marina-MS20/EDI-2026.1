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
// benchmark. por padrão carrega o csv inteiro (~7 milhões de registros).
// uso: java -jar AplicacaoEDI.jar [limite] [csv]
public class AplicacaoFinal {

    private static final int LIMITE_PADRAO = Integer.MAX_VALUE;

    // teto de linhas jogadas na JTable - acima disso a tabela consome
    // memória demais e não dá pra ler mesmo
    private static final int MAX_LINHAS_TABELA = 200_000;

    private final TArvoreAVL arvore = new TArvoreAVL();
    private final Analises analises = new Analises(arvore);
    private long totalRegistros = 0;

    private JFrame frame;
    private CardLayout cards;
    private JPanel raiz;
    private JLabel lblStatus;

    private JTextField txtBuscaId;
    private JTextField txtBuscaData;
    private JTextArea areaBusca;
    private JTextField[] txtInserir;
    private JTextField txtRemoveId;
    private JTextArea areaRemove;
    private JTable tabela;
    private JLabel lblOrdenacao;
    private JTextField txtData;
    private JTextField txtLambda;
    private JTextField txtDe;
    private JTextField txtAte;
    private JComboBox<String> cmbCampo;
    private JTextField txtValor;
    private JTextArea areaAnalises;

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
        JLabel lbl = new JLabel("Aguarde...");
        lbl.setFont(lbl.getFont().deriveFont(Font.BOLD, 16f));
        p.add(lbl);
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
        abas.addTab("Análises", montarAbaAnalises());
        p.add(abas, BorderLayout.CENTER);

        return p;
    }

    // carrega o csv numa thread separada pra não travar a janela.
    // montar a árvore inserindo um a um seria O(n²) por causa do balanco()
    // do professor (inviável pra 7 milhões), então: lê tudo pra um vetor,
    // garante a ordem por ID (o csv já vem ordenado; se não vier, o
    // mergesort do benchmark resolve) e monta a árvore em tempo linear com
    // o CriaABP do exercício 10.
    private void carregarBase(String csv, int limite) {
        SwingWorker<Long, Void> worker = new SwingWorker<>() {

            long tempoNs;

            @Override
            protected Long doInBackground() throws Exception {
                long inicio = System.nanoTime();

                List<Registro> lista = new ArrayList<>();
                boolean ordenado = true;
                long ultimoId = Long.MIN_VALUE;

                try (BufferedReader br = new BufferedReader(new FileReader(csv))) {
                    br.readLine(); // pula cabeçalho

                    String line;
                    while (lista.size() < limite && (line = br.readLine()) != null) {
                        Registro r = Registro.fromCsv(line);
                        if (r == null) continue;
                        if (r.id < ultimoId) ordenado = false;
                        ultimoId = r.id;
                        lista.add(r);
                    }
                }

                Registro[] v = lista.toArray(new Registro[0]);
                lista = null;

                if (!ordenado)
                    new Ordenacao(v, new Ordenacao.Counters()).mergeSort();

                arvore.constroiDeVetorOrdenado(v);

                tempoNs = System.nanoTime() - inicio;
                return (long) v.length;
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

        JPanel topo = new JPanel(new GridLayout(0, 1));

        JPanel porId = new JPanel(new FlowLayout(FlowLayout.LEFT));
        porId.add(new JLabel("ID do registro:"));
        txtBuscaId = new JTextField(14);
        porId.add(txtBuscaId);
        JButton btn = new JButton("Buscar");
        porId.add(btn);
        topo.add(porId);

        JPanel porCampos = new JPanel(new FlowLayout(FlowLayout.LEFT));
        porCampos.add(new JLabel("Por campos: data (aaaa-mm-dd)"));
        txtBuscaData = new JTextField(9);
        porCampos.add(txtBuscaData);
        porCampos.add(new JLabel("campo"));
        cmbCampo = new JComboBox<>(Registro.COLUNAS);
        porCampos.add(cmbCampo);
        porCampos.add(new JLabel("valor"));
        txtValor = new JTextField(10);
        porCampos.add(txtValor);
        JButton btnCampos = new JButton("Pesquisar registros");
        porCampos.add(btnCampos);
        topo.add(porCampos);

        p.add(topo, BorderLayout.NORTH);

        areaBusca = new JTextArea();
        areaBusca.setEditable(false);
        areaBusca.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 13));
        p.add(new JScrollPane(areaBusca), BorderLayout.CENTER);

        btnCampos.addActionListener(e -> {
            String data = txtBuscaData.getText().trim();
            String valor = txtValor.getText().trim();
            if (data.isEmpty() && valor.isEmpty()) {
                areaBusca.setText("Informe a data e/ou um valor para o campo.");
                return;
            }
            areaBusca.setText(analises.pesquisaPorCampos(data,
                    (String) cmbCampo.getSelectedItem(), valor));
        });

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

            int exibidos = preencherTabela(arr);
            lblOrdenacao.setText(String.format(
                    "MergeSort por ID - %,d registros ordenados em %s   |   comparações: %,d   |   cópias: %,d%s",
                    arr.length, fmtNs(tempo), c.comparisons, c.copies,
                    exibidos < arr.length ? String.format("   |   exibindo os primeiros %,d", exibidos) : ""));
        });

        // em-ordem já sai ordenado, sem precisar ordenar
        btnEmOrdem.addActionListener(e -> {
            List<Registro> lista = new ArrayList<>();
            long inicio = System.nanoTime();
            arvore.emOrdem(lista);
            long tempo = System.nanoTime() - inicio;

            int exibidos = preencherTabela(lista.toArray(new Registro[0]));
            lblOrdenacao.setText(String.format(
                    "Caminhamento em-ordem - %,d registros visitados de forma ordenada em %s%s",
                    lista.size(), fmtNs(tempo),
                    exibidos < lista.size() ? String.format("   |   exibindo os primeiros %,d", exibidos) : ""));
        });

        return p;
    }

    private int preencherTabela(Registro[] dados) {
        int n = Math.min(dados.length, MAX_LINHAS_TABELA);
        Object[][] linhas = new Object[n][];
        for (int i = 0; i < n; i++)
            linhas[i] = dados[i].toRow();

        tabela.setModel(new DefaultTableModel(linhas, Registro.COLUNAS) {
            @Override
            public boolean isCellEditable(int r, int c) { return false; }
        });
        for (int i = 0; i < Registro.COLUNAS.length; i++)
            tabela.getColumnModel().getColumn(i).setPreferredWidth(i == 0 ? 90 : 130);
        return n;
    }

    // ===================== ABA ANÁLISES =====================

    private JPanel montarAbaAnalises() {
        JPanel p = new JPanel(new BorderLayout(8, 8));
        p.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        JPanel topo = new JPanel(new GridLayout(0, 1));

        JPanel campos = new JPanel(new FlowLayout(FlowLayout.LEFT));
        campos.add(new JLabel("Data (aaaa-mm-dd):"));
        txtData = new JTextField(9);
        campos.add(txtData);
        campos.add(new JLabel("Comprimento de onda (nm):"));
        txtLambda = new JTextField(7);
        campos.add(txtLambda);
        campos.add(new JLabel("Intervalo (nm): de"));
        txtDe = new JTextField(6);
        campos.add(txtDe);
        campos.add(new JLabel("até"));
        txtAte = new JTextField(6);
        campos.add(txtAte);
        topo.add(campos);

        JPanel botoes = new JPanel(new FlowLayout(FlowLayout.LEFT));
        JButton b1 = new JButton("Maior emissão da data");
        JButton b2 = new JButton("Data de maior emissão do λ");
        JButton b3 = new JButton("Primeira e última data");
        JButton b4 = new JButton("Menor e maior λ");
        JButton b5 = new JButton("Média no intervalo");
        JButton b6 = new JButton("Gráfico do espectro");
        botoes.add(b1);
        botoes.add(b2);
        botoes.add(b3);
        botoes.add(b4);
        botoes.add(b5);
        botoes.add(b6);
        topo.add(botoes);

        p.add(topo, BorderLayout.NORTH);

        areaAnalises = new JTextArea();
        areaAnalises.setEditable(false);
        areaAnalises.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 13));
        p.add(new JScrollPane(areaAnalises), BorderLayout.CENTER);

        b1.addActionListener(e -> {
            String data = txtData.getText().trim();
            if (data.isEmpty()) { avisa("Informe a data."); return; }
            registraLog(analises.maiorEmissaoNaData(data));
        });

        b2.addActionListener(e -> {
            Double lambda = lerDouble(txtLambda.getText());
            if (lambda == null) { avisa("Informe o comprimento de onda."); return; }
            registraLog(analises.dataDeMaiorEmissao(lambda));
        });

        b3.addActionListener(e -> registraLog(analises.limitesDeDatas()));

        b4.addActionListener(e -> registraLog(analises.limitesDeLambda()));

        b5.addActionListener(e -> {
            String data = txtData.getText().trim();
            Double de = lerDouble(txtDe.getText());
            Double ate = lerDouble(txtAte.getText());
            if (data.isEmpty() || de == null || ate == null) {
                avisa("Informe a data e o intervalo de comprimento de onda.");
                return;
            }
            registraLog(analises.mediaNoIntervalo(data, de, ate));
        });

        b6.addActionListener(e -> {
            String data = txtData.getText().trim();
            if (data.isEmpty()) { avisa("Informe a data."); return; }

            Analises.Espectro esp = analises.espectroDaData(data);
            registraLog(esp.registro);

            if (esp.pontos.isEmpty()) {
                avisa("Nenhum registro para a data " + data + ".");
                return;
            }
            JDialog d = new JDialog(frame, "Espectro de emissão - " + data, false);
            d.setContentPane(new GraficoEspectro(data, esp.pontos));
            d.pack();
            d.setLocationRelativeTo(frame);
            d.setVisible(true);
        });

        return p;
    }

    private void avisa(String msg) {
        JOptionPane.showMessageDialog(frame, msg, "Análises", JOptionPane.WARNING_MESSAGE);
    }

    private void registraLog(String registro) {
        areaAnalises.append(registro);
        areaAnalises.append("--------------------------------------------------\n");
        areaAnalises.setCaretPosition(areaAnalises.getDocument().getLength());
    }

    // ===================== AUXILIARES =====================

    private static Long lerLong(String s) {
        try {
            return Long.parseLong(s.trim());
        } catch (Exception e) {
            return null;
        }
    }

    private static Double lerDouble(String s) {
        try {
            return Double.parseDouble(s.trim().replace(',', '.'));
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
