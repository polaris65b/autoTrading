#!/usr/bin/env python3
"""
데이터 수집 예제 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.collector import StockDataCollector
from src.utils.logger import setup_logger
from datetime import datetime, timedelta

logger = setup_logger()


def collect_sample_data():
    """샘플 데이터 수집"""
    collector = StockDataCollector()
    
    tickers = ["AAPL", "GOOGL", "MSFT", "TSLA"]
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    logger.info(f"데이터 수집 시작: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    
    for ticker in tickers:
        try:
            logger.info(f"\n{'='*50}")
            logger.info(f"{ticker} 데이터 수집 시작...")
            
            df = collector.collect_ohlcv(
                ticker=ticker,
                start_date=start_date.strftime("%Y-%m-%d")
            )
            
            collector.save_to_csv(df, ticker, prefix="raw")
            logger.info(f"✅ {ticker} 수집 완료: {len(df)}개 일봉")
            
        except Exception as e:
            logger.error(f"❌ {ticker} 수집 실패: {e}")
    
    logger.info(f"\n{'='*50}")
    logger.info("데이터 수집 완료")


if __name__ == "__main__":
    collect_sample_data()

