"""
Data Aggregator - Ham QR Verilerini Doluluk Oranına Dönüştürme

Bu modül QR sisteminden gelen ham giriş-çıkış verilerini alır ve
modelin beklediği doluluk oranı formatına dönüştürür.
"""

import pandas as pd
import os
from datetime import datetime, timedelta
from collections import defaultdict
from .tesisler import get_tesis_by_id

class DataAggregator:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        self.raw_entries_file = os.path.join(self.data_dir, "ham_qr_veri.csv")
        self.processed_file = os.path.join(self.data_dir, "gercek_ziyaretci.csv")

    def process_raw_qr_data(self, raw_data_list):
        """
        Ham QR verilerini işler ve doluluk oranlarını hesaplar

        Args:
            raw_data_list (list): Ham QR verileri
                [{"timestamp": "2025-01-01 10:00:00", "tesis_id": 1, "action": "enter/exit", "user_id": "123"}]

        Returns:
            list: İşlenmiş doluluk verileri
        """
        # Tesis bazında giriş/çıkışları grupla
        facility_data = defaultdict(lambda: {"entries": [], "exits": []})

        for record in raw_data_list:
            timestamp = datetime.fromisoformat(record["timestamp"])
            tesis_id = record["tesis_id"]
            action = record["action"]

            if action == "enter":
                facility_data[tesis_id]["entries"].append(timestamp)
            elif action == "exit":
                facility_data[tesis_id]["exits"].append(timestamp)

        # Saatlik doluluk hesapla
        processed_data = []

        for tesis_id, actions in facility_data.items():
            tesis = get_tesis_by_id(tesis_id)
            if not tesis:
                continue

            kapasite = tesis["kapasite"]

            # Tüm zaman damgalarını birleştir
            all_timestamps = sorted(actions["entries"] + actions["exits"])

            if not all_timestamps:
                continue

            # Saat başı gruplama
            hourly_data = defaultdict(lambda: {"current_count": 0, "max_count": 0})

            current_count = 0

            for ts in all_timestamps:
                hour_key = ts.replace(minute=0, second=0, microsecond=0)

                if ts in actions["entries"]:
                    current_count += 1
                elif ts in actions["exits"]:
                    current_count = max(0, current_count - 1)

                hourly_data[hour_key]["current_count"] = max(
                    hourly_data[hour_key]["current_count"],
                    current_count
                )
                hourly_data[hour_key]["max_count"] = current_count

            # Doluluk oranlarını hesapla
            for hour_ts, counts in hourly_data.items():
                doluluk_orani = (counts["max_count"] / kapasite) * 100

                processed_data.append({
                    "timestamp": hour_ts.isoformat(),
                    "tesis_id": tesis_id,
                    "saat": hour_ts.hour,
                    "gun": hour_ts.weekday() + 1,
                    "hafta_sonu": 1 if hour_ts.weekday() >= 5 else 0,
                    "resmi_tatil": self._is_official_holiday(hour_ts),
                    "etkinlik_var": 0,  # Gerçek uygulamada belirlenecek
                    "sinav_haftasi": 0,  # Akademik takvimden
                    "rezervasyon_sayisi": counts["max_count"],  # Yaklaşık rezervasyon
                    "sicaklik": 20.0,  # Weather service'den gelecek
                    "yagis_var": 0,    # Weather service'den gelecek
                    "doluluk_orani": round(doluluk_orani, 1)
                })

        return processed_data

    def _is_official_holiday(self, date):
        """Tarihin resmi tatil olup olmadığını kontrol eder"""
        tatil_gunleri = [(1,1), (4,23), (5,19), (8,30), (10,29), (11,10)]
        return 1 if (date.month, date.day) in tatil_gunleri else 0

    def aggregate_and_save(self, raw_data_list):
        """
        Ham veriyi işler ve dosyaya kaydeder

        Args:
            raw_data_list (list): Ham QR verileri

        Returns:
            dict: İşlem sonucu
        """
        try:
            # Veriyi işle
            processed_data = self.process_raw_qr_data(raw_data_list)

            if not processed_data:
                return {"status": "warning", "message": "İşlenecek veri bulunamadı"}

            # DataFrame'e dönüştür
            df = pd.DataFrame(processed_data)

            # Dosyaya kaydet (append mode)
            file_exists = os.path.exists(self.processed_file)

            df.to_csv(self.processed_file, mode='a', header=not file_exists, index=False)

            return {
                "status": "success",
                "records_processed": len(processed_data),
                "file": self.processed_file
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def get_hourly_occupancy(self, tesis_id, date):
        """
        Belirli bir tesis için belirli tarihteki saatlik doluluk verilerini döndürür

        Args:
            tesis_id (int): Tesis ID
            date (str): YYYY-MM-DD formatında tarih

        Returns:
            dict: Saatlik doluluk verileri
        """
        try:
            if not os.path.exists(self.processed_file):
                return {"error": "Gerçek veri dosyası bulunamadı"}

            df = pd.read_csv(self.processed_file)

            # Tarih ve tesis filtresi
            filtered_df = df[
                (df["tesis_id"] == tesis_id) &
                (pd.to_datetime(df["timestamp"]).dt.date == pd.to_datetime(date).date())
            ]

            hourly_data = {}
            for _, row in filtered_df.iterrows():
                hour = int(row["saat"])
                hourly_data[hour] = {
                    "doluluk_orani": row["doluluk_orani"],
                    "timestamp": row["timestamp"]
                }

            return {
                "tesis_id": tesis_id,
                "date": date,
                "hourly_occupancy": hourly_data
            }

        except Exception as e:
            return {"error": str(e)}

# Global instance
aggregator = DataAggregator()

if __name__ == "__main__":
    # Test verisi
    test_raw_data = [
        {"timestamp": "2025-01-01T10:00:00", "tesis_id": 1, "action": "enter", "user_id": "1"},
        {"timestamp": "2025-01-01T10:15:00", "tesis_id": 1, "action": "enter", "user_id": "2"},
        {"timestamp": "2025-01-01T10:30:00", "tesis_id": 1, "action": "enter", "user_id": "3"},
        {"timestamp": "2025-01-01T10:45:00", "tesis_id": 1, "action": "exit", "user_id": "1"},
        {"timestamp": "2025-01-01T11:00:00", "tesis_id": 1, "action": "enter", "user_id": "4"},
    ]

    print("Data Aggregator Test")
    result = aggregator.aggregate_and_save(test_raw_data)
    print(f"İşlem sonucu: {result}")
