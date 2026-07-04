import csv

# Endereço do arquivo CSV
file_path = "solarradiation.csv"

row_count = 0
headers = []
sample_rows = []

with open(file_path, mode="r", encoding="utf-8", newline="") as csv_file:
    reader = csv.reader(csv_file)

    # Lê cabeçalho
    headers = next(reader)

    print("=== CABEÇALHOS ===")
    for i, header in enumerate(headers):
        if header.strip() == "":
            print(f"[{i}] (ID / vazio)")
        else:
            print(f"[{i}] {header}")

    print("\n=== AMOSTRA (primeiras 5 linhas) ===")

    # Lê linhas
    for row in reader:
        if row_count < 5:
            sample_rows.append(row)

        row_count += 1

# Mostra amostra
for i, row in enumerate(sample_rows):
    print(f"\nLinha {i + 1}:")
    for h, v in zip(headers, row):
        label = h if h.strip() != "" else "ID"
        print(f"  {label}: {v}")

# Estatísticas do dataset
print("\n=== ESTATÍSTICAS DO DATASET ===")
print(f"Total de linhas: {row_count}")
print(f"Total de colunas: {len(headers)}")

# estimativa de tamanho em memória aproximado
avg_row_size = sum(len(h) for h in headers) * 2
estimated_memory_kb = (row_count * avg_row_size) / 1024

print(f"Tamanho estimado em memória (bem aproximado): {estimated_memory_kb:.2f} KB")