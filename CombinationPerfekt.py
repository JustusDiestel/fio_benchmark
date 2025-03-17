import subprocess
import itertools
import json
import os
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
from datetime import datetime

# Eingaben des Benutzers
operation = input("Welche Operation: read, write, randread, randwrite (oder all für beide): ").strip().lower()
userinput_bs = input("Gib mehrere Blocksizes ein, getrennt durch Leerzeichen: ")
userinput_numjobs = input("Gib verschiedene Numjobs-Werte ein, getrennt durch Leerzeichen: ")
userinput_iodepth = input("Gib verschiedene Iodepth-Werte ein, getrennt durch Leerzeichen: ")

bs = userinput_bs.split()
numjobs = userinput_numjobs.split()
iodepth = userinput_iodepth.split()

# Alle möglichen Kombinationen
test_combinations = list(itertools.product(bs, numjobs, iodepth))

# Ergebnisse Ordner mit Zeitstempel erstellen
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
dest_folder = f"/root/fio_benchmark/justusresults/combination_results_{timestamp}"
os.makedirs(dest_folder, exist_ok=True)

# Ergebnisse speichern
all_results = {"read": [], "write": []} if operation == "all" else {operation: []}

def run_fio(bs, numjobs, iodepth):
    result_file = f"{dest_folder}/result_{bs}_{numjobs}_{iodepth}.json"
    fio_cmd = (
        f"fio --rw={operation if operation != 'all' else 'rw'} --ioengine=sync --filesize=4m:6m --nrfiles=10 --bs={bs} "
        f"--numjobs={numjobs} --iodepth={iodepth} --direct=1 --unlink=1 "
        f"--directory=/mnt/draidBenchmark/testbereichjustus --group_reporting=1 "
        f"--time_based=1 --runtime=30s --name=test_python --output-format=json "
        f"--output={result_file}"
    )
    subprocess.run(fio_cmd, shell=True)
    return result_file

# Testdurchführung
for (bs, numjobs, iodepth) in test_combinations:
    result_file = run_fio(bs, numjobs, iodepth)
    with open(result_file, 'r') as f:
        result_data = json.load(f)
        if operation == "all":
            all_results["read"].append(result_data)
            all_results["write"].append(result_data)
        else:
            all_results[operation].append(result_data)

# Speichern aller Ergebnisse mit Zeitstempel
total_results_file = f"{dest_folder}/all_results_{operation}_{timestamp}.json"
with open(total_results_file, "w") as f:
    json.dump(all_results, f, indent=4)
print(f"Ergebnisse gespeichert in {total_results_file}")

# Verarbeitung und Visualisierung
def parse_fio_output(json_data, op):
    read_bandwidths, write_bandwidths = [], []
    block_sizes, numjobs, iodepths = [], [], []

    def parse_bs(bs_str):
        size, unit = int(bs_str[:-1]), bs_str[-1].lower()
        return size * (1024 ** {'k': 1, 'm': 2, 'g': 3}.get(unit, 0))

    for entry in json_data.get(op, []):
        job = entry["jobs"][0]  # Erstes Job-Ergebnis

        # Read & Write Bandbreite auslesen
        read_bw = job.get("read", {}).get("bw_bytes", 0) / (1024 * 1024)  # MB/s
        write_bw = job.get("write", {}).get("bw_bytes", 0) / (1024 * 1024)  # MB/s

        # FIO-Global-Optionen auslesen
        global_opts = entry.get("global options", {})
        block_size_bytes = parse_bs(global_opts.get("bs", "4k"))
        numjob = int(global_opts.get("numjobs", 1))
        iodepth = int(global_opts.get("iodepth", 1))

        read_bandwidths.append(read_bw)
        write_bandwidths.append(write_bw)
        block_sizes.append(block_size_bytes)
        numjobs.append(numjob)
        iodepths.append(iodepth)

    return (np.array(read_bandwidths), np.array(write_bandwidths), 
            np.array(block_sizes), np.array(numjobs), np.array(iodepths))

# Ergebnisse einlesen und analysieren
with open(total_results_file, 'r') as f:
    json_data = json.load(f)

if operation == "all":
    read_bw, write_bw, block_sizes, numjobs, iodepths = parse_fio_output(json_data, "read")
    _, write_bw, _, _, _ = parse_fio_output(json_data, "write")  # Write-Bandbreite aktualisieren
else:
    read_bw, write_bw, block_sizes, numjobs, iodepths = parse_fio_output(json_data, operation)

df = pd.DataFrame({
    'Block Size (Bytes)': block_sizes,
    'Num Jobs': numjobs,
    'IO Depth': iodepths,
    'Read Bandwidth (MB/s)': read_bw if read_bw.size > 0 else None,
    'Write Bandwidth (MB/s)': write_bw if write_bw.size > 0 else None
})

print(df)

# 3D-Plot
def plot_surface(numjobs, block_sizes, iodepths, read_bandwidths, write_bandwidths):
    unique_block_sizes = np.unique(block_sizes)

    for block_size in unique_block_sizes:
        idx = block_sizes == block_size
        X_vals, Y_vals = np.unique(numjobs[idx]), np.unique(iodepths[idx])

        if len(X_vals) == 0 or len(Y_vals) == 0:
            continue

        X, Y = np.meshgrid(X_vals, Y_vals)
        Z_read = np.zeros_like(X, dtype=float)
        Z_write = np.zeros_like(X, dtype=float)

        for i, n in enumerate(X_vals):
            for j, d in enumerate(Y_vals):
                match = (numjobs == n) & (iodepths == d) & (block_sizes == block_size)
                
                # Falls Daten vorhanden sind, Mittelwert berechnen, sonst 0 setzen
                if read_bandwidths.size > 0 and np.any(match):
                    Z_read[j, i] = np.mean(read_bandwidths[match])
                else:
                    Z_read[j, i] = 0
                
                if write_bandwidths.size > 0 and np.any(match):
                    Z_write[j, i] = np.mean(write_bandwidths[match])
                else:
                    Z_write[j, i] = 0

        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')

        ax.plot_surface(X, Y, Z_read, cmap='Reds', alpha=0.7)
        ax.plot_surface(X, Y, Z_write, cmap='Blues', alpha=0.7)
        ax.scatter(numjobs[idx], iodepths[idx], read_bandwidths[idx], color='red', s=50, label="Read Messwerte")
        ax.scatter(numjobs[idx], iodepths[idx], write_bandwidths[idx], color='blue', s=50, label="Write Messwerte")

        ax.set_xlabel('Num Jobs')
        ax.set_ylabel('IO Depth')
        ax.set_zlabel('Bandwidth (MB/s)')
        ax.legend()

        plt.savefig(f"{dest_folder}/plot_bs_{block_size}.png", dpi=300)
        plt.close()

plot_surface(numjobs, block_sizes, iodepths, read_bw, write_bw)
