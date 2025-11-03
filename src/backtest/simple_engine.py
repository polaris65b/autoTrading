"""
단순 백테스팅 엔진
Buy & Hold 같은 단일 종목 전략용
"""

from datetime import datetime
from typing import Optional
import pandas as pd
from loguru import logger

from src.backtest.portfolio import Portfolio
from src.strategy.base import BaseStrategy
from src.config.settings import get_settings
from src.utils.metrics import calculate_all_metrics


class SimpleBacktestEngine:
    """단순 백테스팅 엔진 (단일 종목용)"""

    def __init__(
        self,
        ticker: str,
        initial_cash: Optional[float] = None,
        commission_rate: Optional[float] = None
    ):
        """
        초기화
        
        Args:
            ticker: 거래할 종목
            initial_cash: 초기 자본금
            commission_rate: 수수료율
        """
        settings = get_settings()
        
        self.ticker = ticker
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
            if self.ticker in self.portfolio.positions:
                self.portfolio.update_price(self.ticker, current_price)
            
            # 신호 처리
            signal = row.get("Signal", 0)
            if signal != 0:
                # 포지션 사이징 계산
                portfolio_value = self.portfolio.total_value
                current_quantity = 0
                if self.portfolio.get_position(self.ticker):
                    current_quantity = self.portfolio.get_position(self.ticker).quantity
                
                # Mode 정보 전달 (MovingAverageShannonHybrid 전략용)
                mode = row.get("Mode", None)
                ticker_param = row.get("Ticker", self.ticker)
                bb_width = row.get("BB_Width", None)
                
                quantity = self.strategy.calculate_position_size(
                    portfolio_value=portfolio_value,
                    price=current_price,
                    signal=signal,
                    current_quantity=current_quantity,
                    cash=self.portfolio.cash,
                    commission_rate=self.commission_rate,
                    mode=mode,
                    ticker=ticker_param,
                    bb_width=bb_width
                )
                
                # 거래 실행 (리밸런싱 포함)
                if quantity > 0:
                    try:
                        self.portfolio.buy(self.ticker, quantity, current_price, date)
                        if signal == 2:
                            logger.debug(f"리밸런싱 매수 [{self.ticker}] {quantity}주 @ ${current_price:.2f}")
                    except Exception as e:
                        logger.warning(f"매수 실패 [{self.ticker}] {e}")
                elif quantity < 0:
                    try:
                        self.portfolio.sell(self.ticker, abs(quantity), current_price, date)
                        if signal == 2:
                            logger.debug(f"리밸런싱 매도 [{self.ticker}] {abs(quantity)}주 @ ${current_price:.2f}")
                    except Exception as e:
                        logger.warning(f"매도 실패 [{self.ticker}] {e}")
            
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
        
        # 연환산 수익률 계산
        days = len(self.results)
        years = days / 365.25
        annualized_return = ((final_value / self.initial_cash) ** (1 / years) - 1) * 100 if years > 0 else 0
        
        # 리스크 보정 지표 계산
        metrics = calculate_all_metrics(self.results, self.initial_cash)
        
        summary = {
            "Strategy": self.strategy.name if self.strategy else "N/A",
            "Ticker": self.ticker,
            "Period": f"{self.results.index[0].strftime('%Y-%m-%d')} ~ {self.results.index[-1].strftime('%Y-%m-%d')}",
            "Days": days,
            "Initial Cash": f"${self.initial_cash:,.2f}",
            "Final Value": f"${final_value:,.2f}",
            "Total Return": f"{total_return:.2f}%",
            "Annualized Return": f"{annualized_return:.2f}%",
            "Total Trades": len(self.portfolio.trades),
        }
        
        # 추가 지표 추가
        if metrics:
            summary.update({
                "Sharpe Ratio": f"{metrics.get('sharpe_ratio', 0):.2f}",
                "Sortino Ratio": f"{metrics.get('sortino_ratio', 0):.2f}",
                "Calmar Ratio": f"{metrics.get('calmar_ratio', 0):.2f}",
                "Volatility": f"{metrics.get('volatility', 0):.2f}%",
                "Max Drawdown": f"{metrics.get('max_drawdown', 0):.2f}%",
            })
            if metrics.get("recovery_days") is not None:
                summary["Recovery Days"] = f"{metrics['recovery_days']}일"
            else:
                summary["Recovery Days"] = "미회복"
        
        return summary

    def get_holdings(self) -> pd.DataFrame:
        """현재 보유 종목"""
        return self.portfolio.get_holdings_summary()

