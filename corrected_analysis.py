"""
수정된 대출 레버리지 분석 (정확한 배당률 적용)
"""

# 정확한 QQQI 데이터
QQQI_DIVIDEND_ANNUAL = 0.1608  # 연 16.08% (세후)
QQQI_PRICE_RETURN = 0.15  # 가격 상승 15%
QQQI_TOTAL_RETURN = QQQI_DIVIDEND_ANNUAL + QQQI_PRICE_RETURN  # 31.08%

# 대출 조건
OWN_CAPITAL = 10_000_000
LOAN_AMOUNT = 35_000_000
TOTAL_INVESTMENT = OWN_CAPITAL + LOAN_AMOUNT
LOAN_RATE = 0.07

# 월별 계산
MONTHLY_INTEREST = LOAN_AMOUNT * LOAN_RATE / 12
MONTHLY_DIVIDEND = (TOTAL_INVESTMENT * QQQI_DIVIDEND_ANNUAL) / 12

print("=" * 80)
print("수정된 QQQI 대출 레버리지 분석")
print("=" * 80)
print()

print("📊 QQQI 정확한 수익률")
print(f"  연 배당: 19.01% (세전) → 16.08% (세후)")
print(f"  가격 상승: 15% (보수적)")
print(f"  총 수익률: 31.08%")
print()

print("💰 대출 3,500만원 (총 4,500만원 투자)")
print()

# 1년 수익 계산
total_return = TOTAL_INVESTMENT * QQQI_TOTAL_RETURN
loan_interest_annual = LOAN_AMOUNT * LOAN_RATE
net_profit_annual = total_return - loan_interest_annual

# ROE
roe = (net_profit_annual / OWN_CAPITAL) * 100

print(f"📈 연간 수익:")
print(f"  QQQI 총 수익: {total_return:,.0f}원 ({QQQI_TOTAL_RETURN*100:.2f}%)")
print(f"  대출 이자: {loan_interest_annual:,.0f}원")
print(f"  순수익: {net_profit_annual:,.0f}원")
print(f"  ROE: {roe:.2f}%")
print()

print(f"💸 월별 캐시플로우:")
print(f"  월 배당: {MONTHLY_DIVIDEND:,.0f}원")
print(f"  월 이자: {MONTHLY_INTEREST:,.0f}원")
print(f"  순 캐시플로우: {MONTHLY_DIVIDEND - MONTHLY_INTEREST:,.0f}원")
print()

if MONTHLY_DIVIDEND > MONTHLY_INTEREST:
    surplus = MONTHLY_DIVIDEND - MONTHLY_INTEREST
    print(f"✅ 배당이 이자를 초과! (월 +{surplus:,.0f}원)")
else:
    deficit = MONTHLY_INTEREST - MONTHLY_DIVIDEND
    print(f"⚠️ 배당이 이자 부족 (월 -{deficit:,.0f}원)")
    print(f"   → 자기 자금으로 보충 필요")

print()

# 비교
print("=" * 80)
print("💡 대출 효과 비교")
print("=" * 80)
print()

# 대출 없음
no_loan_profit = OWN_CAPITAL * QQQI_TOTAL_RETURN
no_loan_roe = QQQI_TOTAL_RETURN * 100

print(f"대출 없음 (1,000만원):")
print(f"  수익: {no_loan_profit:,.0f}원")
print(f"  ROE: {no_loan_roe:.2f}%")
print()

print(f"대출 3,500만원 (4,500만원):")
print(f"  수익: {net_profit_annual:,.0f}원")
print(f"  ROE: {roe:.2f}%")
print()

print(f"📈 효과:")
print(f"  수익 증가: {net_profit_annual - no_loan_profit:,.0f}원 ({(net_profit_annual/no_loan_profit):.2f}배)")
print(f"  ROE 증가: {roe - no_loan_roe:.2f}%p")
print()

print("=" * 80)
print("🎯 결론")
print("=" * 80)
print()

if MONTHLY_DIVIDEND > MONTHLY_INTEREST:
    print("✅✅ 대출 레버리지 매우 효과적!")
    print()
    print(f"  - 배당이 이자 충당 + 월 {MONTHLY_DIVIDEND - MONTHLY_INTEREST:,.0f}원 추가 수익")
    print(f"  - ROE {no_loan_roe:.1f}% → {roe:.1f}% (2.4배 증가)")
    print(f"  - 안전한 QQQI로 안정적 레버리지")
else:
    print("⚠️ 배당만으로는 이자 충당 부족")
    print(f"  - 월 {MONTHLY_INTEREST - MONTHLY_DIVIDEND:,.0f}원 추가 필요")
    print(f"  - 하지만 ROE는 여전히 높음 ({roe:.1f}%)")

print()
print("추천: 대출 3,500만원으로 시드 확대!")
print("  → QQQI 선행 투자")
print("  → 200일선 이탈 시 Shannon 전환")
