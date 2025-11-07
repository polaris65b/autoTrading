from src.data.collector import StockDataCollector
import pandas as pd

collector = StockDataCollector()

qqqi = collector.collect_ohlcv('QQQI', '2024-02-01', '2025-11-06')
tqqq = collector.collect_ohlcv('TQQQ', '2024-02-01', '2025-11-06')

dividend_dates = qqqi[qqqi['Dividends'] > 0].index

print('=== TQQQ 기회비용 분석 ===')
print()
print(f'{"배당일":<12} {"QQQI배당":<10} {"QQQI변동":<10} {"TQQQ변동":<10} {"기회비용":<10}')
print('-' * 60)

total_qqqi_gain = 0
total_tqqq_opportunity = 0

for div_date in dividend_dates:
    div_idx = qqqi.index.get_loc(div_date)
    
    if div_idx < 1 or div_idx >= len(qqqi) - 1:
        continue
    
    prev_date = qqqi.index[div_idx - 1]
    next_date = qqqi.index[div_idx + 1]
    
    # QQQI 수익 (배당 + 가격변동)
    dividend = qqqi.loc[div_date, 'Dividends'] * 0.846  # 세후
    qqqi_price_change = qqqi.loc[next_date, 'Close'] - qqqi.loc[prev_date, 'Close']
    qqqi_gain_pct = (dividend + qqqi_price_change) / qqqi.loc[prev_date, 'Close'] * 100
    
    # TQQQ 기회비용 (같은 기간 TQQQ 보유 시 수익)
    if prev_date in tqqq.index and next_date in tqqq.index:
        tqqq_price_change = tqqq.loc[next_date, 'Close'] - tqqq.loc[prev_date, 'Close']
        tqqq_gain_pct = (tqqq_price_change / tqqq.loc[prev_date, 'Close']) * 100
        
        opportunity_cost = tqqq_gain_pct - qqqi_gain_pct
        
        print(f'{div_date.strftime("%Y-%m-%d"):<12} ${dividend:<9.2f} {qqqi_gain_pct:<9.2f}% {tqqq_gain_pct:<9.2f}% {opportunity_cost:<9.2f}%')
        
        total_qqqi_gain += qqqi_gain_pct
        total_tqqq_opportunity += opportunity_cost

print()
print(f'총 QQQI 수익: {total_qqqi_gain:.2f}%')
print(f'총 TQQQ 기회비용: {total_tqqq_opportunity:.2f}%')
print()
if total_tqqq_opportunity > 0:
    print('⚠️ TQQQ가 더 좋았음 (기회비용 발생)')
else:
    print('✅ QQQI가 더 좋았음 (기회비용 없음)')
