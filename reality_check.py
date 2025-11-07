"""
현실 체크: 2년치 연봉 대출의 실제 생활
"""

# 가정
ANNUAL_SALARY = 50_000_000
MONTHLY_SALARY_GROSS = ANNUAL_SALARY / 12
MONTHLY_SALARY_NET = 3_000_000  # 세후 실수령액 (약 60%)

LOAN_AMOUNT = 100_000_000  # 2년치 연봉
MONTHLY_PAYMENT = 2_027_639  # 원리금균등

# 생활비
RENT = 1_000_000  # 월세/관리비
LIVING = 800_000  # 생활비
INSURANCE = 200_000  # 보험 등
EMERGENCY = 200_000  # 비상금 적립

print("=" * 80)
print("🏠 현실 체크: 2년치 연봉 대출 시 실제 생활")
print("=" * 80)
print()

print("월 수입:")
print(f"  세후 월급: {MONTHLY_SALARY_NET:,}원")
print()

print("월 지출:")
print(f"  대출 상환: {MONTHLY_PAYMENT:,.0f}원 ⚠️")
print(f"  주거비: {RENT:,}원")
print(f"  생활비: {LIVING:,}원")
print(f"  보험/기타: {INSURANCE:,}원")
print(f"  비상금: {EMERGENCY:,}원")
print(f"  ──────────────────")
print(f"  합계: {MONTHLY_PAYMENT + RENT + LIVING + INSURANCE + EMERGENCY:,}원")
print()

surplus = MONTHLY_SALARY_NET - (MONTHLY_PAYMENT + RENT + LIVING + INSURANCE + EMERGENCY)
print(f"💰 월 잉여금: {surplus:,}원")
print()

if surplus < 0:
    print("🚨🚨 월급이 부족합니다!")
    print(f"   매월 {abs(surplus):,}원 적자")
    print("   → 저축 불가능")
    print("   → 여가/교제비 없음")
    print("   → 삶의 질 크게 하락")
elif surplus < 200_000:
    print("⚠️  여유 자금이 거의 없습니다")
    print("   → 비상 상황 대응 불가")
    print("   → 추가 투자 불가능")
else:
    print("✅ 여유 있음")

print()

# QQQI 배당 고려
qqqi_dividend_monthly = 1_608_000
deficit_with_dividend = MONTHLY_PAYMENT - qqqi_dividend_monthly

print("🎁 QQQI 배당금 고려:")
print(f"  월 배당: {qqqi_dividend_monthly:,}원")
print(f"  월 원리금: {MONTHLY_PAYMENT:,.0f}원")
print(f"  부족: {deficit_with_dividend:,.0f}원")
print()

surplus_with_dividend = MONTHLY_SALARY_NET - (deficit_with_dividend + RENT + LIVING + INSURANCE + EMERGENCY)
print(f"  배당 적용 후 월 잉여: {surplus_with_dividend:,}원")
print()

if surplus_with_dividend < 0:
    print("🚨 배당을 받아도 여전히 적자!")
elif surplus_with_dividend < 500_000:
    print("⚠️ 여유 자금 부족 (50만원 미만)")
else:
    print("✅ 배당 덕분에 관리 가능")

print()

# 비교: 3,500만원 vs 1억원
print("=" * 80)
print("💡 3,500만원 vs 1억원 대출 비교")
print("=" * 80)
print()

loan_35m_payment = 710_000  # 약 71만원
loan_35m_dividend = 560_000  # QQQI 배당
loan_35m_deficit = loan_35m_payment - loan_35m_dividend

print(f"### 대출 3,500만원 (증권담보, 만기일시)")
print(f"  월 이자: 204,167원 (만기일시)")
print(f"  월 배당: 560,000원")
print(f"  순수익: 355,833원 ✅")
print(f"  월 잉여: {MONTHLY_SALARY_NET - 204_167 - RENT - LIVING - INSURANCE - EMERGENCY:,}원")
print()

print(f"### 대출 1억원 (신용대출)")
print(f"  월 원리금: {MONTHLY_PAYMENT:,.0f}원")
print(f"  월 배당: {qqqi_dividend_monthly:,}원")
print(f"  부족: {deficit_with_dividend:,.0f}원")
print(f"  월 잉여: {surplus_with_dividend:,}원")
print()

print("=" * 80)
print("🎯 최종 조언")
print("=" * 80)
print()

print("✅ 귀하의 철학은 100% 옳습니다!")
print("   '부동산 < 나스닥 성장률' = 장기적으로 맞는 판단")
print()

print("⚠️⚠️  하지만 2년치 연봉은 너무 과합니다!")
print()

print("문제점:")
print("  1. 월 200만원 상환 = 월급의 67% (지속 불가능)")
print("  2. 나스닥 -50% 시 파산 (-4,000만원 부채)")
print("  3. 5년간 원리금 부담 (삶의 질 저하)")
print("  4. 실직/감봉 시 대응 불가")
print("  5. 결혼/육아 등 인생 계획 불가")
print()

print("✅✅ 현명한 접근:")
print()
print("1단계: 지금 시작 (3,500만원)")
print("  - 증권담보 3,500만원 (만기일시, 7%)")
print("  - 월 이자 20만원 (배당으로 충당)")
print("  - QQQI 100% 투자")
print("  - 스트레스 없이 운용")
print()

print("2단계: 6개월 후 (수익 +15%)")
print("  - 자산: 약 5,200만원")
print("  - 대출 2,000만원 추가")
print("  - 총 운용: 5,500-6,500만원")
print()

print("3단계: 1년 후 (누적 수익 +30%)")
print("  - 자산: 약 7,000만원")
print("  - 대출 1,500만원 추가 (필요시)")
print("  - 최대 7,000-8,000만원 운용")
print()

print("이렇게 3년에 걸쳐 점진적으로 확대하세요!")
print()

print("💰 예상 결과 (3년):")
print("  1년차: 3,500만원 → 4,600만원 (ROE 115%)")
print("  2년차: 6,000만원 → 7,800만원 (누적)")
print("  3년차: 8,000만원 → 1억+ (목표 달성)")
print()

print("🎯 핵심:")
print("  '같은 목표, 더 안전하게, 단계적으로'")
print()

print("⚠️  특히 신용대출 주의:")
print("  - 신용대출 8% > 증권담보 6-7%")
print("  - 중도상환수수료 1.5% (신용) vs 0% (증권담보)")
print("  - 원리금 vs 만기일시 부담 차이")
print()

print("💡 최종 추천:")
print("  지금: 3,500만원 (증권담보, 만기일시)")
print("  목표: 3년 내 7,000-8,000만원")
print("  방식: 단계적 확대 (수익 재투자)")
