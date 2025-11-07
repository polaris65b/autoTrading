from src.data.collector import StockDataCollector
import pandas as pd

collector = StockDataCollector()

# 데이터 수집
qqqi = collector.collect_ohlcv('QQQI', '2024-02-01', '2025-11-06')
tqqq = collector.collect_ohlcv('TQQQ', '2024-02-01', '2025-11-06')

# 초기 설정
initial_capital = 7142.86
commission_rate = 0.001
dividend_tax = 0.154

print('=== 배당 캡처 전략 vs 일반 Shannon 시뮬레이션 ===')
print()

# 배당락일
dividend_dates = qqqi[qqqi['Dividends'] > 0].index

total_gain_capture = 0
total_gain_normal = 0
total_commission_capture = 0
total_commission_normal = 0

for div_date in dividend_dates[:5]:  # 처음 5회만 테스트
    div_idx = qqqi.index.get_loc(div_date)
    
    if div_idx < 1:
        continue
    
    prev_date = qqqi.index[div_idx - 1]
    
    # 배당 정보
    dividend_per_share = qqqi.loc[div_date, 'Dividends']
    dividend_net = dividend_per_share * (1 - dividend_tax)
    
    # 가격 정보
    qqqi_price_before = qqqi.loc[prev_date, 'Close']
    qqqi_price_div = qqqi.loc[div_date, 'Close']
    
    if div_idx < len(qqqi) - 1:
        next_date = qqqi.index[div_idx + 1]
        qqqi_price_after = qqqi.loc[next_date, 'Close']
    else:
        qqqi_price_after = qqqi_price_div
    
    print(f'\n### {div_date.strftime("%Y-%m-%d")} 배당: ${dividend_per_share:.4f} ###')
    
    # === 전략 1: 배당 캡처 (50% → 100% → 50%) ===
    capital = 7000  # 절반만 사용
    
    # 1일 전: TQQQ 50% → QQQI로 전환
    tqqq_to_qqqi = capital * 0.5
    commission_sell_tqqq = tqqq_to_qqqi * commission_rate
    commission_buy_qqqi = tqqq_to_qqqi * commission_rate
    qqqi_quantity_extra = int((tqqq_to_qqqi * (1 - commission_rate)) / qqqi_price_before)
    
    # 배당락일: 배당 수령
    base_quantity = int((capital * 0.5) / qqqi_price_before)  # 기존 50%
    total_quantity = base_quantity + qqqi_quantity_extra  # 100%
    dividend_received = total_quantity * dividend_net
    
    # 배당락일 이후 가격 변동
    price_change = qqqi_price_after - qqqi_price_before
    capital_change = total_quantity * price_change
    
    # 배당락일 이후: QQQI 50% → TQQQ로 재전환
    qqqi_to_tqqq = (total_quantity * qqqi_price_after * 0.5)
    commission_sell_qqqi = qqqi_to_tqqq * commission_rate
    commission_buy_tqqq = qqqi_to_tqqq * commission_rate
    
    # 총 수수료
    total_commission = commission_sell_tqqq + commission_buy_qqqi + commission_sell_qqqi + commission_buy_tqqq
    
    # 순이익
    net_gain_capture = dividend_received + capital_change - total_commission
    
    # === 전략 2: 일반 Shannon (50:50 유지) ===
    normal_quantity = base_quantity
    dividend_normal = normal_quantity * dividend_net
    capital_change_normal = normal_quantity * price_change
    net_gain_normal = dividend_normal + capital_change_normal
    
    print(f'  전날 가격: ${qqqi_price_before:.2f}')
    print(f'  배당락일 가격: ${qqqi_price_div:.2f} ({(qqqi_price_div/qqqi_price_before-1)*100:+.2f}%)')
    print(f'  익일 가격: ${qqqi_price_after:.2f} ({(qqqi_price_after/qqqi_price_before-1)*100:+.2f}%)')
    print()
    print(f'  배당 캡처:')
    print(f'    수량: {total_quantity}주 (기존 {base_quantity} + 추가 {qqqi_quantity_extra})')
    print(f'    배당 수령: ${dividend_received:.2f}')
    print(f'    가격 변동: ${capital_change:.2f}')
    print(f'    수수료: ${total_commission:.2f}')
    print(f'    순이익: ${net_gain_capture:.2f}')
    print()
    print(f'  일반 Shannon:')
    print(f'    수량: {normal_quantity}주')
    print(f'    배당 수령: ${dividend_normal:.2f}')
    print(f'    가격 변동: ${capital_change_normal:.2f}')
    print(f'    순이익: ${net_gain_normal:.2f}')
    print()
    print(f'  차이: ${net_gain_capture - net_gain_normal:.2f} ({(net_gain_capture/net_gain_normal-1)*100:+.2f}%)')
    
    total_gain_capture += net_gain_capture
    total_gain_normal += net_gain_normal
    total_commission_capture += total_commission

print()
print('=' * 80)
print(f'총 5회 배당 결과:')
print(f'  배당 캡처 순이익: ${total_gain_capture:.2f}')
print(f'  일반 Shannon 순이익: ${total_gain_normal:.2f}')
print(f'  차이: ${total_gain_capture - total_gain_normal:.2f}')
print(f'  수수료 총액: ${total_commission_capture:.2f}')
print()
print(f'결론: 배당 캡처가 {"유리" if total_gain_capture > total_gain_normal else "불리"}')
