"""
장기 레버리지 투자 vs 부동산 비교 분석
2년치 연봉 신용대출로 나스닥 투자
"""

from src.data.collector import StockDataCollector
import pandas as pd
import numpy as np

# 가정: 연봉 5,000만원
ANNUAL_SALARY = 50_000_000
LOAN_AMOUNT = ANNUAL_SALARY * 2  # 2년치 연봉 = 1억원
CREDIT_LOAN_RATE = 0.08  # 신용대출 8%
OWN_CAPITAL = 20_000_000  # 자기자본 2,000만원
TOTAL_INVESTMENT = OWN_CAPITAL + LOAN_AMOUNT

print("=" * 80)
print("장기 레버리지 투자 전략 분석")
print("=" * 80)
print()

print("📋 전제 조건:")
print(f"  연봉: {ANNUAL_SALARY:,}원")
print(f"  대출 한도: {LOAN_AMOUNT:,}원 (2년치 연봉)")
print(f"  신용대출 금리: {CREDIT_LOAN_RATE*100}%")
print(f"  자기자본: {OWN_CAPITAL:,}원")
print(f"  총 투자: {TOTAL_INVESTMENT:,}원")
print()

# 나스닥 vs 한국 부동산 장기 수익률
print("=" * 80)
print("📊 역사적 수익률 비교 (장기)")
print("=" * 80)
print()

print("### 나스닥 (QQQ)")
print("  - 20년 연평균: 약 12-15%")
print("  - 10년 연평균: 약 15-18%")
print("  - 5년 연평균: 약 18-20%")
print("  - 최대 낙폭: -83% (2000-2002)")
print("  - 회복 기간: 15년")
print()

print("### 한국 부동산 (서울 아파트)")
print("  - 20년 연평균: 약 3-5%")
print("  - 전세가율: 50-70%")
print("  - 전세 레버리지 시: 6-10%")
print("  - 최대 낙폭: -30% (2013-2014)")
print("  - 유동성: 낮음 (매도 어려움)")
print()

print("✅ 수익률: 나스닥 >>> 부동산 (명백함)")
print()

# 신용대출 리스크 분석
print("=" * 80)
print("⚠️⚠️  신용대출의 치명적 문제")
print("=" * 80)
print()

# 월 원리금 계산 (5년 만기)
loan_months = 60
monthly_rate = CREDIT_LOAN_RATE / 12
monthly_payment = LOAN_AMOUNT * (monthly_rate * (1 + monthly_rate) ** loan_months) / \
                  ((1 + monthly_rate) ** loan_months - 1)

print(f"💸 신용대출 1억원 (8%, 5년):")
print(f"  월 원리금: {monthly_payment:,.0f}원")
print(f"  연 원리금: {monthly_payment * 12:,}원")
print(f"  총 상환액: {monthly_payment * loan_months:,}원")
print(f"  총 이자: {monthly_payment * loan_months - LOAN_AMOUNT:,}원")
print()

print(f"⚠️  연봉 {ANNUAL_SALARY:,}원 대비:")
print(f"  월 상환: {monthly_payment:,.0f}원 = 세전 월급의 {monthly_payment / (ANNUAL_SALARY/12) * 100:.1f}%")
print(f"  세후 월급 3백만원 가정 시: {monthly_payment / 3_000_000 * 100:.1f}% 차지")
print()

if monthly_payment / 3_000_000 > 0.5:
    print("🚨🚨 월급의 50% 이상을 대출 상환!")
    print("   → 생활비 부족")
    print("   → 추가 저축/투자 불가능")
    print("   → 심리적 압박 극대")

print()

# QQQI 배당으로 충당 가능한가?
qqqi_dividend_annual = TOTAL_INVESTMENT * 0.1608
qqqi_dividend_monthly = qqqi_dividend_annual / 12
loan_interest_monthly = LOAN_AMOUNT * CREDIT_LOAN_RATE / 12

print("💰 QQQI 배당으로 충당 가능한가?")
print(f"  월 배당: {qqqi_dividend_monthly:,.0f}원")
print(f"  월 원리금: {monthly_payment:,.0f}원")
print(f"  부족: {monthly_payment - qqqi_dividend_monthly:,.0f}원/월")
print()

deficit_annual = (monthly_payment - qqqi_dividend_monthly) * 12
print(f"⚠️  연간 부족액: {deficit_annual:,}원")
print(f"   → 월급에서 추가 납입 필수")
print()

# 최악 시나리오
print("=" * 80)
print("🚨 최악 시나리오: 나스닥 -50% 폭락")
print("=" * 80)
print()

crash_scenario = TOTAL_INVESTMENT * 0.5
remaining_asset = crash_scenario - LOAN_AMOUNT
loss_pct = (remaining_asset - OWN_CAPITAL) / OWN_CAPITAL * 100

print(f"투자 자산: {TOTAL_INVESTMENT:,}원 → {crash_scenario:,}원")
print(f"대출 잔액: {LOAN_AMOUNT:,}원")
print(f"순자산: {remaining_asset:,}원")
print(f"손실: {remaining_asset - OWN_CAPITAL:,}원 ({loss_pct:.1f}%)")
print()

if remaining_asset < 0:
    print("🚨🚨🚨 파산 상태!")
    print(f"   부채: {abs(remaining_asset):,}원")
    print("   → 추가 담보 요구")
    print("   → 강제 청산")
    print("   → 신용 파탄")
elif remaining_asset < OWN_CAPITAL * 0.3:
    print("🚨🚨 자기자본 70% 이상 손실!")
    print("   → 심리적 붕괴")
    print("   → 월 원리금 납부 어려움")
    print("   → 추가 손실 감당 불가")

print()

# 대안 제시
print("=" * 80)
print("💡 현명한 대안")
print("=" * 80)
print()

alternatives = [
    ("보수적", 30_000_000, "전세대출 수준", "안전하지만 제한적"),
    ("균형적", 50_000_000, "1년치 연봉", "무난함"),
    ("공격적", 70_000_000, "1.5년치 연봉", "관리 가능한 리스크"),
]

print("추천 대출 규모:")
print()

for level, amount, description, evaluation in alternatives:
    monthly_payment_alt = amount * (monthly_rate * (1 + monthly_rate) ** loan_months) / \
                          ((1 + monthly_rate) ** loan_months - 1)
    total_invest = OWN_CAPITAL + amount
    qqqi_dividend_monthly_alt = (total_invest * 0.1608) / 12
    deficit = monthly_payment_alt - qqqi_dividend_monthly_alt
    
    print(f"### {level}: {amount:,}원 ({description})")
    print(f"  총 투자: {total_invest:,}원")
    print(f"  월 원리금: {monthly_payment_alt:,.0f}원")
    print(f"  월 배당: {qqqi_dividend_monthly_alt:,.0f}원")
    print(f"  월 부족: {deficit:,.0f}원")
    print(f"  평가: {evaluation}")
    print()

print("=" * 80)
print("🎯 최종 결론 및 조언")
print("=" * 80)
print()

print("✅ 나스닥 > 부동산 수익률: 맞습니다!")
print()

print("⚠️⚠️  하지만 2년치 연봉 신용대출은 위험합니다!")
print()
print("이유:")
print(f"  1. 월 원리금 {monthly_payment:,.0f}원 = 월급의 50-60%")
print(f"  2. 배당으로도 {(monthly_payment - qqqi_dividend_monthly):,.0f}원 부족")
print(f"  3. 나스닥 -50% 시 자기자본 거의 소진")
print(f"  4. 5년간 원리금 부담 → 삶의 질 저하")
print(f"  5. 추가 투자/저축 불가능")
print()

print("✅ 추천 전략:")
print()
print("1️⃣  단계적 확대 (추천!)")
print("  - 1차: 3,500만원 (증권담보, QQQI)")
print("  - 수익 확인 후 2차: +2,000만원")
print("  - 점진적으로 5,000만원까지 확대")
print("  - 리스크 분산 + 경험 축적")
print()

print("2️⃣  증권담보 우선")
print("  - 신용대출보다 증권담보 (금리 낮음)")
print("  - 금리: 8% → 6-7%")
print("  - 중도상환 수수료 없음")
print()

print("3️⃣  만기일시 활용")
print("  - 월 이자만 납부 (원금 부담 없음)")
print("  - 투자 원금 최대 활용")
print("  - 3-6개월마다 재평가")
print()

print("⚠️  절대 피할 것:")
print("  ❌ 2년치 연봉 신용대출 (월 원리금 200만원)")
print("  ❌ 한 번에 올인 (단계적 진입 필수)")
print("  ❌ 생활비 고려 안 한 대출")
print("  ❌ 비상금 없이 대출")
print()

print("🎯 현명한 시작:")
print("  1. 대출 3,500만원 (증권담보, 만기일시)")
print("  2. QQQI 100% 투자")
print("  3. 6개월 후 수익 나면:")
print("     → 대출 2,000-3,000만원 추가")
print("     → 총 5,500-6,500만원 운용")
print("  4. 1년 후 다시 평가")
print()

print("💰 예상 경로 (단계적):")
print("  1년차: 3,500만원 → 약 +1,100만원 (ROE 115%)")
print("  2년차: 5,500만원 추가 → 누적 +2,500만원")
print("  3년차: 안정적 운용 → 대출 상환 시작")
print()

print("이것이 지속 가능한 레버리지 투자입니다! 🎯")

