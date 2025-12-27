"""
Error Tracker - Model Hata Takibi ve Performans Analizi

Bu modül yapay zekanın tahminlerini gerçek değerlerle karşılaştırır
ve model performansını izler.
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from .predict import predict_occupancy
from utils.data_aggregator import aggregator

class ErrorTracker:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        self.error_log_file = os.path.join(self.data_dir, "model_errors.json")
        self.performance_file = os.path.join(self.data_dir, "model_performance.json")

        # Hata geçmişi
        self.error_history = self._load_error_history()

    def _load_error_history(self):
        """Hata geçmişini yükler"""
        if os.path.exists(self.error_log_file):
            try:
                with open(self.error_log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    def _save_error_history(self):
        """Hata geçmişini kaydeder"""
        with open(self.error_log_file, 'w', encoding='utf-8') as f:
            json.dump(self.error_history, f, indent=2, ensure_ascii=False)

    def track_prediction_error(self, tesis_id, predicted_value, actual_value, context=None):
        """
        Tek bir tahmin hatasını kaydeder

        Args:
            tesis_id (int): Tesis ID
            predicted_value (float): Model tahmini (%)
            actual_value (float): Gerçek değer (%)
            context (dict): Ek bağlam bilgileri
        """
        error = abs(predicted_value - actual_value)
        timestamp = datetime.now().isoformat()

        error_record = {
            "timestamp": timestamp,
            "tesis_id": tesis_id,
            "predicted": round(predicted_value, 1),
            "actual": round(actual_value, 1),
            "error": round(error, 1),
            "context": context or {}
        }

        self.error_history.append(error_record)
        self._save_error_history()

        print(f"[ERROR TRACKER] Hata kaydedildi - Tesis: {tesis_id}, Tahmin: {predicted_value:.1f}%, Gerçek: {actual_value:.1f}%, Hata: {error:.1f}%")

        return error_record

    def compare_predictions_with_real_data(self, date=None):
        """
        Belirli bir tarih için tüm tahminleri gerçek verilerle karşılaştırır

        Args:
            date (str): YYYY-MM-DD formatında tarih (None ise son 24 saat)

        Returns:
            dict: Karşılaştırma sonuçları
        """
        try:
            if date is None:
                # Son 24 saat
                cutoff_date = datetime.now() - timedelta(hours=24)
                date_filter = lambda ts: datetime.fromisoformat(ts) >= cutoff_date
            else:
                # Belirli tarih
                target_date = pd.to_datetime(date).date()
                date_filter = lambda ts: pd.to_datetime(ts).date() == target_date

            # Gerçek veriyi al
            real_data_file = os.path.join(self.data_dir, "gercek_ziyaretci.csv")
            if not os.path.exists(real_data_file):
                return {"error": "Gerçek veri dosyası bulunamadı"}

            real_df = pd.read_csv(real_data_file)

            # Tarih filtresi
            real_df["datetime"] = pd.to_datetime(real_df["timestamp"])
            filtered_real = real_df[real_df["datetime"].apply(lambda ts: date_filter(ts.isoformat()))]

            if filtered_real.empty:
                return {"error": "Belirtilen tarih için gerçek veri bulunamadı"}

            comparison_results = []

            for _, real_record in filtered_real.iterrows():
                tesis_id = int(real_record["tesis_id"])
                saat = int(real_record["saat"])
                actual_occupancy = real_record["doluluk_orani"]

                # Model tahmini al (simüle edilmiş tarih ile)
                # Gerçek uygulamada tarih bilgisi kullanılacak
                try:
                    prediction = predict_occupancy(tesis_id)
                    predicted_value = float(prediction["doluluk"].replace('%', ''))

                    # Hata kaydı
                    error_record = self.track_prediction_error(
                        tesis_id,
                        predicted_value,
                        actual_occupancy,
                        {
                            "saat": saat,
                            "timestamp": real_record["timestamp"]
                        }
                    )

                    comparison_results.append({
                        "tesis_id": tesis_id,
                        "saat": saat,
                        "predicted": predicted_value,
                        "actual": actual_occupancy,
                        "error": error_record["error"]
                    })

                except Exception as e:
                    print(f"[ERROR TRACKER] Tahmin hatası - Tesis {tesis_id}: {e}")
                    continue

            return {
                "status": "success",
                "date": date or "last_24h",
                "total_comparisons": len(comparison_results),
                "results": comparison_results,
                "summary": self._calculate_summary_stats(comparison_results)
            }

        except Exception as e:
            return {"error": str(e)}

    def _calculate_summary_stats(self, comparison_results):
        """Karşılaştırma sonuçlarından özet istatistikler hesaplar"""
        if not comparison_results:
            return {}

        predicted = [r["predicted"] for r in comparison_results]
        actual = [r["actual"] for r in comparison_results]

        mae = mean_absolute_error(actual, predicted)
        mse = mean_squared_error(actual, predicted)
        rmse = np.sqrt(mse)
        r2 = r2_score(actual, predicted)

        return {
            "mae": round(mae, 2),  # Mean Absolute Error
            "rmse": round(rmse, 2),  # Root Mean Squared Error
            "r2_score": round(r2, 4),  # R² Score
            "accuracy_percentage": round((1 - mae/100) * 100, 1)  # Yaklaşık doğruluk %
        }

    def get_error_trends(self, days=7):
        """
        Son N günün hata trendlerini döndürür

        Args:
            days (int): Kaç günlük trend

        Returns:
            dict: Hata trendleri
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            recent_errors = [
                error for error in self.error_history
                if datetime.fromisoformat(error["timestamp"]) >= cutoff_date
            ]

            if not recent_errors:
                return {"error": f"Son {days} günde hata kaydı bulunamadı"}

            # Günlük gruplama
            daily_errors = {}
            for error in recent_errors:
                date = pd.to_datetime(error["timestamp"]).date().isoformat()
                if date not in daily_errors:
                    daily_errors[date] = []
                daily_errors[date].append(error["error"])

            # Günlük ortalama hatalar
            daily_avg_errors = {
                date: round(np.mean(errors), 2)
                for date, errors in daily_errors.items()
            }

            return {
                "period_days": days,
                "total_errors": len(recent_errors),
                "daily_average_errors": daily_avg_errors,
                "overall_average_error": round(np.mean([e["error"] for e in recent_errors]), 2)
            }

        except Exception as e:
            return {"error": str(e)}

    def generate_performance_report(self):
        """Genel performans raporunu oluşturur"""
        try:
            # Son 30 günün verilerini al
            trends_30d = self.get_error_trends(days=30)

            if "error" in trends_30d:
                return {"error": "Yeterli veri yok"}

            # Tüm hata geçmişini analiz et
            all_errors = [e["error"] for e in self.error_history[-1000:]]  # Son 1000 hata

            report = {
                "generated_at": datetime.now().isoformat(),
                "total_predictions": len(self.error_history),
                "recent_performance": {
                    "30_day_trend": trends_30d,
                    "accuracy_assessment": self._assess_accuracy(trends_30d["overall_average_error"])
                },
                "overall_stats": {
                    "average_error": round(np.mean(all_errors), 2) if all_errors else 0,
                    "median_error": round(np.median(all_errors), 2) if all_errors else 0,
                    "max_error": round(np.max(all_errors), 2) if all_errors else 0,
                    "min_error": round(np.min(all_errors), 2) if all_errors else 0
                },
                "recommendations": self._generate_recommendations(trends_30d["overall_average_error"])
            }

            # Performans dosyasını kaydet
            with open(self.performance_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            return report

        except Exception as e:
            return {"error": str(e)}

    def _assess_accuracy(self, avg_error):
        """Ortalama hataya göre doğruluk değerlendirmesi"""
        if avg_error <= 5:
            return "Çok Yüksek (Mükemmel)"
        elif avg_error <= 10:
            return "Yüksek (Çok İyi)"
        elif avg_error <= 15:
            return "Orta-Yüksek (İyi)"
        elif avg_error <= 20:
            return "Orta (Kabul Edilebilir)"
        else:
            return "Düşük (İyileştirme Gerekli)"

    def _generate_recommendations(self, avg_error):
        """Hata oranına göre öneriler üretir"""
        recommendations = []

        if avg_error > 20:
            recommendations.extend([
                "Daha fazla gerçek veri topla",
                "Model hiperparametrelerini optimize et",
                "Ek özellikler ekle (hava durumu, etkinlikler vb.)"
            ])
        elif avg_error > 15:
            recommendations.extend([
                "Gerçek zamanlı veri akışını artır",
                "Feature engineering iyileştir",
                "Model ensemble yöntemlerini dene"
            ])
        elif avg_error > 10:
            recommendations.extend([
                "Mevcut veri kalitesini koru",
                "Düzenli model güncellemelerini sürdür",
                "Aykırı değerleri filtrele"
            ])
        else:
            recommendations.append("Model performansı çok iyi, mevcut stratejiyi sürdür")

        return recommendations

# Global instance
error_tracker = ErrorTracker()

def track_error(tesis_id, predicted, actual, context=None):
    """Kolay kullanım için global fonksiyon"""
    return error_tracker.track_prediction_error(tesis_id, predicted, actual, context)

if __name__ == "__main__":
    # Test
    print("Error Tracker Test")

    # Örnek hata kaydı
    error_tracker.track_prediction_error(1, 65.0, 70.0, {"saat": 14, "gun": 3})

    # Performans raporu
    report = error_tracker.generate_performance_report()
    print("Performans Raporu:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
