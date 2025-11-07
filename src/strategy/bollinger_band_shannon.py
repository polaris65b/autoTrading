"""
볼린저 밴드 섀넌 전략 (Bollinger Band Shannon Strategy)
"""

from typing import Dict, Optional
import pandas as pd
from loguru import logger

from src.strategy.base import BaseStrategy


class BollingerBandShannonStrategy(BaseStrategy):
    """
    볼린저 밴드 섀넌 전략
    
    현금과 주식을 일정 비율로 유지하며, 리밸런싱은 볼린저 밴드 상단/하단 터치 시 수행
    """

    def __init__(self, name: str = "BollingerBandShannon", params: Optional[Dict] = None):
        """
        초기화
        
        Args:
            name: 전략 이름
            params: 전략 파라미터
                - stock_pct: 주식 비율 (기본: 0.5 = 50%)
                - stock_ticker: 주식 종목 티커 (기본: None, 엔진에서 설정)
                - bond_ticker: 채권 종목 티커 (기본: None = 현금 사용)
                - bb_period: 볼린저 밴드 기간 (기본: 20)
                - bb_std: 볼린저 밴드 표준편차 (기본: 2)
        """
        super().__init__(name, params or {})
        self.stock_pct = self.params.get("stock_pct", 0.5)
        self.stock_ticker = self.params.get("stock_ticker", None)
        self.bond_ticker = self.params.get("bond_ticker", None)
        self.bb_period = self.params.get("bb_period", 20)
        self.bb_std = self.params.get("bb_std", 2)
        self.use_bond = self.bond_ticker is not None

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        거래 신호 생성
        
        Args:
            data: OHLCV 데이터프레임
        
        Returns:
            신호가 추가된 데이터프레임
            - Signal = 1: 초기 매수
            - Signal = 4: 볼린저 밴드 리밸런싱
            - Signal = 0: 보유
        """
        if not self.validate_data(data):
            raise ValueError("데이터 유효성 검증 실패")
        
        df = data.copy()
        
        # 볼린저 밴드 계산
        df['MA'] = df['Close'].rolling(window=self.bb_period).mean()
        df['STD'] = df['Close'].rolling(window=self.bb_period).std()
        df['Upper'] = df['MA'] + (self.bb_std * df['STD'])
        df['Lower'] = df['MA'] - (self.bb_std * df['STD'])
        
        df["Signal"] = 0
        
        # 첫날 매수 신호
        df.iloc[self.bb_period -1, df.columns.get_loc("Signal")] = 1
        
        # 리밸런싱 신호 생성
        for i in range(self.bb_period, len(df)):
            if df['Close'].iloc[i] > df['Upper'].iloc[i] or df['Close'].iloc[i] < df['Lower'].iloc[i]:
                df.iloc[i, df.columns.get_loc("Signal")] = 4  # 볼린저 밴드 리밸런싱
        
        rebalance_count = (df["Signal"] == 4).sum()
        logger.info(
            f"볼린저 밴드 섀넌 전략 신호 생성 완료: {len(df)}개 일봉, "
            f"초기 매수 1회, 리밸런싱 {rebalance_count}회"
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
        """
        if signal == 0:
            return 0
        
        current_quantity = kwargs.get("current_quantity", 0)
        commission_rate = kwargs.get("commission_rate", 0.001)
        ticker = kwargs.get("ticker", None)
        
        is_stock = ticker == self.stock_ticker or (self.stock_ticker is None and ticker is not None and ticker != self.bond_ticker)
        
        if is_stock:
            target_value = portfolio_value * self.stock_pct
            target_quantity = int(target_value / price)
        else:
            if not self.use_bond:
                return 0
            target_value = portfolio_value * (1 - self.stock_pct)
            target_quantity = int(target_value / price)

        if signal == 1:  # 초기 매수
            adjusted_target = target_value * (1 - commission_rate)
            target_quantity = int(adjusted_target / price)
            return target_quantity
        
        elif signal == 4:  # 볼린저 밴드 리밸런싱
            quantity_diff = target_quantity - current_quantity
            return quantity_diff
            
        return 0
