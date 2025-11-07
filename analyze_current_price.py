from src.data.collector import StockDataCollector
import pandas as pd
from datetime import datetime, timedelta

collector = StockDataCollector()

# 최근 3년 데이터 수집
tqqq = collector.collect_ohlcv('TQQQ', '2022-01-01', '2025-11-07')
qqq = collector.collect_ohlcv('QQQ', '2022-01-01', '2025-11-07')
qqqi = collector.collect_ohlcv('QQQI', '2024-01-01', '2025-11-07')

print("=" * 80)
print("현재 가격 수준 분석 (고점 매수 리스크)")
print("=" * 80)
print()

# 현재가 (최근 데이터)
current_tqqq = tqqq['Close'].iloc[-1]
current_qqq = qqq['Close'].iloc[-1]
current_qqqi = qqqi['Close'].iloc[-1]

# 역사적 최고가
max_tqqq = tqqq['Close'].max()
max_qqq = qqq['Close'].max()
max_qqqi = qqqi['Close'].max()

# 최고가 날짜
max_tqqq_date = tqqq['Close'].idxmax()
max_qqq_date = qqq['Close'].idxmax()
max_qqqi_date = qqqi['Close'].idxmax()

print(f"### TQQQ (3배 레버리지)")
print(f"  현재가: ${current_tqqq:.2f}")
print(f"  최고가: ${max_tqqq:.2f} ({max_tqqq_date.strftime('%Y-%m-%d')})")
print(f"  고점 대비: {(current_tqqq / max_tqqq - 1) * 100:+.2f}%")
if (current_tqqq / max_tqqq) > 0.95:
    print(f"  ⚠️  고점 근처! (95% 이상)")
elif (current_tqqq / max_tqqq) > 0.90:
    print(f"  ⚠️  고점 부근 (90-95%)")
else:
    print(f"  ✅ 조정 상태")
print()

print(f"### QQQ (기준 지수)")
print(f"  현재가: ${current_qqq:.2f}")
print(f"  최고가: ${max_qqq:.2f} ({max_qqq_date.strftime('%Y-%m-%d')})")
print(f"  고점 대비: {(current_qqq / max_qqq - 1) * 100:+.2f}%")
print()

print(f"### QQQI (커버드콜)")
print(f"  현재가: ${current_qqqi:.2f}")
print(f"  최고가: ${max_qqqi:.2f} ({max_qqqi_date.strftime('%Y-%m-%d')})")
print(f"  고점 대비: {(current_qqqi / max_qqqi - 1) * 100:+.2f}%")
print()

# 200일선 대비
qqq['MA200'] = qqq['Close'].rolling(window=200).mean()
current_ma200 = qqq['MA200'].iloc[-1]
distance_from_ma = (current_qqq - current_ma200) / current_ma200 * 100

print("=" * 80)
print("200일선 분석")
print("=" * 80)
print(f"QQQ 현재가: ${current_qqq:.2f}")
print(f"QQQ 200일선: ${current_ma200:.2f}")
print(f"200일선 대비: {distance_from_ma:+.2f}%")
print()

if distance_from_ma > 10:
    print("⚠️⚠️  200일선에서 크게 이탈 (과열)")
    print("→ 조정 가능성 높음")
elif distance_from_ma > 5:
    print("⚠️  200일선 위 (정상 상승)")
    print("→ 단기 조정 가능")
else:
    print("✅ 200일선 근처 (안정)")

print()

# 최근 변동성
recent_30d = tqqq.tail(30)
volatility_30d = recent_30d['Close'].pct_change().std() * (252 ** 0.5) * 100
avg_volume_30d = recent_30d['Volume'].mean()

print("=" * 80)
print("최근 30일 시장 상태")
print("=" * 80)
print(f"TQQQ 변동성: {volatility_30d:.2f}% (연환산)")
print(f"평균 거래량: {avg_volume_30d:,.0f}")
print()

# 최근 고점 대비 조정폭
recent_peak = tqqq.tail(60)['Close'].max()
correction = (current_tqqq - recent_peak) / recent_peak * 100

print(f"최근 60일 고점: ${recent_peak:.2f}")
print(f"현재 조정폭: {correction:+.2f}%")
print()

if correction > -5:
    print("⚠️⚠️  거의 고점 (조정 5% 미만)")
    risk_level = "매우 높음"
elif correction > -10:
    print("⚠️  고점 부근 (조정 5-10%)")
    risk_level = "높음"
elif correction > -20:
    print("⭕ 소폭 조정 (10-20%)")
    risk_level = "중간"
else:
    print("✅ 충분한 조정 (20% 이상)")
    risk_level = "낮음"

print()
print("=" * 80)
print("🎯 진입 타이밍 평가")
print("=" * 80)
print(f"리스크 수준: {risk_level}")
print()

