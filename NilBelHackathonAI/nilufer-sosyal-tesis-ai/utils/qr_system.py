"""
QR Code Entry System - Gerçek Zamanlı Giriş Takibi

Bu modül:
- QR kod tarama verilerini yönetir
- Günlük giriş sayılarını takip eder
- Gece yarısında otomatik reset yapar
- CSV dosyası oluşturur
"""

import os
import json
import csv
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import time

class QRSystem:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        self.daily_logs_dir = os.path.join(self.data_dir, "daily_logs")
        self.session_file = os.path.join(self.data_dir, "current_session.json")

        # Klasörleri oluştur
        os.makedirs(self.daily_logs_dir, exist_ok=True)

        # Günlük giriş sayacı
        self.daily_counter = defaultdict(int)
        self.current_date = datetime.now().date()

        # Session'ı yükle
        self.load_session()

        # Otomatik reset scheduler'ı başlat
        self.start_scheduler()

    def load_session(self):
        """Mevcut session'ı yükle"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.daily_counter = defaultdict(int, data.get('counter', {}))
                    saved_date = data.get('date')
                    if saved_date != str(self.current_date):
                        self.reset_daily_data()
        except Exception as e:
            print(f"Session yükleme hatası: {e}")

    def save_session(self):
        """Session'ı kaydet"""
        try:
            data = {
                'date': str(self.current_date),
                'counter': dict(self.daily_counter)
            }
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Session kaydetme hatası: {e}")

    def log_qr_scan(self, tesis_id: int, qr_data: str = None) -> dict:
        """
        QR kod tarama verisini kaydeder

        Args:
            tesis_id (int): Tesis ID
            qr_data (str): QR kod verisi

        Returns:
            dict: İşlem sonucu
        """
        try:
            # Tesis kontrolü
            from .tesisler import get_tesis_by_id
            tesis = get_tesis_by_id(tesis_id)
            if not tesis:
                return {"status": "error", "message": f"Tesis {tesis_id} bulunamadı"}

            # Giriş sayısını artır
            self.daily_counter[tesis_id] += 1

            # Session'ı kaydet
            self.save_session()

            # Detaylı log oluştur
            timestamp = datetime.now().isoformat()
            log_entry = {
                "timestamp": timestamp,
                "tesis_id": tesis_id,
                "tesis_adi": tesis["isim"],
                "qr_data": qr_data or f"SCAN-{int(time.time())}",
                "daily_count": self.daily_counter[tesis_id]
            }

            # Günlük log dosyasına kaydet
            self.save_scan_log(log_entry)

            return {
                "status": "success",
                "tesis_adi": tesis["isim"],
                "total_entries_today": self.daily_counter[tesis_id],
                "timestamp": timestamp
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def save_scan_log(self, log_entry: dict):
        """Tarama logunu dosyaya kaydeder"""
        try:
            log_file = os.path.join(self.daily_logs_dir, f"scan_log_{self.current_date}.json")

            # Mevcut logları oku
            logs = []
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)

            # Yeni logu ekle
            logs.append(log_entry)

            # Kaydet
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Scan log kaydetme hatası: {e}")

    def create_daily_csv(self):
        """
        Günün sonunda CSV dosyası oluşturur
        """
        try:
            from .weather_service import get_weather_data
            from .events import event_manager

            csv_filename = f"{self.current_date}.csv"
            csv_path = os.path.join(self.daily_logs_dir, csv_filename)

            weather = get_weather_data()

            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'date', 'tesis_id', 'total_people_entered',
                    'temperature', 'rain', 'event_status',
                    'weekend', 'holiday'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                # Her tesis için veri yaz
                for tesis_id in range(1, 13):  # 1-12 arası tesisler
                    event_status = event_manager.get_event_impact(tesis_id, str(self.current_date))

                    writer.writerow({
                        'date': str(self.current_date),
                        'tesis_id': tesis_id,
                        'total_people_entered': self.daily_counter.get(tesis_id, 0),
                        'temperature': weather.get('hava_sicakligi', 20.0),
                        'rain': weather.get('yagis_var', 0),
                        'event_status': int(event_status > 0),
                        'weekend': int(self.current_date.weekday() >= 5),
                        'holiday': int(self.is_official_holiday(self.current_date))
                    })

            print(f"📄 Günlük CSV oluşturuldu: {csv_filename}")
            return csv_path

        except Exception as e:
            print(f"CSV oluşturma hatası: {e}")
            return None

    def reset_daily_data(self):
        """Günlük veriyi sıfırlar ve CSV oluşturur"""
        print(f"🔄 Günlük reset: {self.current_date}")

        # Önce CSV oluştur
        self.create_daily_csv()

        # Sayacı sıfırla
        self.daily_counter.clear()
        self.current_date = datetime.now().date()

        # Session'ı kaydet
        self.save_session()

        print("✅ Günlük veri reset tamamlandı")

    def is_official_holiday(self, date):
        """Tarihin resmi tatil olup olmadığını kontrol eder"""
        tatil_gunleri = [(1,1), (4,23), (5,19), (8,30), (10,29), (11,10)]
        return (date.month, date.day) in tatil_gunleri

    def get_daily_stats(self):
        """Günlük istatistikleri döndürür"""
        return {
            "date": str(self.current_date),
            "total_entries": sum(self.daily_counter.values()),
            "facility_breakdown": dict(self.daily_counter),
            "most_popular_facility": max(self.daily_counter, key=self.daily_counter.get) if self.daily_counter else None
        }

    def start_scheduler(self):
        """Otomatik günlük reset scheduler'ı başlatır"""
        def daily_reset_job():
            while True:
                now = datetime.now()
                # Gece yarısını bekle
                if now.hour == 0 and now.minute == 0:
                    self.reset_daily_data()
                    time.sleep(60)  # 1 dakika bekle
                time.sleep(30)  # 30 saniyede bir kontrol

        # Daemon thread olarak başlat
        reset_thread = threading.Thread(target=daily_reset_job, daemon=True)
        reset_thread.start()

# Global instance
qr_system = QRSystem()

def log_qr_scan(tesis_id, qr_data=None):
    """Kolay kullanım için global fonksiyon"""
    return qr_system.log_qr_scan(tesis_id, qr_data)

if __name__ == "__main__":
    print("QR System Test")
    result = qr_system.log_qr_scan(1, "TEST-QR-123")
    print(f"QR Log Sonucu: {result}")

    stats = qr_system.get_daily_stats()
    print(f"Günlük İstatistikler: {stats}")
