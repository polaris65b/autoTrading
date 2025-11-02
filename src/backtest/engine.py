"""
백테스팅 엔진
메인 로직 구현
"""

from datetime import datetime
from typing import Optional
import pandas as pd
from loguru import logger

from src.backtest.portfolio import Portfolio
from src.strategy.base import BaseStrategy
from src.config.settings import get_settings


class BacktestEngine:
    """백테스팅 엔진"""

    def __init__(
        self,
        initial_cash: Optional[float] = None,
        commission_rate: Optional[float] = None
    ):
        """
        초기화
        
        Args:
            initial_cash: 초기 자본금
            commission_rate: 수수료율
        """
        settings = get_settings()
        
        self.initial_cash = initial_cash or settings.DEFAULT_INITIAL_CASH
        self.commission_rate = commission_rate or settings.DEFAULT_COMMISSION
        
        self.portfolio = Portfolio(
            initial_cash=self.initial_cash,
            commission_rate=self.commission_rate
        )
        
        self.strategy: Optional[BaseStrategy] = None
        self.results: pd.DataFrame = pd.DataFrame()

    def set_strategy(self, strategy: BaseStrategy):
        """전략 설정"""
        self.strategy = strategy
        logger.info(f"전략 설정: {strategy.name}")

    def run(
        self,
        data: pd.DataFrame,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        백테스팅 실행
        
        Args:
            data: OHLCV 데이터프레임
            start_date: 시작일
            end_date: 종료일
        
        Returns:
            백테스팅 결과 데이터프레임
        """
        if self.strategy is None:
            raise ValueError("전략이 설정되지 않았습니다")
        
        if not self.strategy.validate_data(data):
            raise ValueError("데이터 유효성 검증 실패")
        
        # 날짜 필터링
        if start_date:
            data = data[data.index >= start_date]
        if end_date:
            data = data[data.index <= end_date]
        
        logger.info(f"백테스팅 시작: {len(data)}개 일봉")
        
        # 전략 초기화
        self.strategy.reset()
        
        # 신호 생성
        data_with_signals = self.strategy.generate_signals(data)
        
        # 백테스팅 실행
        for idx, (date, row) in enumerate(data_with_signals.iterrows()):
            current_price = row["Close"]
            
            # 포트폴리오 가격 업데이트
            for ticker in self.portfolio.positions.keys():
                self.portfolio.update_price(ticker, current_price)
            
            # 신호 처리
            signal = row.get("Signal", 0)
            if signal != 0:
                # 포지션 사이징 계산
                portfolio_value = self.portfolio.total_value
                ticker = row.get("Ticker", "UNKNOWN")
                
                quantity = self.strategy.calculate_position_size(
                    portfolio_value=portfolio_value,
                    price=current_price,
                    signal=signal,
                    current_quantity=self.portfolio.get_position(ticker).quantity if self.portfolio.get_position(ticker) else 0
                )
                
                # 거래 실행
                if quantity > 0:
                    try:
                        self.portfolio.buy(ticker, quantity, current_price, date)
                    except Exception as e:
                        logger.warning(f"매수 실패 [{ticker}] {e}")
                elif quantity < 0:
                    try:
                        self.portfolio.sell(ticker, abs(quantity), current_price, date)
                    except Exception as e:
                        logger.warning(f"매도 실패 [{ticker}] {e}")
            
            # 스냅샷
            self.portfolio.snapshot(date)
        
        logger.info("백테스팅 완료")
        
        # 결과 정리
        self.results = pd.DataFrame(self.portfolio.equity_curve)
        if not self.results.empty:
            self.results.set_index("date", inplace=True)
        
        return self.results

    def get_summary(self) -> dict:
        """백테스팅 결과 요약"""
        if self.results.empty:
            return {}
        
        final_value = self.results["total_value"].iloc[-1]
        total_return = self.portfolio.total_profit_loss_pct
        
        return {
            "Strategy": self.strategy.name if self.strategy else "N/A",
            "Initial Cash": f"${self.initial_cash:,.2f}",
            "Final Value": f"${final_value:,.2f}",
            "Total Return": f"{total_return:.2f}%",
            "Total Trades": len(self.portfolio.trades),
            "Num Positions": len(self.portfolio.positions)
        }

    def get_holdings(self) -> pd.DataFrame:
        """현재 보유 종목"""
        return self.portfolio.get_holdings_summary()

