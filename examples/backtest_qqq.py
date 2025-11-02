#!/usr/bin/env python3
"""
QQQ Buy & Hold 백테스팅
2010년부터 현재까지의 성과 분석
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.collector import StockDataCollector
from src.backtest.simple_engine import SimpleBacktestEngine
from src.strategy.buyhold import BuyHoldStrategy
from src.utils.logger import setup_logger
from datetime import datetime

logger = setup_logger()


def backtest_qqq():
    """QQQ Buy & Hold 백테스팅"""
    logger.info("="*70)
    logger.info("QQQ Buy & Hold 백테스팅 (2010 ~ 현재)")
    logger.info("="*70)
    
    # 1. 데이터 수집
    ticker = "QQQ"
    collector = StockDataCollector()
    
    logger.info(f"\n{ticker} 데이터 수집 중...")
    try:
        df = collector.collect_ohlcv(
            ticker=ticker,
            start_date="2010-01-01"
        )
        logger.info(f"데이터 수집 완료: {len(df)}개 일봉")
        logger.info(f"기간: {df.index[0]} ~ {df.index[-1]}")
    except Exception as e:
        logger.error(f"데이터 수집 실패: {e}")
        return
    
    # 2. 전략 설정
    strategy = BuyHoldStrategy(name="BuyHold", params={"position_pct": 1.0})
    logger.info(f"\n전략: {strategy.name}")
    
    # 3. 백테스팅 실행
    engine = SimpleBacktestEngine(
        ticker=ticker,
        initial_cash=100_000,
        commission_rate=0.001
    )
    
    engine.set_strategy(strategy)
    
    logger.info("\n백테스팅 실행 중...")
    try:
        results = engine.run(df)
        logger.info("백테스팅 완료")
    except Exception as e:
        logger.error(f"백테스팅 실패: {e}")
        return
    
    # 4. 결과 출력
    summary = engine.get_summary()
    
    logger.info("\n" + "="*70)
    logger.info("백테스팅 결과 요약")
    logger.info("="*70)
    
    for key, value in summary.items():
        logger.info(f"{key}: {value}")
    
    # 5. 상세 분석
    logger.info("\n" + "="*70)
    logger.info("상세 분석")
    logger.info("="*70)
    
    # 거래 내역
    portfolio = engine.portfolio
    logger.info(f"\n총 거래 횟수: {len(portfolio.trades)}")
    if portfolio.trades:
        first_trade = portfolio.trades[0]
        logger.info(f"첫 매수: {first_trade.date.strftime('%Y-%m-%d')} "
                   f"{first_trade.quantity}주 @ ${first_trade.price:.2f}")
    
    # 보유 종목
    holdings = engine.get_holdings()
    if not holdings.empty:
        logger.info("\n현재 보유 종목:")
        print(holdings.to_string(index=False))
    
    # 수익률 계산
    final_price = results["total_value"].iloc[-1]
    initial_price = results["total_value"].iloc[0]
    total_return_pct = ((final_price / initial_price) - 1) * 100
    
    logger.info(f"\n초기 가치: ${initial_price:,.2f}")
    logger.info(f"최종 가치: ${final_price:,.2f}")
    logger.info(f"총 수익률: {total_return_pct:.2f}%")
    
    # 최고점/최저점
    max_value = results["total_value"].max()
    min_value = results["total_value"].min()
    max_date = results["total_value"].idxmax()
    min_date = results["total_value"].idxmin()
    
    logger.info(f"\n최고점: ${max_value:,.2f} ({max_date.strftime('%Y-%m-%d')})")
    logger.info(f"최저점: ${min_value:,.2f} ({min_date.strftime('%Y-%m-%d')})")
    
    # 최대 낙폭 (Max Drawdown)
    max_drawdown = 0
    peak = results["total_value"].iloc[0]
    
    for value in results["total_value"]:
        if value > peak:
            peak = value
        drawdown = ((value - peak) / peak) * 100
        if drawdown < max_drawdown:
            max_drawdown = drawdown
    
    logger.info(f"최대 낙폭: {max_drawdown:.2f}%")
    
    # 연도별 수익률 (간단 버전)
    logger.info("\n" + "="*70)
    logger.info("주요 시점 분석")
    logger.info("="*70)
    
    # 특정 시점들의 가치 출력
    checkpoints = [
        "2010-12-31",
        "2012-12-31",
        "2015-12-31",
        "2018-12-31",
        "2020-12-31",
        "2022-12-31",
        "2024-12-31"
    ]
    
    logger.info("\n연도별 포트폴리오 가치:")
    for checkpoint in checkpoints:
        try:
            value = results.loc[results.index <= checkpoint]["total_value"].iloc[-1]
            return_pct = ((value / initial_price) - 1) * 100
            logger.info(f"{checkpoint[:4]}년: ${value:,.2f} ({return_pct:+.2f}%)")
        except (IndexError, KeyError):
            pass
    
    logger.info("\n" + "="*70)
    logger.info("백테스팅 완료")
    logger.info("="*70)


if __name__ == "__main__":
    backtest_qqq()

