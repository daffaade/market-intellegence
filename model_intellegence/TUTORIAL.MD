## CONTOH PENGGUNAAN

from model_intellegence.isolation_forest import anomaly_detect

def cek_pasar_hari_ini():
    # 1. Panggil Model
    hasil = anomaly_detect(["BBCA", "BMRI"])
    
    # 2. Cek apakah ada error
    if hasil["status"] == "ERROR":
        print("Gagal:", hasil.get("error"))
        return
        
    # 3. Looping ke tiap saham untuk menampilkan anomali
    for saham, data in hasil["companies"].items():
        jumlah_anomali = len(data["anomalies"])
        jumlah_episode = len(data["episodes"])
        print(f"Saham {saham} memiliki {jumlah_anomali} titik anomali dalam {jumlah_episode} kejadian.")
        
        # 4. Ambil anomali terakhir/paling ekstrem
        for anomali in data["anomalies"]:
            print(f"  -> Tgl {anomali['date']}: {anomali['anomaly_type']} (Score: {anomali['anomaly_score']})")

if __name__ == "__main__":
    cek_pasar_hari_ini()
