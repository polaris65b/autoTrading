#!/usr/bin/env python3
"""
설정 파일 사용 데모
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.loader import load_config
from src.utils.logger import setup_logger

logger = setup_logger()


def config_demo():
    """설정 파일 데모"""
    logger.info("설정 파일 데모 시작")
    
    # 설정 파일 경로
    config_path = project_root / "config.yml.example"
    
    logger.info(f"설정 파일 로드: {config_path}")
    config = load_config(config_path)
    
    logger.info("\n" + "="*70)
    logger.info("백테스팅 설정")
    logger.info("="*70)
    logger.info(f"기간: {config.backtest.start_date} ~ {config.backtest.end_date}")
    logger.info(f"초기 자본금: ${config.backtest.initial_cash:,.0f}")
    logger.info(f"수수료율: {config.backtest.commission_rate*100:.2f}%")
    
    logger.info("\n" + "="*70)
    logger.info("거래 종목")
    logger.info("="*70)
    logger.info(f"종목: {', '.join(config.assets.tickers)}")
    
    logger.info("\n" + "="*70)
    logger.info("전략 설정")
    logger.info("="*70)
    for strategy in config.portfolio.strategies:
        status = "🟢 활성" if strategy.enabled else "🔴 비활성"
        logger.info(f"{status}: {strategy.name}")
        if strategy.enabled and strategy.params:
            params = strategy.params
            if params.rebalance_freq:
                logger.info(f"  - 리밸런싱 주기: {params.rebalance_freq}일")
            if params.fast_period and params.slow_period:
                logger.info(f"  - 이동평균: {params.fast_period} / {params.slow_period}")
            if params.target_weights:
                logger.info(f"  - 목표 비중:")
                for tw in params.target_weights:
                    logger.info(f"    * {tw.ticker}: {tw.weight*100:.0f}%")
    
    logger.info("\n" + "="*70)
    logger.info("리스크 관리")
    logger.info("="*70)
    logger.info(f"최대 보유 종목 수: {config.risk.max_positions}")
    logger.info(f"종목당 최대 비중: {config.risk.max_position_weight*100:.0f}%")
    
    stop_loss_status = "🟢 ON" if config.risk.stop_loss.enabled else "🔴 OFF"
    logger.info(f"손절: {stop_loss_status}")
    if config.risk.stop_loss.enabled:
        logger.info(f"  - 기준: {config.risk.stop_loss.threshold*100:.0f}%")
    
    take_profit_status = "🟢 ON" if config.risk.take_profit.enabled else "🔴 OFF"
    logger.info(f"익절: {take_profit_status}")
    if config.risk.take_profit.enabled:
        logger.info(f"  - 기준: {config.risk.take_profit.threshold*100:.0f}%")
    
    logger.info("\n" + "="*70)
    logger.info("리포트 설정")
    logger.info("="*70)
    logger.info(f"결과 저장: {'🟢 ON' if config.report.save_results else '🔴 OFF'}")
    logger.info(f"차트 생성: {'🟢 ON' if config.report.generate_charts else '🔴 OFF'}")
    
    logger.info("\n" + "="*70)
    logger.info("설정 파일 데모 완료")
    logger.info("="*70)


if __name__ == "__main__":
    config_demo()

