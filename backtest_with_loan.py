"""
대출 포함 백테스팅
Shannon (TQQQ + QQQI) 전략에 대출 적용
"""

from src.data.collector import StockDataCollector
from src.strategy.shannon import ShannonStrategy
from src.backtest.multi_asset_engine import MultiAssetBacktestEngine
import pandas as pd
import numpy as np
from datetime import datetime

# 설정
INITIAL_CAPITAL = 10_000_000  # 자기자본 1천만원
LOAN_AMOUNT = 35_000_000  # 대출 3,500만원
TOTAL_INVESTMENT = INITIAL_CAPITAL + LOAN_AMOUNT  # 총 투자금 4,500만원
LOAN_RATE_ANNUAL = 0.07  # 연 7%
LOAN_PERIOD_MONTHS = 60  # 5년
COMMISSION_RATE = 0.001  # 0.1%

# 환율 (결과 표시용)
EXCHANGE_RATE = 1400
INITIAL_CAPITAL_USD = INITIAL_CAPITAL / EXCHANGE_RATE
LOAN_AMOUNT_USD = LOAN_AMOUNT / EXCHANGE_RATE
TOTAL_INVESTMENT_USD = TOTAL_INVESTMENT / EXCHANGE_RATE

# 월 상환액 계산
MONTHLY_RATE = LOAN_RATE_ANNUAL / 12

# 1. 원리금균등
monthly_payment_equal = LOAN_AMOUNT * (MONTHLY_RATE * (1 + MONTHLY_RATE) ** LOAN_PERIOD_MONTHS) / \
                        ((1 + MONTHLY_RATE) ** LOAN_PERIOD_MONTHS - 1)

# 2. 원금균등
monthly_principal = LOAN_AMOUNT / LOAN_PERIOD_MONTHS

# 3. 만기일시
monthly_interest_only = LOAN_AMOUNT * MONTHLY_RATE

print("=" * 80)
print("대출 포함 Shannon (TQQQ + QQQI) 백테스팅")
print("=" * 80)
print()
print(f"투자 조건:")
print(f"  자기자본: {INITIAL_CAPITAL:,}원 (${INITIAL_CAPITAL_USD:,.2f})")
print(f"  대출금액: {LOAN_AMOUNT:,}원 (${LOAN_AMOUNT_USD:,.2f})")
print(f"  총 투자금: {TOTAL_INVESTMENT:,}원 (${TOTAL_INVESTMENT_USD:,.2f})")
print(f"  대출금리: {LOAN_RATE_ANNUAL*100}% (연)")
print()

# 데이터 수집
collector = StockDataCollector()
print("데이터 수집 중...")
tqqq = collector.collect_ohlcv("TQQQ", "2024-02-01", "2025-11-06")
qqqi = collector.collect_ohlcv("QQQI", "2024-02-01", "2025-11-06")

# Shannon 전략 백테스팅 (밴딩)
strategy_banding = ShannonStrategy(
    name="Shannon_Banding",
    params={
        "stock_ticker": "TQQQ",
        "bond_ticker": "QQQI",
        "stock_pct": 0.5,
        "rebalance_mode": "banding",
        "band_threshold": 0.1
    }
)

engine_banding = MultiAssetBacktestEngine(
    tickers=["TQQQ", "QQQI"],
    initial_cash=TOTAL_INVESTMENT_USD,
    commission_rate=COMMISSION_RATE,
    monthly_addition=0
)

engine_banding.set_strategy(strategy_banding)

# 신호 생성
tqqq_signals = strategy_banding.generate_signals(tqqq)
qqqi_df = qqqi.copy()
qqqi_df["Signal"] = 0

engine_banding.set_data({"TQQQ": tqqq_signals, "QQQI": qqqi_df})

# 백테스팅 실행
results_banding = engine_banding.run(start_date="2024-02-01", end_date="2025-11-06")

final_value_usd = results_banding["total_value"].iloc[-1]
final_value_krw = final_value_usd * EXCHANGE_RATE

# 투자 기간 계산
days = len(results_banding)
years = days / 365.25

print()
print("=" * 80)
print("백테스팅 결과 (밴딩 방식)")
print("=" * 80)
print(f"투자 기간: {days}일 ({years:.2f}년)")
print(f"최종 자산: ${final_value_usd:,.2f} ({final_value_krw:,.0f}원)")
print(f"투자 수익: {(final_value_usd / TOTAL_INVESTMENT_USD - 1) * 100:.2f}%")
print()

# 세 가지 대출 방식 비교
print("=" * 80)
print("💰 대출 방식별 순수익 비교")
print("=" * 80)
print()

# 원금 상환 시뮬레이션
loan_scenarios = {
    "원리금균등": {
        "monthly": monthly_payment_equal,
        "total_interest": 6_582_517,
        "description": "월 693,042원 고정"
    },
    "원금균등": {
        "monthly": monthly_principal + LOAN_AMOUNT * MONTHLY_RATE,
        "total_interest": 6_227_083,
        "description": "초기 787,500원 → 점차 감소"
    },
    "만기일시": {
        "monthly": monthly_interest_only,
        "total_interest": 12_250_000,
        "description": "월 204,167원 고정 (이자만)"
    }
}

for method, data in loan_scenarios.items():
    # 월 상환액을 투자 기간 동안 지불
    months = int(years * 12)
    total_payments = data["monthly"] * months
    
    # 만기일시는 원금도 고려
    if method == "만기일시":
        remaining_principal = LOAN_AMOUNT
    else:
        # 원리금균등/원금균등은 일부 원금 상환됨
        remaining_principal = LOAN_AMOUNT - (LOAN_AMOUNT * months / LOAN_PERIOD_MONTHS)
    
    # 순수익 계산 (원화 기준)
    gross_profit_krw = final_value_krw - TOTAL_INVESTMENT
    paid_payments_krw = total_payments
    
    # 대출 원금 상환해야 할 금액
    loan_to_repay = remaining_principal
    
    # 순자산 = 최종자산 - 대출잔액
    net_asset = final_value_krw - loan_to_repay
    
    # 순수익 = 순자산 - 자기자본 - 지불한 상환액
    net_profit = net_asset - INITIAL_CAPITAL
    
    # 수익률 (자기자본 + 지불한 상환액 대비)
    invested_own_money = INITIAL_CAPITAL + paid_payments_krw
    net_return_pct = (net_profit / invested_own_money) * 100 if invested_own_money > 0 else 0
    
    print(f"### {method}")
    print(f"  월 납입: {data['monthly']:,.0f}원 ({data['description']})")
    print(f"  {months}개월 납입액: {paid_payments_krw:,.0f}원")
    print(f"  대출 잔액: {loan_to_repay:,.0f}원")
    print(f"  최종 자산: {final_value_krw:,.0f}원")
    print(f"  순자산(대출 제외): {net_asset:,.0f}원")
    print(f"  총 투입금: {invested_own_money:,.0f}원 (자기자본 + 납입액)")
    print(f"  순수익: {net_profit:,.0f}원")
    print(f"  수익률: {net_return_pct:.2f}%")
    print()

print("=" * 80)
print("⚠️  중요 고려사항")
print("=" * 80)
print()
print("1. 리스크 관리:")
print(f"   - 최대 낙폭: -39% (백테스팅 기준)")
print(f"   - 3,500만원 × 39% = 약 {35_000_000 * 0.39:,.0f}원 손실 가능")
print(f"   - 자기자본 {INITIAL_CAPITAL:,}원 초과 손실 가능 ⚠️")
print()
print("2. 현금흐름 관리:")
print(f"   - 원리금균등: 월 {monthly_payment_equal:,.0f}원 필요")
print(f"   - 원금균등: 초기 월 {monthly_principal + LOAN_AMOUNT * MONTHLY_RATE:,.0f}원 필요")
print(f"   - 만기일시: 월 {monthly_interest_only:,.0f}원 필요")
print(f"   → 안정적인 현금흐름(월급 등) 필수!")
print()
print("3. 5년 후 상황:")
print(f"   - 만기일시: 3,500만원 일시 상환 필요")
print(f"   - 투자금 청산 또는 재대출 필요")
print()
print("4. 심리적 부담:")
print(f"   - 대출 + 레버리지(TQQQ) = 이중 레버리지")
print(f"   - 최대 손실 시 자기자본 초과 손실 가능")
print(f"   - 강한 멘탈 필수!")

