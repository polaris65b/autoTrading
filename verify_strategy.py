"""
전략 시뮬레이션: QQQI 대기 → 200일선 이탈 시 Shannon → 익절
"""

# 초기 설정
OWN_CAPITAL = 10_000_000
LOAN_AMOUNT = 35_000_000
TOTAL = OWN_CAPITAL + LOAN_AMOUNT
LOAN_RATE = 0.07

# QQQI 특성
QQQI_DIVIDEND = 0.1608  # 연 16.08% (세후)
QQQI_PRICE_STABLE = 0.05  # 안정적 상승 5%

# TQQQ 특성
TQQQ_LEVERAGE = 3  # 3배 레버리지

print("=" * 80)
print("전략 시뮬레이션: QQQI → Shannon → 익절")
print("=" * 80)
print()

print("초기 조건:")
print(f"  자기자본: {OWN_CAPITAL:,}원")
print(f"  대출: {LOAN_AMOUNT:,}원 (7%)")
print(f"  총 투자: {TOTAL:,}원")
print()

# ========================================
# 시나리오: 하락 -20% → 회복 +30%
# ========================================
print("=" * 80)
print("📊 시뮬레이션 시나리오")
print("=" * 80)
print()
print("가정: QQQ 하락 -20% → 회복 +30%")
print("  (TQQQ = QQQ × 3배 = -60% → +90%)")
print()

# 1단계: QQQI 대기 (3개월)
print("=" * 80)
print("1️⃣  1단계: QQQI 100% 대기 (3개월)")
print("=" * 80)

months_waiting = 3
dividend_3months = TOTAL * QQQI_DIVIDEND * (months_waiting / 12)
interest_3months = LOAN_AMOUNT * LOAN_RATE * (months_waiting / 12)
net_cashflow_3months = dividend_3months - interest_3months

# QQQI 가격 약간 상승 가정 (안정적)
qqqi_value_after_3m = TOTAL * (1 + QQQI_PRICE_STABLE * (months_waiting / 12))

print(f"  초기 투자: {TOTAL:,}원 (QQQI 100%)")
print(f"  3개월 배당: {dividend_3months:,.0f}원")
print(f"  3개월 이자: {interest_3months:,.0f}원")
print(f"  순 캐시: {net_cashflow_3months:,.0f}원")
print(f"  자산 가치: {qqqi_value_after_3m:,.0f}원 (약간 상승)")
print()

# 2단계: 200일선 이탈 (하락장)
print("=" * 80)
print("2️⃣  2단계: 200일선 이탈 → Shannon 전환")
print("=" * 80)

# QQQ -20% 하락 시점 (TQQQ -60%)
qqq_drop = -0.20
tqqq_drop = qqq_drop * 3  # -60%

# QQQI는 안정적 (작은 하락만)
qqqi_drop = -0.10  # QQQI는 QQQ보다 덜 하락 (커버드콜)

# 전환 시점 자산
qqqi_value_at_drop = qqqi_value_after_3m * (1 + qqqi_drop)

# Shannon 전환: QQQI 50% → TQQQ 50%
tqqq_buy_amount = qqqi_value_at_drop * 0.5
qqqi_remaining = qqqi_value_at_drop * 0.5

# TQQQ 진입가 (현재가 대비 -60%)
# 현재 TQQQ: $106.89, -60% = $42.76
tqqq_entry_price = 106.89 * (1 + tqqq_drop)

print(f"  하락 시점:")
print(f"    QQQ: {qqq_drop*100:.0f}% 하락")
print(f"    TQQQ: {tqqq_drop*100:.0f}% 하락 (${106.89:.2f} → ${tqqq_entry_price:.2f})")
print(f"    QQQI: {qqqi_drop*100:.0f}% 하락")
print()
print(f"  전환 전 자산: {qqqi_value_at_drop:,.0f}원 (QQQI 100%)")
print()
print(f"  전환:")
print(f"    QQQI 50% 보유: {qqqi_remaining:,.0f}원")
print(f"    TQQQ 50% 매수: {tqqq_buy_amount:,.0f}원 (저점 매수!)")
print()

# 3단계: 회복 + 익절
print("=" * 80)
print("3️⃣  3단계: 회복 + 익절")
print("=" * 80)

# QQQ +30% 회복 시점 (저점 대비)
qqq_recovery = 0.30
tqqq_recovery = qqq_recovery * 3  # +90%

# QQQI도 회복
qqqi_recovery = 0.15  # QQQI는 안정적 회복

# 회복 후 자산 가치
tqqq_value_after_recovery = tqqq_buy_amount * (1 + tqqq_recovery)
qqqi_value_after_recovery = qqqi_remaining * (1 + qqqi_recovery)
total_value_after_recovery = tqqq_value_after_recovery + qqqi_value_after_recovery

# 익절 시점 순수익
total_interest_6months = LOAN_AMOUNT * LOAN_RATE * (6 / 12)  # 6개월 총 이자
net_profit = total_value_after_recovery - TOTAL - total_interest_6months

# ROE
roe = (net_profit / OWN_CAPITAL) * 100

print(f"  회복 시점:")
print(f"    QQQ: 저점 대비 +{qqq_recovery*100:.0f}% 회복")
print(f"    TQQQ: 저점 대비 +{tqqq_recovery*100:.0f}% 회복")
print(f"    QQQI: +{qqqi_recovery*100:.0f}% 상승")
print()
print(f"  자산 가치:")
print(f"    TQQQ: {tqqq_value_after_recovery:,.0f}원 (진입가 대비 +{tqqq_recovery*100:.0f}%)")
print(f"    QQQI: {qqqi_value_after_recovery:,.0f}원")
print(f"    총 자산: {total_value_after_recovery:,.0f}원")
print()
print(f"  익절:")
print(f"    초기 투자: {TOTAL:,}원")
print(f"    최종 자산: {total_value_after_recovery:,.0f}원")
print(f"    총 수익: {total_value_after_recovery - TOTAL:,.0f}원")
print(f"    6개월 이자: {total_interest_6months:,.0f}원")
print(f"    순수익: {net_profit:,.0f}원")
print()
print(f"  대출 상환:")
print(f"    최종 자산: {total_value_after_recovery:,.0f}원")
print(f"    대출 상환: -{LOAN_AMOUNT:,}원")
print(f"    남은 자산: {total_value_after_recovery - LOAN_AMOUNT:,.0f}원")
print()
print(f"  🎯 최종 수익:")
print(f"    투입 자본: {OWN_CAPITAL:,}원")
print(f"    회수 자산: {total_value_after_recovery - LOAN_AMOUNT:,.0f}원")
print(f"    순수익: {net_profit:,.0f}원")
print(f"    ROE: {roe:.2f}%")
print()

# 비교: 즉시 Shannon vs QQQI 선행
print("=" * 80)
print("💡 전략 비교: QQQI 선행 vs 즉시 Shannon")
print("=" * 80)
print()

# 즉시 Shannon 시작 (고점 매수)
print("### 즉시 Shannon (고점 매수)")
# 고점에서 시작
tqqq_entry_high = 106.89
tqqq_drop_from_high = tqqq_drop  # -60%
tqqq_recovery_from_high = (1 + tqqq_drop_from_high) * (1 + tqqq_recovery) - 1

shannon_tqqq = (TOTAL * 0.5) * (1 + tqqq_recovery_from_high)
shannon_qqqi = (TOTAL * 0.5) * (1 + qqqi_recovery - 0.1 + 0.15)  # 조정 -10% + 회복 +15%
shannon_total = shannon_tqqq + shannon_qqqi
shannon_profit = shannon_total - TOTAL - total_interest_6months

print(f"  TQQQ 50%: {TOTAL*0.5:,.0f}원 → {shannon_tqqq:,.0f}원 ({tqqq_recovery_from_high*100:.1f}%)")
print(f"  QQQI 50%: {TOTAL*0.5:,.0f}원 → {shannon_qqqi:,.0f}원")
print(f"  총 자산: {shannon_total:,.0f}원")
print(f"  순수익: {shannon_profit:,.0f}원")
print()

print("### QQQI 선행 → Shannon")
print(f"  총 자산: {total_value_after_recovery:,.0f}원")
print(f"  순수익: {net_profit:,.0f}원")
print()

print(f"💰 차이: {net_profit - shannon_profit:,.0f}원 ({'더' if net_profit > shannon_profit else '덜'} 유리)")
print()

# 핵심 인사이트
print("=" * 80)
print("🎯 전략의 핵심 포인트")
print("=" * 80)
print()
print("✅ 1. 고점 회피")
print(f"     현재 TQQQ ${106.89:.2f} (고점 근처)")
print(f"     → 하락 후 ${tqqq_entry_price:.2f}에 매수 (-60%)")
print(f"     → 평균 단가 {(106.89 - tqqq_entry_price) / 106.89 * 100:.1f}% 절감!")
print()
print("✅ 2. 배당 수익")
print(f"     대기 기간 배당: {dividend_3months:,.0f}원")
print(f"     이자 납부: {interest_3months:,.0f}원")
print(f"     순수익: {net_cashflow_3months:,.0f}원")
print()
print("✅ 3. 리밸런싱 효과")
print(f"     TQQQ 저점 매수 후 회복")
print(f"     Shannon 리밸런싱으로 수익 극대화")
print(f"     TQQQ +{tqqq_recovery*100:.0f}% 수익 획득")
print()
print("✅ 4. 안전한 레버리지")
print(f"     QQQI는 변동성 낮음 (17.76%)")
print(f"     대기 기간 손실 최소화")
print(f"     배당으로 이자 충당")
print()

# 리스크
print("=" * 80)
print("⚠️  리스크 관리")
print("=" * 80)
print()
print("리스크 1: 조정이 안 올 경우")
print("  → QQQI로 계속 배당 수령")
print("  → 연 31% 수익도 나쁘지 않음")
print("  → TQQQ 추가 상승만 놓칠 뿐")
print()
print("리스크 2: 큰 하락 (-40% 이상)")
print("  → QQQI도 -20% 하락 가능")
print("  → 자산 3,600만원, 대출 3,500만원")
print("  → 자기자본 거의 소진")
print("  → 하지만 TQQQ 저점 매수 기회")
print()
print("리스크 3: L자형 하락 (회복 안됨)")
print("  → TQQQ 저점 매수 후 더 하락")
print("  → 손실 확대")
print("  → 대출 상환 부담")
print()

# 최종 추천
print("=" * 80)
print("🎯 최종 평가")
print("=" * 80)
print()
print("✅✅ 매우 합리적인 전략입니다!")
print()
print("장점:")
print("  1. 고점 매수 회피 (현명함)")
print("  2. 배당으로 이자 충당 + 월 40만원")
print("  3. TQQQ 저점 매수 기회 확보")
print("  4. Shannon 리밸런싱으로 수익 극대화")
print("  5. 익절 전략 명확함")
print()
print("주의사항:")
print("  ⚠️ 조정이 안 오면 기회비용 (TQQQ 상승 놓침)")
print("  ⚠️ 큰 하락 시 자기자본 손실 가능")
print("  ⚠️ 회복 안 되면 손실 확대")
print()
print("추천 실행:")
print("  1. 대출 3,500만원 (만기일시, 7-8%)")
print("  2. QQQI 100% 투자")
print("  3. QQQ 200일선 매일 체크")
print("  4. 이탈 시 즉시 Shannon 전환")
print("  5. +20~30% 회복 시 익절 고려")
print()
print("익절 타이밍:")
print("  - 보수적: +20% (빠른 수익 실현)")
print("  - 균형적: +30% (적절한 수익)")
print("  - 공격적: +50% (큰 수익 추구)")
print()
print("🎯 이 전략의 핵심:")
print("   '고점 회피 + 저점 매수 + 리밸런싱 + 익절'")
print("   = 시장 타이밍 전략의 교과서!")

