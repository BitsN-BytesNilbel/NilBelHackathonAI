"""
Data Logger - QR Kod Sisteminden Gelen Gerçek Zamanlı Verilerin Kaydedilmesi

Bu modül QR kod okuma anında tetiklenir ve aşağıdaki işlemleri gerçekleştirir:
1. Hava durumu servisini çağırır
2. Tesis bilgilerini alır
3. Zaman damgası ile birlikte veriyi kaydeder
4. Belirli aralıklarla model yeniden eğitimini tetikler
"""

import os
import csv
import time
from datetime import datetime
from .weather_service import get_weather_data
from .tesisler import get_tesis_by_id

class DataLogger:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        self.real_data_file = os.path.join(self.data_dir, "gercek_ziyaretci.csv")

        # CSV başlıkları (modelin beklediği format)
        self.headers = [
            "timestamp", "tesis_id", "saat", "gun", "hafta_sonu", "resmi_tatil",
            "etkinlik_var", "sinav_haftasi", "rezervasyon_sayisi",
            "sicaklik", "yagis_var", "doluluk_orani"
        ]

        # Dosya yoksa oluştur
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """CSV dosyasının varlığını kontrol eder, yoksa oluşturur"""
        if not os.path.exists(self.real_data_file):
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.real_data_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(self.headers)

    def log_qr_entry(self, tesis_id, qr_data=None):
        """
        QR kod okuma verisini kaydeder

        Args:
            tesis_id (int): Tesis ID
            qr_data (dict): QR verisi (opsiyonel, şimdilik mock)

        Returns:
            dict: Kaydedilen veri bilgileri
        """
        try:
            # Tesis kontrolü
            tesis = get_tesis_by_id(tesis_id)
            if not tesis:
                raise ValueError(f"Tesis {tesis_id} bulunamadı")

            # Zaman bilgilerini al
            simdi = datetime.now()
            gun = simdi.weekday() + 1  # 1-7 arası
            hafta_sonu = 1 if gun >= 6 else 0

            # Basit resmi tatil kontrolü
            tatil_gunleri = [(1,1), (4,23), (5,19), (8,30), (10,29), (11,10)]
            resmi_tatil = 1 if (simdi.month, simdi.day) in tatil_gunleri else 0

            # Hava durumu
            weather = get_weather_data()
            sicaklik = weather.get("hava_sicakligi", 20.0)
            yagis_var = weather.get("yagis_var", 0)

            # Mock veriler (QR sisteminden gelecek)
            etkinlik_var = 0  # Gerçek uygulamada QR verisinden alınacak
            sinav_haftasi = 0  # Akademik takvimden belirlenecek
            rezervasyon_sayisi = qr_data.get("rezervasyon", 0) if qr_data else 0

            # Doluluk oranı (QR sisteminden hesaplanacak)
            # Bu gerçek uygulamada gerçek zamanlı hesaplanacak
            doluluk_orani = qr_data.get("doluluk_orani", 50.0) if qr_data else 50.0

            # Veri satırı
            data_row = [
                simdi.isoformat(),  # timestamp
                tesis_id,
                simdi.hour,
                gun,
                hafta_sonu,
                resmi_tatil,
                etkinlik_var,
                sinav_haftasi,
                rezervasyon_sayisi,
                round(sicaklik, 1),
                int(yagis_var),
                round(doluluk_orani, 1)
            ]

            # CSV'ye kaydet
            with open(self.real_data_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(data_row)

            print(f"[DATA LOGGER] QR giriş kaydedildi - Tesis: {tesis['isim']}, Saat: {simdi.hour}")

            # Retraining kontrolü
            self._check_retraining_trigger()

            return {
                "status": "success",
                "tesis": tesis["isim"],
                "timestamp": simdi.isoformat(),
                "doluluk_orani": doluluk_orani
            }

        except Exception as e:
            print(f"[DATA LOGGER] Hata: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def _check_retraining_trigger(self):
        """Her 100 yeni kayıt sonrası model yeniden eğitimini tetikler"""
        try:
            # Kayıt sayısını kontrol et
            with open(self.real_data_file, 'r', encoding='utf-8') as f:
                record_count = sum(1 for line in f) - 1  # Başlık hariç

            if record_count > 0 and record_count % 100 == 0:
                print(f"[DATA LOGGER] {record_count} kayıt ulaştı - Model retraining tetikleniyor...")
                self._trigger_retraining()

        except Exception as e:
            print(f"[DATA LOGGER] Retraining kontrol hatası: {e}")

    def _trigger_retraining(self):
        """Model yeniden eğitimini çalıştırır"""
        try:
            import subprocess
            import sys

            # train_model.py'yi çalıştır
            script_path = os.path.join(os.path.dirname(__file__), "..", "ai", "train_model.py")
            result = subprocess.run([sys.executable, script_path],
                                  capture_output=True, text=True)

            if result.returncode == 0:
                print("[DATA LOGGER] Model başarıyla yeniden eğitildi")
            else:
                print(f"[DATA LOGGER] Model retraining hatası: {result.stderr}")

        except Exception as e:
            print(f"[DATA LOGGER] Retraining tetikleme hatası: {e}")

    def get_record_count(self):
        """Toplam kayıt sayısını döndürür"""
        try:
            with open(self.real_data_file, 'r', encoding='utf-8') as f:
                return sum(1 for line in f) - 1  # Başlık hariç
        except:
            return 0

# Global instance
data_logger = DataLogger()

def log_qr_entry(tesis_id, qr_data=None):
    """Kolay kullanım için global fonksiyon"""
    return data_logger.log_qr_entry(tesis_id, qr_data)

if __name__ == "__main__":
    # Test
    print("Data Logger Test")
    result = log_qr_entry(1, {"doluluk_orani": 75.5, "rezervasyon": 5})
    print(f"Sonuç: {result}")
    print(f"Toplam kayıt: {data_logger.get_record_count()}")
