import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, TextBox

OUTPUT_DIR = "output_ordenacao"

def get_all_csvs():
    if not os.path.exists(OUTPUT_DIR):
        print(f"❌ Pasta '{OUTPUT_DIR}' não encontrada!")
        return []
    csvs = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".csv")]
    print(f"✅ Encontrados {len(csvs)} arquivos CSV")
    return sorted(csvs)

DATASETS = get_all_csvs()
current_index = 0

y_mode = "fixed"          # "fixed" ou "auto"
y_max_manual = None

# ====================== CARREGAR DADOS ======================
def load_all_data():
    all_dfs = []
    for filename in DATASETS:
        path = os.path.join(OUTPUT_DIR, filename)
        df = pd.read_csv(path)

        df["is_fail"] = df["comparisons"].astype(str).str.contains("FAIL", na=False)

        df["n"] = pd.to_numeric(df["n"], errors="coerce")
        df["comparisons"] = pd.to_numeric(df["comparisons"], errors="coerce")
        df["copies"] = pd.to_numeric(df["copies"], errors="coerce")
        df["time_ns"] = pd.to_numeric(df["time_ns"], errors="coerce")

        all_dfs.append(df)
    return all_dfs

all_data = load_all_data()

# ====================== LIMITES GLOBAIS ======================
global_max_n = max((df["n"].max() for df in all_data if not df.empty), default=10000)

global_max_comp   = max((df["comparisons"].max() for df in all_data if not df.empty), default=1000)
global_max_copies = max((df["copies"].max() for df in all_data if not df.empty), default=1000)
global_max_time   = max((df["time_ns"].max() for df in all_data if not df.empty), default=1000)

def get_y_max(df, column):
    if y_max_manual is not None:
        return y_max_manual
    
    if y_mode == "auto":
        valid = df[column].dropna()
        return valid.max() * 1.08 if not valid.empty else 100
    
    # Modo fixed
    if column == "comparisons":
        gmax = global_max_comp
    elif column == "copies":
        gmax = global_max_copies
    else:  # time_ns
        gmax = global_max_time
    return gmax * 1.08


# ====================== PLOT ======================
def plot_dataset(filename):
    idx = DATASETS.index(filename)
    df = all_data[idx]

    ax1.clear()
    ax2.clear()
    ax3.clear()

    label = filename.replace(".csv", "").replace("_", " ").upper()

    ok = df[~df["is_fail"]]
    fail = df[df["is_fail"]]

    # Comparações
    ax1.scatter(ok["n"], ok["comparisons"], s=12, alpha=0.75, label="OK")
    if not fail.empty:
        ax1.scatter(fail["n"], [0]*len(fail), color="red", s=90, label="FAIL")

    ax1.set_title(f"{label}\nComparações")
    ax1.set_xlabel("n")
    ax1.set_ylabel("comparisons")
    ax1.set_xlim(0, global_max_n * 1.02)
    ax1.set_ylim(0, get_y_max(df, "comparisons"))
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Cópias
    ax2.scatter(ok["n"], ok["copies"], s=12, alpha=0.75, label="OK")
    if not fail.empty:
        ax2.scatter(fail["n"], [0]*len(fail), color="red", s=90, label="FAIL")

    ax2.set_title("Cópias")
    ax2.set_xlabel("n")
    ax2.set_ylabel("copies")
    ax2.set_xlim(0, global_max_n * 1.02)
    ax2.set_ylim(0, get_y_max(df, "copies"))
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Tempo
    ax3.scatter(ok["n"], ok["time_ns"], s=12, alpha=0.75, label="OK")
    if not fail.empty:
        ax3.scatter(fail["n"], [0]*len(fail), color="red", s=90, label="FAIL")

    ax3.set_title("Tempo (ns)")
    ax3.set_xlabel("n")
    ax3.set_ylabel("time_ns")
    ax3.set_xlim(0, global_max_n * 1.02)
    ax3.set_ylim(0, get_y_max(df, "time_ns"))
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    fig.canvas.draw_idle()

# ====================== CONTROLES ======================
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
    y_mode = "auto" if y_mode == "fixed" else "fixed"
    btn_mode.label.set_text(f"Y: {'AUTO' if y_mode == 'auto' else 'FIXO'}")
    plot_dataset(DATASETS[current_index])

def submit_ymax(text):
    global y_max_manual
    try:
        y_max_manual = float(text) if text.strip() else None
    except ValueError:
        y_max_manual = None
    plot_dataset(DATASETS[current_index])

# ====================== INTERFACE ======================
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(19, 7))
plt.subplots_adjust(bottom=0.22)

ax_prev = plt.axes([0.10, 0.06, 0.10, 0.07])
ax_next = plt.axes([0.22, 0.06, 0.10, 0.07])
ax_mode = plt.axes([0.36, 0.06, 0.15, 0.07])
ax_ymax = plt.axes([0.55, 0.06, 0.22, 0.07])

btn_prev = Button(ax_prev, "Anterior")
btn_next = Button(ax_next, "Próximo")
btn_mode = Button(ax_mode, "Y: FIXO")
text_box = TextBox(ax_ymax, "Y-max manual (Enter)", initial="")

btn_prev.on_clicked(prev_dataset)
btn_next.on_clicked(next_dataset)
btn_mode.on_clicked(toggle_y_mode)
text_box.on_submit(submit_ymax)

# ====================== INICIALIZAÇÃO ======================
if DATASETS:
    plot_dataset(DATASETS[0])
    plt.show()
else:
    print("Nenhum arquivo .csv encontrado na pasta output_ordenacao")