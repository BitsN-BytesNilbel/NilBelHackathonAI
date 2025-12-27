"""
Akıllı Sıralama Sistemi - Yapay Zeka Destekli Tesis Önerisi

Bu modül:
- Doluluk tahminlerine göre tesisleri akıllı sıralar
- Kullanıcı tercihlerine göre kişiselleştirilmiş öneriler sunar
- Belediye için dengeli doluluk dağılımı sağlar
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import random

# Yolları ayarla
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ai.predict import predict_occupancy
from utils.tesisler import TESISLER, get_tesis_by_id
from utils.events import event_manager

class SmartRanking:
    def __init__(self):
        self.weights = {
            "doluluk_orani": 0.4,      # En önemli faktör
            "mesafe": 0.2,             # Kullanıcı konumu (şimdilik rastgele)
            "tesis_turu": 0.15,       # Kullanıcı tercihleri
            "etkinlik": 0.15,         # Etkinlik etkisi
            "puan": 0.1               # Genel memnuniyet puanı
        }

    def rank_facilities(self,
                        user_location: Tuple[float, float] = None,
                        preferred_types: List[str] = None,
                        current_time: datetime = None,
                        top_n: int = 5) -> List[Dict]:
        """
        Tesisleri akıllı sıralayarak öneri listesi oluştur

        Args:
            user_location: (lat, lon) tuple
            preferred_types: Tercih edilen tesis türleri
            current_time: Geçerli zaman
            top_n: Kaç tesis önerilsin

        Returns:
            Sıralanmış tesis listesi
        """
        if current_time is None:
            current_time = datetime.now()

        facility_scores = []

        for tesis in TESISLER:
            try:
                # Doluluk tahmini al
                prediction = predict_occupancy(tesis["tesis_id"])
                doluluk_orani = float(prediction["doluluk"].replace('%', ''))

                # Faktörleri hesapla
                factors = self._calculate_factors(
                    tesis, doluluk_orani, user_location,
                    preferred_types, current_time
                )

                # Toplam skor hesapla
                total_score = sum(
                    factors[factor] * self.weights[factor]
                    for factor in self.weights.keys()
                )

                facility_scores.append({
                    "tesis": tesis,
                    "prediction": prediction,
                    "factors": factors,
                    "total_score": total_score,
                    "rank_reason": self._generate_rank_reason(factors)
                })

            except Exception as e:
                print(f"Tesis {tesis['tesis_id']} sıralama hatası: {e}")
                continue

        # Skora göre sırala (düşük skor = daha iyi öneri)
        ranked = sorted(facility_scores, key=lambda x: x["total_score"])

        return ranked[:top_n]

    def _calculate_factors(self, tesis: Dict, doluluk_orani: float,
                          user_location: Tuple[float, float],
                          preferred_types: List[str],
                          current_time: datetime) -> Dict:
        """Farklı sıralama faktörlerini hesapla"""

        factors = {}

        # 1. Doluluk faktörü (düşük doluluk = yüksek skor)
        factors["doluluk_orani"] = doluluk_orani / 100.0  # 0-1 arası

        # 2. Mesafe faktörü (şimdilik rastgele, gerçek uygulamada GPS)
        if user_location:
            # Bursa merkez koordinatları
            bursa_center = (40.1885, 29.0610)
            distance = self._calculate_distance(user_location, bursa_center)
            factors["mesafe"] = min(distance / 10.0, 1.0)  # Max 10km
        else:
            factors["mesafe"] = random.uniform(0.1, 0.9)

        # 3. Tesis türü tercihi
        if preferred_types and tesis["tesis_tipi"] in preferred_types:
            factors["tesis_turu"] = 0.0  # Tercih edilen tür = yüksek öncelik
        else:
            factors["tesis_turu"] = 0.5  # Nötr

        # 4. Etkinlik etkisi
        today_str = current_time.strftime("%Y-%m-%d")
        event_impact = event_manager.get_event_impact(tesis["tesis_id"], today_str)
        factors["etkinlik"] = event_impact

        # 5. Genel memnuniyet puanı (şimdilik rastgele, gerçek uygulamada gerçek veriler)
        factors["puan"] = random.uniform(0.3, 0.9)

        return factors

    def _calculate_distance(self, point1: Tuple[float, float],
                           point2: Tuple[float, float]) -> float:
        """İki koordinat arası mesafeyi hesapla (km)"""
        # Basit Haversine formülü
        from math import radians, sin, cos, sqrt, atan2

        lat1, lon1 = point1
        lat2, lon2 = point2

        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)

        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        # Dünya yarıçapı (km)
        R = 6371.0
        return R * c

    def _generate_rank_reason(self, factors: Dict) -> str:
        """Sıralama nedenini açıklamalı olarak döndür"""
        reasons = []

        if factors["doluluk_orani"] < 0.3:
            reasons.append("düşük doluluk oranı")
        elif factors["doluluk_orani"] > 0.8:
            reasons.append("yüksek doluluk oranı")

        if factors["mesafe"] < 0.3:
            reasons.append("yakın konum")
        elif factors["mesafe"] > 0.7:
            reasons.append("uzak konum")

        if factors["etkinlik"] > 0.2:
            reasons.append("etkinlik etkisi")

        if factors["puan"] > 0.8:
            reasons.append("yüksek memnuniyet puanı")

        return ", ".join(reasons) if reasons else "genel değerlendirme"

    def get_load_balancing_recommendations(self) -> List[Dict]:
        """Belediye için yük dengeleme önerileri"""
        all_predictions = []

        # Tüm tesisler için tahmin al
        for tesis in TESISLER:
            try:
                prediction = predict_occupancy(tesis["tesis_id"])
                doluluk = float(prediction["doluluk"].replace('%', ''))

                all_predictions.append({
                    "tesis": tesis,
                    "doluluk": doluluk,
                    "kapasite": tesis["kapasite"],
                    "kullanilan": (doluluk / 100) * tesis["kapasite"]
                })
            except:
                continue

        # Doluluk oranına göre sırala
        sorted_by_usage = sorted(all_predictions, key=lambda x: x["doluluk"], reverse=True)

        recommendations = []

        # Yüksek doluluklu tesisler için öneriler
        high_usage = [p for p in sorted_by_usage if p["doluluk"] > 80]
        for facility in high_usage[:3]:  # İlk 3'ü öner
            recommendations.append({
                "type": "warning",
                "tesis": facility["tesis"]["isim"],
                "message": f"Yüksek doluluk ({facility['doluluk']:.0f}%) - Yönlendirme önerilir",
                "action": "Alternatif tesis önerileri aktif et"
            })

        # Düşük doluluklu tesisler için öneriler
        low_usage = [p for p in sorted_by_usage if p["doluluk"] < 40]
        for facility in low_usage[:3]:  # İlk 3'ü öner
            recommendations.append({
                "type": "info",
                "tesis": facility["tesis"]["isim"],
                "message": f"Düşük doluluk ({facility['doluluk']:.0f}%) - Promosyon önerilir",
                "action": "Etkinlik veya kampanya düzenle"
            })

        return recommendations

# Global instance
smart_ranking = SmartRanking()

def get_smart_ranking(user_location=None, preferred_types=None, top_n=5):
    """Kolay kullanım için global fonksiyon"""
    return smart_ranking.rank_facilities(user_location, preferred_types, None, top_n)

if __name__ == "__main__":
    print("Akıllı Sıralama Sistemi Test")

    # Akıllı sıralama testi
    recommendations = smart_ranking.rank_facilities(top_n=3)
    print("\n--- Akıllı Öneriler ---")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['tesis']['isim']} - Doluluk: {rec['prediction']['doluluk']} - Sebep: {rec['rank_reason']}")

    # Yük dengeleme önerileri
    balancing = smart_ranking.get_load_balancing_recommendations()
    print(f"\n--- Yük Dengeleme Önerileri ({len(balancing)}) ---")
    for rec in balancing[:3]:
        print(f"{rec['type'].upper()}: {rec['tesis']} - {rec['message']}")
