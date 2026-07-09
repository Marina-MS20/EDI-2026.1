// registro do solarradiation.csv - a chave é o id da primeira coluna,
// a mesma que os benchmarks usaram. o resto dos campos fica como texto
// mesmo, só pra exibir igual ao arquivo.
public class Registro {

    public long id;
    public String date;
    public String minWavelength;
    public String maxWavelength;
    public String instrumentMode;
    public String dataVersion;
    public String irradiance;
    public String irradianceUncertainty;
    public String quality;

    public static final String[] COLUNAS = {
            "ID", "date", "MIN_WAVELENGTH", "MAX_WAVELENGTH", "INSTRUMENT_MODE",
            "DATA_VERSION", "IRRADIANCE", "IRRADIANCE_UNCERTAINTY", "QUALITY"
    };

    public Registro(long id, String date, String minWavelength, String maxWavelength,
                    String instrumentMode, String dataVersion, String irradiance,
                    String irradianceUncertainty, String quality) {
        this.id = id;
        this.date = date;
        this.minWavelength = minWavelength;
        this.maxWavelength = maxWavelength;
        this.instrumentMode = instrumentMode;
        this.dataVersion = dataVersion;
        this.irradiance = irradiance;
        this.irradianceUncertainty = irradianceUncertainty;
        this.quality = quality;
    }

    public static Registro fromCsv(String line) {
        String[] v = line.split(",", -1);
        if (v.length == 0 || v[0].isEmpty()) return null;
        long id = Long.parseLong(v[0]);
        return new Registro(id,
                col(v, 1), col(v, 2), col(v, 3), col(v, 4),
                col(v, 5), col(v, 6), col(v, 7), col(v, 8));
    }

    private static String col(String[] v, int i) {
        return i < v.length ? v[i] : "";
    }

    public Object[] toRow() {
        return new Object[]{ id, date, minWavelength, maxWavelength, instrumentMode,
                dataVersion, irradiance, irradianceUncertainty, quality };
    }
}
