import javax.swing.*;
import java.awt.*;
import java.awt.geom.AffineTransform;
import java.util.List;

// gráfico do espectro (irradiância x comprimento de onda) desenhado com
// Graphics2D. se a data tiver mais pontos que pixels, o desenho pula pontos
// pra não pesar.
public class GraficoEspectro extends JPanel {

    private final String data;
    private final List<double[]> pontos;

    public GraficoEspectro(String data, List<double[]> pontos) {
        this.data = data;
        this.pontos = pontos;
        setBackground(Color.WHITE);
        setPreferredSize(new Dimension(900, 600));
    }

    @Override
    protected void paintComponent(Graphics g0) {
        super.paintComponent(g0);
        Graphics2D g = (Graphics2D) g0;
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        int mEsq = 85, mDir = 30, mCima = 50, mBaixo = 65;
        int w = getWidth() - mEsq - mDir;
        int h = getHeight() - mCima - mBaixo;
        if (w < 50 || h < 50 || pontos.isEmpty()) return;

        double xMin = Double.MAX_VALUE, xMax = -Double.MAX_VALUE;
        double yMin = Double.MAX_VALUE, yMax = -Double.MAX_VALUE;
        for (double[] p : pontos) {
            if (p[0] < xMin) xMin = p[0];
            if (p[0] > xMax) xMax = p[0];
            if (p[1] < yMin) yMin = p[1];
            if (p[1] > yMax) yMax = p[1];
        }
        if (xMax - xMin < 1e-12) xMax = xMin + 1;
        if (yMax - yMin < 1e-12) yMax = yMin + 1;

        FontMetrics fm = g.getFontMetrics();
        int div = 6;
        for (int i = 0; i <= div; i++) {
            int px = mEsq + w * i / div;
            int py = mCima + h - h * i / div;

            g.setColor(new Color(230, 230, 230));
            g.drawLine(px, mCima, px, mCima + h);
            g.drawLine(mEsq, py, mEsq + w, py);

            g.setColor(Color.BLACK);
            g.drawLine(px, mCima + h, px, mCima + h + 4);
            String sx = String.format("%.0f", xMin + (xMax - xMin) * i / div);
            g.drawString(sx, px - fm.stringWidth(sx) / 2, mCima + h + 18);

            g.drawLine(mEsq - 4, py, mEsq, py);
            String sy = fmtY(yMin + (yMax - yMin) * i / div);
            g.drawString(sy, mEsq - 8 - fm.stringWidth(sy), py + 4);
        }

        g.setColor(Color.BLACK);
        g.drawLine(mEsq, mCima, mEsq, mCima + h);
        g.drawLine(mEsq, mCima + h, mEsq + w, mCima + h);

        // espectro; passo > 1 quando tem mais pontos que o dobro da largura
        g.setColor(new Color(200, 60, 30));
        int passo = Math.max(1, pontos.size() / (w * 2));
        int px0 = -1, py0 = -1;
        for (int i = 0; i < pontos.size(); i += passo) {
            double[] p = pontos.get(i);
            int px = mEsq + (int) ((p[0] - xMin) / (xMax - xMin) * w);
            int py = mCima + h - (int) ((p[1] - yMin) / (yMax - yMin) * h);
            if (px0 >= 0) g.drawLine(px0, py0, px, py);
            px0 = px;
            py0 = py;
        }

        g.setColor(Color.BLACK);
        g.setFont(getFont().deriveFont(Font.BOLD, 15f));
        String titulo = "Espectro de emissão solar - " + data;
        FontMetrics fmT = g.getFontMetrics();
        g.drawString(titulo, mEsq + (w - fmT.stringWidth(titulo)) / 2, 28);

        g.setFont(getFont().deriveFont(Font.PLAIN, 12f));
        fm = g.getFontMetrics();
        String lx = "Comprimento de onda (nm)";
        g.drawString(lx, mEsq + (w - fm.stringWidth(lx)) / 2, getHeight() - 12);

        String ly = "Irradiância (W/m²/nm)";
        AffineTransform antes = g.getTransform();
        g.rotate(-Math.PI / 2);
        g.drawString(ly, -(mCima + h / 2 + fm.stringWidth(ly) / 2), 22);
        g.setTransform(antes);

        int lgW = 200, lgX = mEsq + w - lgW - 10, lgY = mCima + 10;
        g.setColor(Color.WHITE);
        g.fillRect(lgX, lgY, lgW, 24);
        g.setColor(Color.GRAY);
        g.drawRect(lgX, lgY, lgW, 24);
        g.setColor(new Color(200, 60, 30));
        g.drawLine(lgX + 8, lgY + 12, lgX + 30, lgY + 12);
        g.setColor(Color.BLACK);
        g.drawString(String.format("irradiância (%,d pontos)", pontos.size()), lgX + 36, lgY + 16);
    }

    private static String fmtY(double v) {
        return Math.abs(v) < 0.01 ? String.format("%.4f", v) : String.format("%.3f", v);
    }
}
