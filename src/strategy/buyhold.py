"""
Buy & Hold 전략
단순 매수 후 보유 전략
"""

from typing import Dict, Optional
import pandas as pd
from loguru import logger

from src.strategy.base import BaseStrategy


class BuyHoldStrategy(BaseStrategy):
    """
    Buy & Hold 전략
    
    첫날 한 번 매수 후 계속 보유하는 전략
    """

    def __init__(self, name: str = "BuyHold", params: Optional[Dict] = None):
        """
        초기화
        
        Args:
            name: 전략 이름
            params: 전략 파라미터
                - position_pct: 투자 비율 (기본: 1.0 = 100%)
                - stock_ticker: 주식 종목 티커 (기본: None, 엔진에서 설정)
        """
        super().__init__(name, params or {})
        self.position_pct = self.params.get("position_pct", 1.0)  # 100% 투자
        self.stock_ticker = self.params.get("stock_ticker", None)  # 주식 종목
        self.first_buy_date = None

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        거래 신호 생성
        
        Args:
            data: OHLCV 데이터프레임
        
        Returns:
            신호가 추가된 데이터프레임
        """
        if not self.validate_data(data):
            raise ValueError("데이터 유효성 검증 실패")
        
        df = data.copy()
        
        # 첫날에만 매수 신호
        df["Signal"] = 0
        df.iloc[0, df.columns.get_loc("Signal")] = 1
        
        # 첫 매수 날짜 기록
        self.first_buy_date = df.index[0]
        
        logger.info(f"Buy & Hold 신호 생성 완료: {len(df)}개 일봉, 첫날 매수")
        
        return df

    def calculate_position_size(
        self,
        portfolio_value: float,
        price: float,
        signal: float,
        **kwargs
    ) -> int:
        """
        포지션 사이징 계산
        
        Args:
            portfolio_value: 포트폴리오 가치
            price: 현재가
            signal: 신호 (1=매수, 0=보유)
            **kwargs: 추가 파라미터
                - commission_rate: 수수료율 (선택)
        
        Returns:
            거래 수량
        """
        logger.debug(f"BuyHoldStrategy kwargs: {kwargs}")
        if signal == 1:  # 첫날 매수
            # 수수료를 고려하여 여유를 둠
            commission_rate = kwargs.get("commission_rate", 0.001)
            target_value = portfolio_value * self.position_pct * (1 - commission_rate)
            quantity = int(target_value / price)
            return quantity
        
        return 0  # 보유만

