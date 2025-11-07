from src.data.collector import StockDataCollector
import pandas as pd

collector = StockDataCollector()

# QQQI 배당 날짜 확인
qqqi = collector.collect_ohlcv('QQQI', '2024-02-01', '2025-11-06')

# 배당이 있는 날짜 추출
dividend_dates = qqqi[qqqi['Dividends'] > 0]

print('=== QQQI 배당 날짜 (2024-02-01 ~ 2025-11-06) ===')
print()
for date, row in dividend_dates.iterrows():
    print(f"{date.strftime('%Y-%m-%d')}: ${row['Dividends']:.4f}")

print()
print(f'총 배당 횟수: {len(dividend_dates)}회')
print(f'평균 배당: ${dividend_dates["Dividends"].mean():.4f}')
