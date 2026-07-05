import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

OUTPUT_DIR = "output"

DATASETS = [
    "seq.csv",
    "bin.csv",
    "bst_random.csv",
    "bst_sorted.csv",
    "bst_reverse.csv",
    "avl_random.csv",
    "avl_sorted.csv",
    "avl_reverse.csv"
]

current_index = 0


def load_data(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    df = pd.read_csv(path)

    # detecta FAIL
    df["is_fail"] = df["comparisons"].astype(str).str.contains("FAIL")

    df["n"] = pd.to_numeric(df["n"], errors="coerce")
    df["comparisons"] = pd.to_numeric(df["comparisons"], errors="coerce")
    df["time_ns"] = pd.to_numeric(df["time_ns"], errors="coerce")

    return df


def plot_dataset(filename):
    df = load_data(filename)

    ax1.clear()
    ax2.clear()

    label = filename.replace(".csv", "")

    ok = df[df["is_fail"] == False]
    fail = df[df["is_fail"] == True]

    # =========================
    # COMPARAÇÕES (scatter)
    # =========================
    ax1.scatter(ok["n"], ok["comparisons"], s=10, alpha=0.6)

    ax1.scatter(
        fail["n"],
        [0] * len(fail),
        color="red",
        s=80,  # DOBRO DO RAIO (vs normal ~10-40)
        label="FAIL"
    )

    ax1.set_title(f"{label} - Comparações")
    ax1.set_xlabel("n")
    ax1.set_ylabel("comparisons")
    ax1.legend()

    # =========================
    # TEMPO (scatter)
    # =========================
    ax2.scatter(ok["n"], ok["time_ns"], s=10, alpha=0.6)

    ax2.scatter(
        fail["n"],
        [0] * len(fail),
        color="red",
        s=80,
        label="FAIL"
    )

    ax2.set_title(f"{label} - Tempo (ns)")
    ax2.set_xlabel("n")
    ax2.set_ylabel("time_ns")
    ax2.legend()

    fig.canvas.draw_idle()


def next_dataset(event):
    global current_index
    current_index = (current_index + 1) % len(DATASETS)
    plot_dataset(DATASETS[current_index])


def prev_dataset(event):
    global current_index
    current_index = (current_index - 1) % len(DATASETS)
    plot_dataset(DATASETS[current_index])


# =========================
# FIGURA
# =========================

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
plt.subplots_adjust(bottom=0.2)

ax_prev = plt.axes([0.3, 0.05, 0.15, 0.075])
ax_next = plt.axes([0.55, 0.05, 0.15, 0.075])

btn_prev = Button(ax_prev, "Anterior")
btn_next = Button(ax_next, "Próximo")

btn_prev.on_clicked(prev_dataset)
btn_next.on_clicked(next_dataset)

plot_dataset(DATASETS[current_index])

plt.show()