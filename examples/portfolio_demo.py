#!/usr/bin/env python3
"""
포트폴리오 관리 데모 스크립트
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.backtest.portfolio import Portfolio
from src.utils.logger import setup_logger
from datetime import datetime, timedelta

logger = setup_logger()


def portfolio_demo():
    """포트폴리오 데모"""
    logger.info("포트폴리오 데모 시작")
    
    portfolio = Portfolio(
        initial_cash=100_000,
        commission_rate=0.001
    )
    
    logger.info(f"초기 자본금: ${portfolio.initial_cash:,.2f}")
    logger.info(f"수수료율: {portfolio.commission_rate*100:.2f}%")
    
    base_date = datetime.now()
    prices = [150, 155, 160, 158, 165]
    
    logger.info(f"\n{'='*70}")
    logger.info("거래 시뮬레이션")
    logger.info(f"{'='*70}")
    
    for i, price in enumerate(prices):
        date = base_date + timedelta(days=i)
        
        # 기존 포지션 가격 업데이트
        if i > 0:
            portfolio.update_price("AAPL", price)
        
        # 매수/매도
        if i == 0:
            quantity = 100
            portfolio.buy("AAPL", quantity, price, date)
            logger.info(f"[{date.strftime('%Y-%m-%d')}] 매수: {quantity}주 @ ${price:.2f}")
        elif i == 3:
            quantity = 50
            portfolio.sell("AAPL", quantity, price, date)
            logger.info(f"[{date.strftime('%Y-%m-%d')}] 매도: {quantity}주 @ ${price:.2f}")
        
        # 스냅샷
        portfolio.snapshot(date)
        
        # 일일 결과
        logger.info(f"  → 현금: ${portfolio.cash:,.2f} | "
                   f"총 자산: ${portfolio.total_value:,.2f} | "
                   f"수익률: {portfolio.total_profit_loss_pct:.2f}%")
    
    # 최종 결과
    logger.info(f"\n{'='*70}")
    logger.info("최종 결과")
    logger.info(f"{'='*70}")
    logger.info(f"총 자산: ${portfolio.total_value:,.2f}")
    logger.info(f"현금: ${portfolio.cash:,.2f}")
    logger.info(f"평가금: ${portfolio.total_market_value:,.2f}")
    logger.info(f"총 수익률: {portfolio.total_profit_loss_pct:.2f}%")
    logger.info(f"총 거래 횟수: {len(portfolio.trades)}")
    
    # 보유 종목
    holdings = portfolio.get_holdings_summary()
    if not holdings.empty:
        logger.info(f"\n보유 종목:")
        print("\n", holdings.to_string(index=False))
    
    # 거래 내역
    if portfolio.trades:
        logger.info(f"\n거래 내역:")
        for trade in portfolio.trades:
            logger.info(f"  [{trade.date.strftime('%Y-%m-%d')}] "
                       f"{trade.action}: {trade.quantity}주 @ ${trade.price:.2f}")
    
    logger.info(f"\n{'='*70}")
    logger.info("포트폴리오 데모 완료")


if __name__ == "__main__":
    portfolio_demo()

