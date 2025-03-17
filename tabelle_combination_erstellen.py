import json
import pandas as pd
import os

# Funktion zum Extrahieren relevanter Daten aus dem JSON
def extract_data(json_data):
    data = []

    # Falls die JSON-Daten keine Liste sind, in eine Liste umwandeln
    if isinstance(json_data, dict):
        json_data = [json_data]  # Umwandlung in eine Liste

    for entry in json_data:
        global_options = entry.get("global options", {})
        jobs = entry.get("jobs", [])[0]

        read_bw = jobs["read"].get("bw_bytes", 0) / (1024 * 1024)  # in MB/s
        read_bw = round(read_bw, 2)
        write_bw = jobs["write"].get("bw_bytes", 0) / (1024 * 1024)  # in MB/s
        write_bw = round(write_bw, 2)

        # Extrahiere relevante Parameter aus dem FIO-Befehl
        row = {
            "block_size": global_options.get("bs", "unknown"),
            "numjobs": global_options.get("numjobs", "unknown"),
            "iodepth": global_options.get("iodepth", "unknown"),
            "nrfiles": global_options.get("nrfiles", "unknown"),
            "filesize": global_options.get("filesize", "unknown"),
            "ioengine": global_options.get("ioengine", "unknown"),
            "read_bandwidth_MB_s": read_bw,
            "write_bandwidth_MB_s": write_bw
        }

        data.append(row)

    return data

# Hauptfunktion zum Erstellen der Tabelle
def main():
    file_path = input("Bitte gib den Pfad zur JSON-Datei an: ")

    with open(file_path, 'r') as file:
        json_data = json.load(file)

    data = extract_data(json_data)

    # Erstellen eines DataFrames für eine saubere tabellarische Darstellung
    df = pd.DataFrame(data)
    print(df)

    # Erstellen des Ausgabepfads im gleichen Ordner und mit angehängtem _result
    dir_name, base_name = os.path.split(file_path)
    output_file = os.path.join(dir_name, f"{os.path.splitext(base_name)[0]}_result.csv")

    # Tabelle in die CSV-Datei speichern
    df.to_csv(output_file, index=False)
    print(f"Tabelle gespeichert unter: {output_file}")

if __name__ == "__main__":
    main()

