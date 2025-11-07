"""
3개월 후 대출 갈아타기 분석
Shannon (TQQQ + QQQI) 투자 시나리오
"""

import pandas as pd
import numpy as np

# 대출 조건
LOAN_AMOUNT = 35_000_000  # 3,500만원
INTEREST_RATE = 0.07  # 연 7%
MONTHLY_RATE = INTEREST_RATE / 12

# 투자 조건
INITIAL_CAPITAL = 10_000_000  # 자기자본
TOTAL_INVESTMENT = INITIAL_CAPITAL + LOAN_AMOUNT
EXCHANGE_RATE = 1400

# 백테스팅 수익률 (연환산)
ANNUAL_RETURN = 0.7588  # 75.88% (밴딩 + 배당 재투자)

print("=" * 80)
print("3개월 후 대출 갈아타기 분석")
print("=" * 80)
print()

# 3개월 투자 수익 계산
MONTHS = 3
investment_period_years = MONTHS / 12

# 복리 수익률
expected_return_3months = (1 + ANNUAL_RETURN) ** investment_period_years - 1

# 투자 자산 가치 (3개월 후)
investment_value_usd = (TOTAL_INVESTMENT / EXCHANGE_RATE) * (1 + expected_return_3months)
investment_value_krw = investment_value_usd * EXCHANGE_RATE

print(f"투자 조건:")
print(f"  초기 투자: {TOTAL_INVESTMENT:,}원")
print(f"  예상 수익률: {ANNUAL_RETURN*100:.2f}% (연)")
print(f"  투자 기간: {MONTHS}개월")
print()

print(f"3개월 후 예상:")
print(f"  투자 자산 가치: {investment_value_krw:,.0f}원")
print(f"  수익금: {investment_value_krw - TOTAL_INVESTMENT:,.0f}원 ({expected_return_3months*100:.2f}%)")
print()

# 각 대출 방식별 3개월 후 상황
print("=" * 80)
print("📊 대출 방식별 3개월 후 상황")
print("=" * 80)
print()

# 1. 원리금균등
monthly_payment_equal = LOAN_AMOUNT * (MONTHLY_RATE * (1 + MONTHLY_RATE) ** 60) / \
                        ((1 + MONTHLY_RATE) ** 60 - 1)

remaining_equal = LOAN_AMOUNT
paid_interest_equal = 0
paid_principal_equal = 0

for month in range(1, MONTHS + 1):
    interest = remaining_equal * MONTHLY_RATE
    principal = monthly_payment_equal - interest
    paid_interest_equal += interest
    paid_principal_equal += principal
    remaining_equal -= principal

print("### 1️⃣  원리금균등")
print(f"  월 납입: {monthly_payment_equal:,.0f}원 × {MONTHS}개월 = {monthly_payment_equal * MONTHS:,.0f}원")
print(f"  납입 원금: {paid_principal_equal:,.0f}원")
print(f"  납입 이자: {paid_interest_equal:,.0f}원")
print(f"  대출 잔액: {remaining_equal:,.0f}원")
print()

# 2. 원금균등
monthly_principal = LOAN_AMOUNT / 60
remaining_principal_equal = LOAN_AMOUNT
paid_interest_principal_equal = 0
paid_principal_principal_equal = 0
monthly_payments_principal_equal = []

for month in range(1, MONTHS + 1):
    interest = remaining_principal_equal * MONTHLY_RATE
    total_payment = monthly_principal + interest
    paid_interest_principal_equal += interest
    paid_principal_principal_equal += monthly_principal
    remaining_principal_equal -= monthly_principal
    monthly_payments_principal_equal.append(total_payment)

print("### 2️⃣  원금균등")
print(f"  월 납입: 787,500원 → 778,472원 → 769,444원 = 평균 {np.mean(monthly_payments_principal_equal):,.0f}원")
print(f"  총 납입: {sum(monthly_payments_principal_equal):,.0f}원")
print(f"  납입 원금: {paid_principal_principal_equal:,.0f}원")
print(f"  납입 이자: {paid_interest_principal_equal:,.0f}원")
print(f"  대출 잔액: {remaining_principal_equal:,.0f}원")
print()

# 3. 만기일시
monthly_interest_only = LOAN_AMOUNT * MONTHLY_RATE
paid_interest_bullet = monthly_interest_only * MONTHS

print("### 3️⃣  만기일시상환")
print(f"  월 납입: {monthly_interest_only:,.0f}원 × {MONTHS}개월 = {paid_interest_bullet:,.0f}원")
print(f"  납입 원금: 0원")
print(f"  납입 이자: {paid_interest_bullet:,.0f}원")
print(f"  대출 잔액: {LOAN_AMOUNT:,}원 (변동 없음)")
print()

# 중도상환 수수료 분석
print("=" * 80)
print("💸 중도상환 수수료 (갈아타기 비용)")
print("=" * 80)
print()

prepayment_fee_rates = {
    "일반 신용대출": 0.015,  # 1.5%
    "주택담보대출": 0.008,   # 0.8%
    "증권담보대출": 0.0,     # 0% (보통 없음)
}

print("중도상환수수료율 (금융기관별 다름):")
for loan_type, fee_rate in prepayment_fee_rates.items():
    print(f"  {loan_type}: {fee_rate*100}%")
print()

print("3개월 후 갈아타기 비용:")
print()

for loan_type, fee_rate in prepayment_fee_rates.items():
    # 원리금균등: 잔액 기준
    fee_equal = remaining_equal * fee_rate
    
    # 원금균등: 잔액 기준
    fee_principal_equal = remaining_principal_equal * fee_rate
    
    # 만기일시: 전액 기준
    fee_bullet = LOAN_AMOUNT * fee_rate
    
    print(f"### {loan_type} (수수료 {fee_rate*100}%)")
    print(f"  원리금균등: {remaining_equal:,.0f}원 × {fee_rate*100}% = {fee_equal:,.0f}원")
    print(f"  원금균등: {remaining_principal_equal:,.0f}원 × {fee_rate*100}% = {fee_principal_equal:,.0f}원")
    print(f"  만기일시: {LOAN_AMOUNT:,}원 × {fee_rate*100}% = {fee_bullet:,.0f}원")
    print()

# 순수익 계산 (증권담보대출 가정 - 수수료 0%)
print("=" * 80)
print("💰 3개월 후 갈아타기 순수익 (증권담보대출 가정)")
print("=" * 80)
print()

for method, remaining, paid_total, paid_interest in [
    ("원리금균등", remaining_equal, monthly_payment_equal * MONTHS, paid_interest_equal),
    ("원금균등", remaining_principal_equal, sum(monthly_payments_principal_equal), paid_interest_principal_equal),
    ("만기일시", LOAN_AMOUNT, paid_interest_bullet, paid_interest_bullet),
]:
    # 순자산 = 투자자산 - 대출잔액
    net_asset = investment_value_krw - remaining
    
    # 순수익 = 순자산 - 자기자본 - 납입액
    net_profit = net_asset - INITIAL_CAPITAL - paid_total
    
    # 수익률
    total_invested = INITIAL_CAPITAL + paid_total
    net_return_pct = (net_profit / total_invested) * 100
    
    print(f"### {method}")
    print(f"  투자 자산: {investment_value_krw:,.0f}원")
    print(f"  대출 잔액: {remaining:,.0f}원")
    print(f"  순자산: {net_asset:,.0f}원")
    print(f"  납입 금액: {paid_total:,.0f}원")
    print(f"  총 투입금: {total_invested:,.0f}원")
    print(f"  순수익: {net_profit:,.0f}원")
    print(f"  수익률: {net_return_pct:.2f}%")
    print()

# 갈아타기 추천
print("=" * 80)
print("🎯 3개월 후 갈아타기 결론")
print("=" * 80)
print()
print("✅ 갈아타기 문제 없음! (증권담보대출 가정)")
print()
print("이유:")
print("  1. 중도상환수수료 0% (증권담보대출)")
print("  2. 3개월 이자만 납부했으므로 부담 적음")
print("  3. 투자 자산 증가로 더 유리한 조건 가능")
print()
print(f"예상 시나리오:")
print(f"  - 투자 자산: {investment_value_krw:,.0f}원")
print(f"  - 대출 상환 후 순자산: {investment_value_krw - LOAN_AMOUNT:,.0f}원")
print(f"  - 더 낮은 금리로 재대출 가능")
print()
print("⚠️  주의사항:")
print(f"  1. 증권담보대출인지 확인 필수 (중도상환수수료 0%)")
print(f"  2. 신용대출이면 중도상환수수료 1.5% = {LOAN_AMOUNT * 0.015:,.0f}원")
print(f"  3. 3개월 내 큰 하락(-39%) 시 갈아타기 불가능")
print(f"  4. 금리 상승 시 재대출 조건 악화 가능")
print()

# 최악 시나리오
print("=" * 80)
print("🚨 리스크 시나리오: 3개월 내 -39% 하락")
print("=" * 80)
print()

worst_case_value = TOTAL_INVESTMENT * 0.61  # -39% 손실
worst_case_net = worst_case_value - LOAN_AMOUNT

print(f"최악의 경우:")
print(f"  투자 자산: {worst_case_value:,.0f}원 (-39%)")
print(f"  대출 잔액: {LOAN_AMOUNT:,}원")
print(f"  순자산: {worst_case_net:,.0f}원")
print(f"  손실: {worst_case_net - INITIAL_CAPITAL:,.0f}원")
print()

if worst_case_net < INITIAL_CAPITAL:
    print(f"⚠️⚠️  자기자본 {INITIAL_CAPITAL:,}원 소진!")
    print(f"⚠️⚠️  추가 손실: {INITIAL_CAPITAL - worst_case_net:,.0f}원")
    print(f"⚠️⚠️  이 경우 갈아타기 불가능 (담보 부족)")
else:
    print(f"✅ 자기자본은 유지 (손실 {INITIAL_CAPITAL - worst_case_net:,.0f}원)")

print()
print("=" * 80)
print("💡 최종 추천")
print("=" * 80)
print()
print("✅ 3개월 후 갈아타기 가능!")
print()
print("조건:")
print("  1. 증권담보대출로 받을 것 (중도상환수수료 0%)")
print("  2. 3개월간 큰 손실 없을 것 (최소 -20% 이내)")
print("  3. 재대출 조건 확인 (금리, 한도)")
print()
print("전략:")
print("  1. 만기일시로 시작 (월 20만원, 원금 활용 극대화)")
print("  2. 3개월 투자 진행 (예상 수익 15-20%)")
print("  3. 3개월 후 상황 판단:")
print("     - 수익 나면: 더 낮은 금리로 재대출")
print("     - 손실이면: 일부 청산 후 대출 축소")
print("     - 원하면: 원리금균등으로 전환")
print()
print("⚠️  필수 체크리스트:")
print("  □ 증권담보대출인가? (중도상환수수료 확인)")
print("  □ 재대출 가능 증권사 확인")
print("  □ 월 20만원 현금흐름 확보")
print("  □ 비상금 500만원 이상 확보")
print("  □ -30% 하락 견딜 수 있는 멘탈")

