import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, TextBox

OUTPUT_DIR = "output"

DATASETS = [
    "seq_random.csv",
    "seq_sorted.csv",
    "seq_reverse.csv",
    "bin.csv",

    "abb_random.csv",
    "abb_sorted.csv",
    "abb_reverse.csv",

    "avl_random.csv",
    "avl_sorted.csv",
    "avl_reverse.csv"
]

current_index = 0
y_mode = "fixed"          # "fixed" ou "auto"
y_max_manual = None       # Se None, usa o máximo calculado

# ==========================================================
# CARREGAR TODOS OS DADOS
# ==========================================================

def load_all_data():
    all_dfs = []

    for filename in DATASETS:

        path = os.path.join(OUTPUT_DIR, filename)

        if not os.path.exists(path):
            print(f"Aviso: {filename} não encontrado.")
            all_dfs.append(pd.DataFrame(
                columns=["n", "comparisons", "time_ns", "is_fail"]
            ))
            continue

        df = pd.read_csv(path)

        df["is_fail"] = (
            df["comparisons"]
            .astype(str)
            .str.upper()
            .str.contains("FAIL")
        )

        df["n"] = pd.to_numeric(df["n"], errors="coerce")
        df["comparisons"] = pd.to_numeric(df["comparisons"], errors="coerce")
        df["time_ns"] = pd.to_numeric(df["time_ns"], errors="coerce")

        all_dfs.append(df)

    return all_dfs


all_data = load_all_data()

# ==========================================================
# LIMITES GLOBAIS
# ==========================================================

global_max_n = max(
    (df["n"].max() for df in all_data if not df.empty),
    default=1000
)

global_max_comp = max(
    (df["comparisons"].max() for df in all_data if not df.empty),
    default=1000
)

global_max_time = max(
    (df["time_ns"].max() for df in all_data if not df.empty),
    default=1000
)


def get_y_max(df, column):

    if y_max_manual is not None:
        return y_max_manual

    if y_mode == "auto":

        if df.empty:
            return 100

        m = df[column].max()

        if pd.isna(m):
            return 100

        return m * 1.05

    # modo fixo
    if column == "comparisons":
        return global_max_comp * 1.05
    else:
        return global_max_time * 1.05


# ==========================================================
# PLOT
# ==========================================================

def plot_dataset(filename):

    idx = DATASETS.index(filename)
    df = all_data[idx]

    ax1.clear()
    ax2.clear()

    label = filename.replace(".csv", "").upper()

    ok = df[~df["is_fail"]]
    fail = df[df["is_fail"]]

    # ---------------- COMPARAÇÕES ----------------

    if not ok.empty:
        ax1.scatter(
            ok["n"],
            ok["comparisons"],
            s=10,
            alpha=0.7,
            label="OK"
        )

    if not fail.empty:
        ax1.scatter(
            fail["n"],
            [0] * len(fail),
            color="red",
            s=80,
            marker="x",
            label="FAIL"
        )

    ax1.set_title(f"{label} - Comparações")
    ax1.set_xlabel("n")
    ax1.set_ylabel("Comparações")

    ax1.set_xlim(0, global_max_n * 1.02)
    ax1.set_ylim(0, get_y_max(df, "comparisons"))

    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # ---------------- TEMPO ----------------

    if not ok.empty:
        ax2.scatter(
            ok["n"],
            ok["time_ns"],
            s=10,
            alpha=0.7,
            label="OK"
        )

    if not fail.empty:
        ax2.scatter(
            fail["n"],
            [0] * len(fail),
            color="red",
            s=80,
            marker="x",
            label="FAIL"
        )

    ax2.set_title(f"{label} - Tempo (ns)")
    ax2.set_xlabel("n")
    ax2.set_ylabel("Tempo (ns)")

    ax2.set_xlim(0, global_max_n * 1.02)
    ax2.set_ylim(0, get_y_max(df, "time_ns"))

    ax2.grid(True, alpha=0.3)
    ax2.legend()

    fig.suptitle(filename, fontsize=16)

    fig.canvas.draw_idle()


# ==========================================================
# BOTÕES
# ==========================================================

def next_dataset(event):
    global current_index
    current_index = (current_index + 1) % len(DATASETS)
    plot_dataset(DATASETS[current_index])


def prev_dataset(event):
    global current_index
    current_index = (current_index - 1) % len(DATASETS)
    plot_dataset(DATASETS[current_index])


def toggle_y_mode(event):
    global y_mode

    if y_mode == "fixed":
        y_mode = "auto"
        btn_mode.label.set_text("Y: AUTO")
    else:
        y_mode = "fixed"
        btn_mode.label.set_text("Y: FIXO")

    plot_dataset(DATASETS[current_index])


def submit_ymax(text):
    global y_max_manual

    text = text.strip()

    if text == "":
        y_max_manual = None
    else:
        try:
            y_max_manual = float(text)
        except ValueError:
            y_max_manual = None

    plot_dataset(DATASETS[current_index])


# ==========================================================
# FIGURA
# ==========================================================

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))

plt.subplots_adjust(bottom=0.28)

# ---------------- Botões ----------------

ax_prev = plt.axes([0.15, 0.05, 0.12, 0.075])
ax_next = plt.axes([0.28, 0.05, 0.12, 0.075])
ax_mode = plt.axes([0.45, 0.05, 0.18, 0.075])

btn_prev = Button(ax_prev, "Anterior")
btn_next = Button(ax_next, "Próximo")
btn_mode = Button(ax_mode, "Y: FIXO")

btn_prev.on_clicked(prev_dataset)
btn_next.on_clicked(next_dataset)
btn_mode.on_clicked(toggle_y_mode)

# ---------------- Caixa de texto ----------------

ax_ymax = plt.axes([0.70, 0.05, 0.18, 0.075])

text_box = TextBox(
    ax_ymax,
    "Y-max manual\n(Enter)",
    initial=""
)

text_box.on_submit(submit_ymax)

# ==========================================================
# PLOT INICIAL
# ==========================================================

plot_dataset(DATASETS[current_index])

plt.show()