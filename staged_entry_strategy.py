"""
단계적 진입 전략 시뮬레이션
현재 고점 우려 → 분할 매수
"""

LOAN_AMOUNT = 35_000_000
INITIAL_CAPITAL = 10_000_000
TOTAL = LOAN_AMOUNT + INITIAL_CAPITAL
MONTHLY_INTEREST = LOAN_AMOUNT * 0.07 / 12

print("=" * 80)
print("단계적 진입 전략")
print("=" * 80)
print()

# 방안 1: QQQI 선행 투자
print("### 📌 방안 1: QQQI 선행 → 하락 시 TQQQ 추가 (추천!)")
print()
print("🔹 1단계: 오늘 (2025-11-07)")
print(f"  - 대출 실행: {LOAN_AMOUNT:,}원 (만기일시, 7%)")
print(f"  - QQQI 100% 투자: {TOTAL:,}원")
print(f"  - 월 이자: {MONTHLY_INTEREST:,.0f}원")
print()
print("🔹 2단계: 2-3개월 대기")
print(f"  - QQQI 배당 수령: 월 약 21만원 (이자 충당)")
print(f"  - 예상 수익: +10~15% (배당 + 가격 상승)")
print(f"  - 시장 관찰: QQQ 200일선 체크")
print()
print("🔹 3단계: 200일선 이탈 시 (하락장)")
print(f"  - QQQI 50% 매도 → TQQQ 50% 매수")
print(f"  - TQQQ 진입가: 현재가 대비 -15~20% 예상")
print(f"  - Shannon 50:50 완성")
print()
print("장점:")
print("  ✅ 고점 매수 회피")
print("  ✅ 저점 진입 기회 확보")
print("  ✅ 배당으로 이자 충당")
print("  ✅ 심리적 안정")
print()
print("단점:")
print("  ⚠️ 추가 상승 시 기회 손실 (TQQQ 놓침)")
print("  ⚠️ 조정 없으면 진입 타이밍 애매")
print()

# 방안 2: 분할 매수
print("=" * 80)
print("### 📌 방안 2: 분할 매수")
print()

stages = [
    ("1차", 15_000_000, "즉시 진입 (33%)"),
    ("2차", 15_000_000, "2주 후 또는 -5% 조정 시"),
    ("3차", 15_000_000, "1개월 후 또는 -10% 조정 시"),
]

print(f"총 투자금: {TOTAL:,}원")
print()
for stage_name, amount, condition in stages:
    print(f"🔹 {stage_name}: {amount:,}원 ({amount/TOTAL*100:.1f}%)")
    print(f"   조건: {condition}")
    print()

print("장점:")
print("  ✅ 리스크 분산")
print("  ✅ 평균 단가 낮출 기회")
print("  ✅ 심리적 부담 감소")
print()
print("단점:")
print("  ⚠️ 계속 상승 시 일부만 투자")
print("  ⚠️ 복잡한 실행")
print()

# 방안 3: 대출 금액 축소
print("=" * 80)
print("### 📌 방안 3: 대출 금액 축소 (안전)")
print()

reduced_loan = 20_000_000
reduced_total = reduced_loan + INITIAL_CAPITAL
reduced_interest = reduced_loan * 0.07 / 12

print(f"대출: {LOAN_AMOUNT:,}원 → {reduced_loan:,}원")
print(f"총 투자: {TOTAL:,}원 → {reduced_total:,}원")
print(f"월 이자: {MONTHLY_INTEREST:,.0f}원 → {reduced_interest:,.0f}원")
print()
print("장점:")
print("  ✅ 리스크 크게 감소")
print("  ✅ 조정 시 추가 대출 여력")
print("  ✅ 심리적 안정")
print()
print("단점:")
print("  ⚠️ 수익 규모 감소")
print()

# 시나리오 분석
print("=" * 80)
print("📊 시나리오별 손익 분석 (3개월)")
print("=" * 80)
print()

scenarios = [
    ("추가 상승 +10%", 1.10, "조정 없이 계속 상승"),
    ("조정 후 회복 -10%→+5%", 0.95, "단기 조정 후 회복"),
    ("큰 조정 -20%", 0.80, "시장 충격"),
]

for scenario_name, final_mult, description in scenarios:
    print(f"### {scenario_name}: {description}")
    
    # 방안 1: QQQI 100%
    qqqi_return = 0.15  # QQQI는 안정적 +15% (배당 포함)
    value_qqqi = TOTAL * (1 + qqqi_return)
    
    # 방안 2: Shannon 50:50 즉시
    tqqq_return = final_mult - 1
    qqqi_return_2 = 0.15
    value_shannon = (TOTAL * 0.5 * (1 + tqqq_return)) + (TOTAL * 0.5 * (1 + qqqi_return_2))
    
    profit_qqqi = value_qqqi - TOTAL
    profit_shannon = value_shannon - TOTAL
    
    print(f"  QQQI 100%: {value_qqqi:,.0f}원 (수익: {profit_qqqi:,.0f}원, {profit_qqqi/TOTAL*100:+.1f}%)")
    print(f"  Shannon 50:50: {value_shannon:,.0f}원 (수익: {profit_shannon:,.0f}원, {profit_shannon/TOTAL*100:+.1f}%)")
    print(f"  차이: {profit_qqqi - profit_shannon:,.0f}원")
    print()

print("=" * 80)
print("🎯 최종 추천")
print("=" * 80)
print()
print("✅ 방안 1 추천: QQQI 100% 선행 투자")
print()
print("이유:")
print("  1. 현재 QQQ가 200일선 대비 +13.69% (과열)")
print("  2. TQQQ 소폭 조정 중이지만 고점 부근")
print("  3. 2-3개월 대기 시 더 좋은 진입점 가능")
print("  4. QQQI 배당으로 이자 충당 가능")
print("  5. 심리적 안정 (조정 와도 손실 적음)")
print()
print("실행 계획:")
print("  1. 대출 3,500만원 (만기일시, 7%)")
print("  2. QQQI 4,500만원 전량 매수")
print("  3. 2-3개월 배당 수령하며 대기")
print("  4. QQQ 200일선 이탈 시 Shannon으로 전환")
print("     (QQQI 50% → TQQQ 50%)")
print()
print("⚠️  만약 계속 상승하면?")
print("  → QQQI도 상승 + 배당 받으므로 손해는 아님")
print("  → 단지 TQQQ의 추가 상승을 놓칠 뿐")
print("  → 안전을 우선하는 선택")

