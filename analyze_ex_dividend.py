from src.data.collector import StockDataCollector
import pandas as pd

collector = StockDataCollector()
qqqi = collector.collect_ohlcv('QQQI', '2024-02-01', '2025-11-06')

# 배당이 있는 날짜
dividend_dates = qqqi[qqqi['Dividends'] > 0].copy()

print('=== QQQI 배당락 가격 변동 분석 ===')
print()

price_drops = []
for i, (date, row) in enumerate(dividend_dates.iterrows()):
    dividend = row['Dividends']
    price_on_div_date = row['Close']
    
    # 다음 거래일 가격 (배당락일 이후)
    date_idx = qqqi.index.get_loc(date)
    if date_idx < len(qqqi) - 1:
        next_date = qqqi.index[date_idx + 1]
        next_price = qqqi.loc[next_date, 'Close']
        
        # 가격 변동
        price_change = next_price - price_on_div_date
        price_change_pct = (price_change / price_on_div_date) * 100
        
        # 배당 대비 가격 하락
        drop_vs_dividend = (price_change / dividend) * 100 if dividend > 0 else 0
        
        price_drops.append({
            'date': date.strftime('%Y-%m-%d'),
            'dividend': dividend,
            'price_on_div': price_on_div_date,
            'next_price': next_price,
            'change': price_change,
            'change_pct': price_change_pct,
            'drop_vs_div': drop_vs_dividend
        })

df = pd.DataFrame(price_drops)

print(f'{"날짜":<12} {"배당":<8} {"당일종가":<10} {"익일종가":<10} {"변동":<8} {"변동%":<8} {"배당대비":<10}')
print('-' * 80)
for _, row in df.iterrows():
    print(f"{row['date']:<12} ${row['dividend']:<7.4f} ${row['price_on_div']:<9.2f} ${row['next_price']:<9.2f} ${row['change']:<7.2f} {row['change_pct']:<7.2f}% {row['drop_vs_div']:<9.2f}%")

print()
print(f'평균 익일 가격 변동: {df["change_pct"].mean():.2f}%')
print(f'평균 배당 대비 하락: {df["drop_vs_div"].mean():.2f}%')
print(f'가격 상승 횟수: {(df["change"] > 0).sum()}회')
print(f'가격 하락 횟수: {(df["change"] < 0).sum()}회')
