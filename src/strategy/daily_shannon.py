"""
Daily 섀넌 전략
종가 기준 매일 50:50 비율로 리밸런싱
"""

from typing import Dict, Optional
import pandas as pd
from loguru import logger

from src.strategy.base import BaseStrategy


class DailyShannonStrategy(BaseStrategy):
    """
    Daily 섀넌 전략
    
    매일 종가 기준으로 주식과 채권(또는 현금)을 50:50 비율로 리밸런싱
    """
    
    def __init__(self, name: str = "DailyShannon", params: Optional[Dict] = None):
        """
        초기화
        
        Args:
            name: 전략 이름
            params: 전략 파라미터
                - stock_pct: 주식 비율 (기본: 0.5 = 50%)
                - stock_ticker: 주식 종목 티커 (기본: None, 엔진에서 설정)
                - bond_ticker: 채권 종목 티커 (기본: None = 현금 사용)
        """
        super().__init__(name, params or {})
        self.stock_pct = self.params.get("stock_pct", 0.5)
        self.stock_ticker = self.params.get("stock_ticker", None)
        self.bond_ticker = self.params.get("bond_ticker", None)
        
        self.use_bond = self.bond_ticker is not None
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        거래 신호 생성
        
        매일 리밸런싱 신호 생성
        
        Args:
            data: OHLCV 데이터프레임
        
        Returns:
            신호가 추가된 데이터프레임
            - Signal = 1: 초기 매수
            - Signal = 3: 매일 리밸런싱
        """
        if not self.validate_data(data):
            raise ValueError("데이터 유효성 검증 실패")
        
        df = data.copy()
        df["Signal"] = 0
        
        # 첫날 초기 매수 신호
        df.iloc[0, df.columns.get_loc("Signal")] = 1
        
        # 나머지 날짜는 매일 리밸런싱 신호
        for idx in range(1, len(df)):
            df.iloc[idx, df.columns.get_loc("Signal")] = 3
        
        logger.info(
            f"Daily 섀넌 전략 신호 생성 완료: {len(df)}개 일봉, "
            f"초기 매수 1회, 매일 리밸런싱 {len(df) - 1}회"
        )
        
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
            signal: 신호 (1=초기 매수, 3=매일 리밸런싱, 0=보유)
            **kwargs: 추가 파라미터
                - current_quantity: 현재 보유 수량
                - cash: 현재 현금
                - current_bond_value: 현재 채권 가치 (bond_ticker 사용 시)
                - commission_rate: 수수료율
                - ticker: 현재 거래하는 종목 (stock_ticker 또는 bond_ticker)
        
        Returns:
            거래 수량 (양수=매수, 음수=매도, 0=보유)
        """
        if signal == 0:
            return 0
        
        if price <= 0 or pd.isna(price):
            return 0
        
        current_quantity = kwargs.get("current_quantity", 0)
        commission_rate = kwargs.get("commission_rate", 0.001)
        ticker = kwargs.get("ticker", None)
        
        if ticker is None:
            return 0
        
        # 거래하는 종목이 주식인지 채권인지 확인
        is_stock = ticker == self.stock_ticker or (self.stock_ticker is None and ticker != self.bond_ticker)
        
        if is_stock:
            # 주식 포지션 계산
            target_value = portfolio_value * self.stock_pct * (1 - commission_rate)
            target_quantity = int(target_value / price) if price > 0 else 0
        else:
            # 채권 포지션 계산 (채권 사용 시)
            if not self.use_bond:
                return 0
            target_value = portfolio_value * (1 - self.stock_pct) * (1 - commission_rate)
            target_quantity = int(target_value / price) if price > 0 else 0
        
        quantity_diff = target_quantity - current_quantity
        return quantity_diff


