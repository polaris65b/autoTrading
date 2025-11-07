"""
안전 추구형 이동평균선 기반 섀넌 하이브리드 전략
200일선 위: 섀넌 전략 (TQQQ 50% + SGOV 50%)
200일선 아래: SGOV 100%
"""

from typing import Dict, Optional
import pandas as pd
from loguru import logger

from src.strategy.base import BaseStrategy


class SafeMovingAverageShannonHybridStrategy(BaseStrategy):
    """
    안전 추구형 이동평균선 기반 섀넌 하이브리드 전략
    
    주식 종목의 n일 이동평균선을 기준으로:
    - n일선 위: 섀넌 전략 (주식 50% + 채권 50%, 밴딩 방식)
    - n일선 아래: 채권 100% 보유
    """

    def __init__(self, name: str = "SafeMovingAverageShannonHybrid", params: Optional[Dict] = None):
        super().__init__(name, params or {})
        self.stock_ticker = self.params.get("stock_ticker", "TQQQ")
        self.bond_ticker = self.params.get("bond_ticker", "SGOV")
        self.ma_period = self.params.get("ma_period", 200)
        self.stock_pct = self.params.get("stock_pct", 0.5)
        self.band_threshold = self.params.get("band_threshold", 0.1)
        
        self.use_bond = self.bond_ticker is not None
        if not self.use_bond:
            raise ValueError("SafeMovingAverageShannonHybridStrategy requires a bond_ticker.")

        self.current_mode = None

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        거래 신호 생성
        - Signal = 1: 모드 전환 필요 (200일선 아래로)
        - Signal = 3: 밴딩 체크 필요 (200일선 위, 섀넌 모드)
        - Mode: "ABOVE" 또는 "BELOW"
        """
        if not self.validate_data(data):
            raise ValueError("Data validation failed")
        
        df = data.copy()
        df["Signal"] = 0
        df["Mode"] = None
        
        ma_column = f"MA{self.ma_period}"
        df[ma_column] = df["Close"].rolling(window=self.ma_period, min_periods=1).mean()
        
        for idx in range(len(df)):
            is_first_day = (idx == 0)
            close = df.iloc[idx]["Close"]
            ma = df.iloc[idx][ma_column]
            
            prev_mode = df.iloc[idx-1]["Mode"] if not is_first_day else None
            
            is_above = close >= ma
            current_mode = "ABOVE" if is_above else "BELOW"
            df.iloc[idx, df.columns.get_loc("Mode")] = current_mode

            if is_first_day or current_mode != prev_mode:
                df.iloc[idx, df.columns.get_loc("Signal")] = 1  # 모드 전환
            elif current_mode == "ABOVE":
                df.iloc[idx, df.columns.get_loc("Signal")] = 3  # 섀넌 리밸런싱 체크
        
        return df

    def check_banding_rebalance(self, portfolio_value: float, current_stock_value: float) -> bool:
        if portfolio_value == 0:
            return False
        current_stock_pct = current_stock_value / portfolio_value
        diff = abs(current_stock_pct - self.stock_pct)
        return diff >= self.band_threshold

    def calculate_position_size(self, portfolio_value: float, price: float, signal: float, **kwargs) -> int:
        if signal == 0:
            return 0
        
        current_quantity = kwargs.get("current_quantity", 0)
        ticker = kwargs.get("ticker", None)
        mode = kwargs.get("mode", None)

        # 주식 포지션 계산
        if ticker == self.stock_ticker:
            if mode == "ABOVE": # 섀넌 모드
                if signal == 1: # 모드 진입
                    target_value = portfolio_value * self.stock_pct
                    target_quantity = int(target_value / price)
                    return target_quantity - current_quantity
                elif signal == 3: # 리밸런싱 체크
                    current_stock_value = kwargs.get("current_stock_value", 0.0)
                    if self.check_banding_rebalance(portfolio_value, current_stock_value):
                        target_value = portfolio_value * self.stock_pct
                        target_quantity = int(target_value / price)
                        return target_quantity - current_quantity
            elif mode == "BELOW": # 채권 100% 모드
                return -current_quantity  # 주식 전량 매도

        # 채권 포지션 계산
        elif ticker == self.bond_ticker:
            if mode == "ABOVE": # 섀넌 모드
                if signal == 1: # 모드 진입
                    target_value = portfolio_value * (1 - self.stock_pct)
                    target_quantity = int(target_value / price)
                    return target_quantity - current_quantity
                elif signal == 3: # 리밸런싱 체크
                    current_stock_value = kwargs.get("current_stock_value", 0.0)
                    if self.check_banding_rebalance(portfolio_value, current_stock_value):
                        target_value = portfolio_value * (1 - self.stock_pct)
                        target_quantity = int(target_value / price)
                        return target_quantity - current_quantity
            elif mode == "BELOW": # 채권 100% 모드
                target_value = portfolio_value
                target_quantity = int(target_value / price)
                return target_quantity - current_quantity
                
        return 0
