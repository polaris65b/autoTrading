"""
대출(빚투) 투자 시뮬레이션
Shannon 전략 (TQQQ + QQQI) + 대출 3,500만원
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# 대출 조건
LOAN_AMOUNT = 35_000_000  # 3,500만원
INTEREST_RATE = 0.07  # 연 7%
LOAN_PERIOD_MONTHS = 60  # 5년 (일반적)
MONTHLY_RATE = INTEREST_RATE / 12  # 월 이자율

print("=" * 80)
print("대출(빚투) 투자 시뮬레이션: Shannon (TQQQ + QQQI)")
print("=" * 80)
print()
print(f"대출 조건:")
print(f"  대출 금액: {LOAN_AMOUNT:,}원")
print(f"  대출 금리: {INTEREST_RATE*100}% (연)")
print(f"  대출 기간: {LOAN_PERIOD_MONTHS}개월 ({LOAN_PERIOD_MONTHS//12}년)")
print(f"  월 이자율: {MONTHLY_RATE*100:.4f}%")
print()

# 1. 원리금균등 (Equal Installment)
monthly_payment_equal = LOAN_AMOUNT * (MONTHLY_RATE * (1 + MONTHLY_RATE) ** LOAN_PERIOD_MONTHS) / \
                        ((1 + MONTHLY_RATE) ** LOAN_PERIOD_MONTHS - 1)

total_payment_equal = monthly_payment_equal * LOAN_PERIOD_MONTHS
total_interest_equal = total_payment_equal - LOAN_AMOUNT

print("=" * 80)
print("1️⃣  원리금균등 상환")
print("=" * 80)
print(f"월 상환액: {monthly_payment_equal:,.0f}원 (고정)")
print(f"총 상환액: {total_payment_equal:,.0f}원")
print(f"총 이자: {total_interest_equal:,.0f}원")
print()

# 첫 3개월 상세
print("초기 3개월 상세:")
remaining = LOAN_AMOUNT
for month in range(1, 4):
    interest = remaining * MONTHLY_RATE
    principal = monthly_payment_equal - interest
    remaining -= principal
    print(f"  {month}개월: 원금 {principal:,.0f}원 + 이자 {interest:,.0f}원 = {monthly_payment_equal:,.0f}원 (잔액: {remaining:,.0f}원)")

print()

# 2. 원금균등 (Equal Principal)
monthly_principal = LOAN_AMOUNT / LOAN_PERIOD_MONTHS

print("=" * 80)
print("2️⃣  원금균등 상환")
print("=" * 80)
print(f"월 원금: {monthly_principal:,.0f}원 (고정)")

total_interest_principal_equal = 0
remaining = LOAN_AMOUNT

# 첫 3개월 상세
print("초기 3개월 상세:")
for month in range(1, 4):
    interest = remaining * MONTHLY_RATE
    total_payment = monthly_principal + interest
    total_interest_principal_equal += interest
    remaining -= monthly_principal
    print(f"  {month}개월: 원금 {monthly_principal:,.0f}원 + 이자 {interest:,.0f}원 = {total_payment:,.0f}원 (잔액: {remaining:,.0f}원)")

# 전체 이자 계산
for month in range(4, LOAN_PERIOD_MONTHS + 1):
    interest = remaining * MONTHLY_RATE
    total_interest_principal_equal += interest
    remaining -= monthly_principal

total_payment_principal_equal = LOAN_AMOUNT + total_interest_principal_equal

print()
print(f"첫 달 상환액: {monthly_principal + LOAN_AMOUNT * MONTHLY_RATE:,.0f}원")
print(f"마지막 달 상환액: {monthly_principal + monthly_principal * MONTHLY_RATE:,.0f}원")
print(f"총 상환액: {total_payment_principal_equal:,.0f}원")
print(f"총 이자: {total_interest_principal_equal:,.0f}원")
print()

# 3. 만기일시상환 (Bullet Repayment)
monthly_interest_only = LOAN_AMOUNT * MONTHLY_RATE
total_interest_bullet = monthly_interest_only * LOAN_PERIOD_MONTHS
total_payment_bullet = LOAN_AMOUNT + total_interest_bullet

print("=" * 80)
print("3️⃣  만기일시상환 (이자만 납부)")
print("=" * 80)
print(f"월 이자: {monthly_interest_only:,.0f}원 (고정)")
print(f"총 이자: {total_interest_bullet:,.0f}원")
print(f"총 상환액: {total_payment_bullet:,.0f}원 (만기 시 원금 {LOAN_AMOUNT:,}원 포함)")
print()

# 비교 표
print("=" * 80)
print("📊 상환 방식 비교")
print("=" * 80)
print()
print(f"{'구분':<15} {'월 납입액(초기)':<20} {'총 이자':<20} {'총 상환액':<20}")
print("-" * 80)
print(f"{'원리금균등':<15} {monthly_payment_equal:>18,.0f}원 {total_interest_equal:>18,.0f}원 {total_payment_equal:>18,.0f}원")
print(f"{'원금균등':<15} {monthly_principal + LOAN_AMOUNT * MONTHLY_RATE:>18,.0f}원 {total_interest_principal_equal:>18,.0f}원 {total_payment_principal_equal:>18,.0f}원")
print(f"{'만기일시':<15} {monthly_interest_only:>18,.0f}원 {total_interest_bullet:>18,.0f}원 {total_payment_bullet:>18,.0f}원")
print()

# 이자 절감액
print(f"💰 이자 절감액 (원금균등 vs 만기일시): {total_interest_bullet - total_interest_principal_equal:,.0f}원")
print(f"💰 이자 절감액 (원리금균등 vs 만기일시): {total_interest_bullet - total_interest_equal:,.0f}원")
print()

# 투자 관점 분석
print("=" * 80)
print("📈 투자 관점 분석")
print("=" * 80)
print()
print("### 만기일시상환의 장점:")
print(f"  - 월 {monthly_interest_only:,.0f}원만 납부 → 현금흐름 여유")
print(f"  - 투자 원금 최대 활용 가능")
print(f"  - 복리 효과 극대화")
print()
print("### 만기일시상환의 단점:")
print(f"  - 총 이자 최대 ({total_interest_bullet:,.0f}원)")
print(f"  - 5년 후 원금 {LOAN_AMOUNT:,}원 일시 상환 부담")
print(f"  - 투자 실패 시 원금 상환 어려움")
print()
print("### 원금균등의 장점:")
print(f"  - 이자 절감 ({total_interest_bullet - total_interest_principal_equal:,.0f}원)")
print(f"  - 대출 잔액 꾸준히 감소 → 심리적 안정")
print(f"  - 리스크 점진적 감소")
print()
print("### 원금균등의 단점:")
print(f"  - 초기 월 상환액 높음 ({monthly_principal + LOAN_AMOUNT * MONTHLY_RATE:,.0f}원)")
print(f"  - 투자 원금 점진적 감소")
print()

# 손익분기점 계산
print("=" * 80)
print("💡 손익분기점 분석")
print("=" * 80)
print()

# 연 7% 이자를 상회하는 수익률이 필요
breakeven_return_annual = INTEREST_RATE * 100
print(f"필요 최소 수익률: 연 {breakeven_return_annual:.2f}% (대출 이자율)")
print()
print(f"Shannon (TQQQ+QQQI) 예상 수익률:")
print(f"  - 밴딩: 약 75-77% (배당 재투자 포함)")
print(f"  - 월단위 리밸런싱: 약 79-80%")
print()
print(f"✅ Shannon 전략은 대출 이자({INTEREST_RATE*100}%)를 크게 상회!")
print(f"   → 빚투 타당성 있음")
print()

# 시나리오 분석
print("=" * 80)
print("🎲 시나리오 분석 (5년 투자)")
print("=" * 80)
print()

scenarios = [
    ("최선", 0.80, "백테스팅 수익률 유지"),
    ("기대", 0.50, "보수적 추정"),
    ("최악", 0.00, "원금 보존"),
    ("손실", -0.20, "20% 손실"),
]

investment_amount = LOAN_AMOUNT
years = LOAN_PERIOD_MONTHS / 12

for scenario_name, annual_return, description in scenarios:
    # 복리 계산
    final_value = investment_amount * ((1 + annual_return) ** years)
    profit = final_value - investment_amount
    
    # 대출 비용
    if scenario_name in ["최선", "기대"]:
        loan_cost = total_interest_bullet  # 만기일시 (최대 투자)
    else:
        loan_cost = total_interest_equal  # 원리금균등 (안전)
    
    # 순수익
    net_profit = profit - loan_cost
    net_return = (net_profit / investment_amount) * 100
    
    print(f"### {scenario_name} 시나리오: 연 {annual_return*100:+.0f}% ({description})")
    print(f"  최종 자산: {final_value:,.0f}원")
    print(f"  투자 수익: {profit:,.0f}원")
    print(f"  대출 이자: {loan_cost:,.0f}원")
    print(f"  순수익: {net_profit:,.0f}원 ({net_return:+.2f}%)")
    print()

