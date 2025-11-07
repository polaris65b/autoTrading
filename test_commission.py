# 수수료율별 Moving Average 전략 성과 시뮬레이션
initial = 7142.86
trades = 53

print('=== 수수료율별 Moving Average 전략 영향 ===')
print()

for commission_rate in [0.001, 0.005, 0.01]:
    # 왕복 거래당 손실
    round_trip_loss = commission_rate * 2
    total_trades_loss = round_trip_loss * (trades / 2)
    
    # 수수료만으로 손실되는 금액
    fee_loss = initial * total_trades_loss
    
    print(f'수수료율 {commission_rate*100}%:')
    print(f'  왕복 손실: {round_trip_loss*100:.2f}%')
    print(f'  총 수수료 손실: {total_trades_loss*100:.2f}% (${fee_loss:.2f})')
    print()
