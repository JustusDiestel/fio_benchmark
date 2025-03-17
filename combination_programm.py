import json
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

def parse_fio_output(json_data):
    # Extrahiere die relevanten Informationen aus dem JSON-Dokument
    read_bandwidths = []
    block_sizes = []
    numjobs = []
    iodepths = []

    def parse_block_size(block_size_str):
        """Hilfsfunktion zur Umrechnung von Blockgrößen in Bytes"""
        size, unit = int(block_size_str[:-1]), block_size_str[-1].lower()
        if unit == 'k':
            return size * 1024  # KB -> Bytes
        elif unit == 'm':
            return size * 1024 * 1024  # MB -> Bytes
        elif unit == 'g':
            return size * 1024 * 1024 * 1024  # GB -> Bytes
        else:
            return size  # Wenn keine Einheit, gehe von Bytes aus

    for entry in json_data:
        # Extrahiere die Bandbreite der Leseoperationen (bw_bytes -> bw)
        read_bw = entry["jobs"][0]["read"]["bw_bytes"]

        # Berechne Bandbreite in MB/s (bytes pro Sekunde -> MB pro Sekunde)
        read_bw_mb_s = read_bw / (1024 * 1024)

        # Extrahiere die relevanten Parameter
        block_size_str = entry["global options"]["bs"]
        numjob = int(entry["global options"]["numjobs"])
        iodepth = int(entry["global options"]["iodepth"])

        # Umwandlung der Blockgröße in Bytes
        block_size_bytes = parse_block_size(block_size_str)

        # Füge die Werte zu den Listen hinzu
        read_bandwidths.append(read_bw_mb_s)
        block_sizes.append(block_size_bytes)  # Speichere in Bytes
        numjobs.append(numjob)
        iodepths.append(iodepth)

    return np.array(read_bandwidths), np.array(block_sizes), np.array(numjobs), np.array(iodepths)

def plot_surface_per_block_size(numjobs, block_sizes, iodepths, read_bandwidths):
    unique_block_sizes = np.unique(block_sizes)
    
    for block_size in unique_block_sizes:
        # Filtern der Daten für die aktuelle Blockgröße
        idx = block_sizes == block_size
        filtered_numjobs = numjobs[idx]
        filtered_iodepths = iodepths[idx]
        filtered_bandwidths = read_bandwidths[idx]

        # Erstelle das Oberflächendiagramm (Surface Plot) für die aktuelle Blockgröße
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')

        # Erstelle ein Gitter von numjobs und iodepths
        X, Y = np.meshgrid(np.unique(filtered_numjobs), np.unique(filtered_iodepths))

        # Initialisiere Z-Werte für das Gitter (Lesegeschwindigkeit)
        Z = np.zeros_like(X)

        # Fülle Z-Werte mit den Lesegeschwindigkeiten (durchschnittliche Bandbreite) für jede Kombination von numjobs und iodepth
        for i, numjob in enumerate(np.unique(filtered_numjobs)):
            for j, iodepth in enumerate(np.unique(filtered_iodepths)):
                # Finde den entsprechenden Index für die Kombination
                idx_comb = (filtered_numjobs == numjob) & (filtered_iodepths == iodepth)
                if np.any(idx_comb):
                    Z[j, i] = np.mean(filtered_bandwidths[idx_comb])  # Mittelwert der Bandbreite für diese Kombination

        # Erstelle das Oberflächendiagramm
        surf = ax.plot_surface(X, Y, Z, cmap='viridis')

        # Achsenbeschriftungen
        ax.set_xlabel('Anzahl der Jobs (numjobs)')
        ax.set_ylabel('IO-Tiefe (iodepth)')
        ax.set_zlabel('Lesegeschwindigkeit (MB/s)')
        ax.set_title(f'Oberflächendiagramm der Lesegeschwindigkeit bei Blockgröße {block_size} Bytes')

        # Farbskala
        fig.colorbar(surf, label='Lesegeschwindigkeit (MB/s)')

        # Setze numjobs und iodepth als ganze Zahlen auf den Achsen
        ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
        ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

        # Anzeige des Plots
        plt.show()

def main():
    # Frage den Benutzer nach dem Pfad zur JSON-Datei
    file_path = input("Bitte gib den Pfad zur JSON-Datei an: ")

    # Lese das JSON-Dokument
    with open(file_path, 'r') as file:
        json_data = json.load(file)

    # Parse die FIO-Ausgabe
    read_bandwidths, block_sizes, numjobs, iodepths = parse_fio_output(json_data)

    # Plotte die Oberflächendiagramme für jede Blockgröße
    plot_surface_per_block_size(numjobs, block_sizes, iodepths, read_bandwidths)

if __name__ == "__main__":
    main()
