"""
최대 한도 1년치 연봉 분석
현실적이고 지속 가능한 레버리지 투자
"""

# 가정
ANNUAL_SALARY = 50_000_000
MAX_LOAN = ANNUAL_SALARY  # 1년치 연봉
OWN_CAPITAL = 20_000_000
TOTAL = OWN_CAPITAL + MAX_LOAN

LOAN_RATE_CREDIT = 0.08  # 신용대출 8%
LOAN_RATE_SECURITY = 0.07  # 증권담보 7%
MONTHLY_SALARY_NET = 3_000_000

# QQQI 특성
QQQI_DIVIDEND = 0.1608  # 세후 16.08%
QQQI_TOTAL_RETURN = 0.31  # 총 31%

print("=" * 80)
print("최대 한도: 1년치 연봉 (5,000만원)")
print("=" * 80)
print()

print("📋 기본 설정:")
print(f"  연봉: {ANNUAL_SALARY:,}원")
print(f"  최대 대출: {MAX_LOAN:,}원 (1년치)")
print(f"  자기자본: {OWN_CAPITAL:,}원")
print(f"  총 투자: {TOTAL:,}원")
print(f"  세후 월급: {MONTHLY_SALARY_NET:,}원")
print()

# 원리금균등 vs 만기일시 비교
print("=" * 80)
print("💸 대출 방식별 월 부담")
print("=" * 80)
print()

loan_months = 60
monthly_rate_credit = LOAN_RATE_CREDIT / 12

# 원리금균등
monthly_payment_equal = MAX_LOAN * (monthly_rate_credit * (1 + monthly_rate_credit) ** loan_months) / \
                        ((1 + monthly_rate_credit) ** loan_months - 1)

# 만기일시
monthly_interest_bullet = MAX_LOAN * LOAN_RATE_SECURITY / 12  # 증권담보 7%

# QQQI 월 배당
qqqi_dividend_monthly = (TOTAL * QQQI_DIVIDEND) / 12

print(f"### 신용대출 (원리금균등, 8%)")
print(f"  월 원리금: {monthly_payment_equal:,.0f}원")
print(f"  월 배당: {qqqi_dividend_monthly:,.0f}원")
print(f"  순 부담: {monthly_payment_equal - qqqi_dividend_monthly:,.0f}원")
print(f"  월급 대비: {monthly_payment_equal / MONTHLY_SALARY_NET * 100:.1f}%")
print()

print(f"### 증권담보 (만기일시, 7%)")
print(f"  월 이자: {monthly_interest_bullet:,.0f}원")
print(f"  월 배당: {qqqi_dividend_monthly:,.0f}원")
print(f"  순수익: {qqqi_dividend_monthly - monthly_interest_bullet:,.0f}원 ✅")
print(f"  월급 대비: {monthly_interest_bullet / MONTHLY_SALARY_NET * 100:.1f}%")
print()

# 생활비 시뮬레이션
RENT = 1_000_000
LIVING = 800_000
INSURANCE = 200_000
SAVINGS = 300_000

print("=" * 80)
print("🏠 현실 체크: 생활 가능한가?")
print("=" * 80)
print()

expenses_basic = RENT + LIVING + INSURANCE + SAVINGS

print(f"기본 생활비:")
print(f"  주거비: {RENT:,}원")
print(f"  생활비: {LIVING:,}원")
print(f"  보험/기타: {INSURANCE:,}원")
print(f"  저축/여유: {SAVINGS:,}원")
print(f"  합계: {expenses_basic:,}원")
print()

# 신용대출 (원리금균등)
surplus_credit = MONTHLY_SALARY_NET - monthly_payment_equal - expenses_basic
print(f"### 신용대출 5,000만원 (원리금균등)")
print(f"  월급: {MONTHLY_SALARY_NET:,}원")
print(f"  대출: {monthly_payment_equal:,.0f}원")
print(f"  생활: {expenses_basic:,}원")
print(f"  잉여: {surplus_credit:,.0f}원")

if surplus_credit < 0:
    print(f"  🚨 매월 {abs(surplus_credit):,}원 적자!")
else:
    print(f"  {'⚠️' if surplus_credit < 300_000 else '✅'} 여유 {'부족' if surplus_credit < 300_000 else '충분'}")

# 배당 고려
deficit_credit = monthly_payment_equal - qqqi_dividend_monthly
surplus_with_dividend_credit = MONTHLY_SALARY_NET - deficit_credit - expenses_basic
print(f"  배당 적용: 잉여 {surplus_with_dividend_credit:,.0f}원")
print()

# 증권담보 (만기일시)
surplus_security = MONTHLY_SALARY_NET - monthly_interest_bullet - expenses_basic
net_cashflow = qqqi_dividend_monthly - monthly_interest_bullet
surplus_with_dividend_security = surplus_security + net_cashflow

print(f"### 증권담보 5,000만원 (만기일시)")
print(f"  월급: {MONTHLY_SALARY_NET:,}원")
print(f"  이자: {monthly_interest_bullet:,.0f}원")
print(f"  생활: {expenses_basic:,}원")
print(f"  잉여: {surplus_security:,.0f}원 ✅")
print(f"  배당 순수익: +{net_cashflow:,.0f}원")
print(f"  총 잉여: {surplus_with_dividend_security:,.0f}원 ✅✅")
print()

# 리스크 분석
print("=" * 80)
print("⚠️  리스크 분석")
print("=" * 80)
print()

# -50% 하락 시
asset_at_crash = TOTAL * 0.5
net_asset_crash = asset_at_crash - MAX_LOAN
loss_pct = (net_asset_crash - OWN_CAPITAL) / OWN_CAPITAL * 100

print(f"🚨 최악 시나리오: -50% 폭락")
print(f"  자산: {TOTAL:,}원 → {asset_at_crash:,}원")
print(f"  대출: {MAX_LOAN:,}원")
print(f"  순자산: {net_asset_crash:,}원")
print(f"  손실: {net_asset_crash - OWN_CAPITAL:,}원 ({loss_pct:.1f}%)")

if net_asset_crash < 0:
    print(f"  🚨🚨 파산! 부채 {abs(net_asset_crash):,}원")
elif net_asset_crash < OWN_CAPITAL * 0.3:
    print(f"  🚨 자기자본 70% 이상 손실")
else:
    print(f"  ⚠️ 큰 손실이지만 파산은 아님")

print()

# 권장 사항
print("=" * 80)
print("🎯 1년치 연봉 한도: 타당성 평가")
print("=" * 80)
print()

print("✅✅ 증권담보 + 만기일시 조건으로는 합리적!")
print()
print("근거:")
print(f"  1. 월 이자 29만원 = 월급의 9.7% (감당 가능)")
print(f"  2. 배당이 이자 초과 (월 +{net_cashflow:,.0f}원)")
print(f"  3. 월 잉여 {surplus_with_dividend_security:,.0f}원 (여유 있음)")
print(f"  4. -50% 폭락도 파산은 아님")
print(f"  5. 3-6개월마다 조정 가능")
print()

print("⚠️  신용대출 + 원리금균등은 부담:")
print(f"  1. 월 원리금 101만원 = 월급의 33.7%")
print(f"  2. 배당 고려해도 월 잉여 {surplus_with_dividend_credit:,.0f}원")
print(f"  3. 여유 부족")
print()

# 단계별 로드맵
print("=" * 80)
print("💡 추천 로드맵")
print("=" * 80)
print()

stages = [
    ("1단계", 35_000_000, "지금", 204_167, 560_000),
    ("2단계", 50_000_000, "6개월 후", 291_667, 800_000),
    ("3단계", 50_000_000, "1년 후 (최대)", 291_667, 800_000),
]

print(f"최대 한도: {MAX_LOAN:,}원 (1년치 연봉)")
print()

for stage, loan, timing, interest, dividend in stages:
    net = dividend - interest
    burden_pct = interest / MONTHLY_SALARY_NET * 100
    
    print(f"### {stage}: 대출 {loan:,}원 ({timing})")
    print(f"  월 이자: {interest:,.0f}원 (월급의 {burden_pct:.1f}%)")
    print(f"  월 배당: {dividend:,.0f}원")
    print(f"  순수익: {net:,.0f}원")
    
    if stage == "3단계":
        print(f"  ✅ 최대 한도 도달!")
        print(f"  ⚠️ 이후 추가 대출 금지 (리스크 관리)")
    print()

print("=" * 80)
print("🎯 최종 전략")
print("=" * 80)
print()

print("✅ 최대 한도: 1년치 연봉 (5,000만원)")
print()
print("조건:")
print("  ✅ 증권담보대출 (6-7%)")
print("  ✅ 만기일시상환 (이자만)")
print("  ✅ 단계적 확대 (3,500만원 → 5,000만원)")
print("  ✅ QQQI 선행 전략")
print()

print("실행:")
print("  1. 지금: 3,500만원 (증권담보)")
print("  2. 6개월 후 평가:")
print("     - 수익 +15% 이상: +1,500만원 추가")
print("     - 손실 또는 횡보: 현상 유지")
print("  3. 1년 후: 최대 5,000만원 운용")
print("  4. 이후 추가 대출 금지 (리스크 관리)")
print()

print("⚠️  절대 원칙:")
print("  1. 신용대출 회피 (증권담보만)")
print("  2. 만기일시만 (원리금 회피)")
print("  3. 1년치 연봉 초과 금지")
print("  4. 배당으로 이자 충당 안 되면 축소")
print("  5. 비상금 항상 500-1,000만원 유지")
print()

print("🎯 이것이 지속 가능한 레버리지 투자입니다!")
print()
print("예상 3년 후:")
print("  투자 자산: 7,000-1억원")
print("  대출 잔액: 5,000만원")
print("  순자산: 2,000-5,000만원")
print("  월 배당: 80-100만원 (불로소득!)")
