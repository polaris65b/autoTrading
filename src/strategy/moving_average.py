"""
이동평균선 기반 전략
n일선 위: 주식 보유, n일선 아래: 채권 보유
"""

from typing import Dict, Optional
import pandas as pd
from loguru import logger

from src.strategy.base import BaseStrategy


class MovingAverageStrategy(BaseStrategy):
    """
    이동평균선 전략 (n일선 설정 가능)
    
    주식 종목의 n일 이동평균선을 기준으로:
    - n일선 위: 주식 보유
    - n일선 아래: 채권 보유
    
    기본값은 200일선이며, config에서 ma_period로 변경 가능
    """

    def __init__(self, name: str = "MovingAverage", params: Optional[Dict] = None):
        """
        초기화
        
        Args:
            name: 전략 이름
            params: 전략 파라미터
                - stock_ticker: 주식 종목 (기본: "TQQQ")
                - bond_ticker: 채권 종목 (기본: "BIL")
                - ma_period: 이동평균 기간 (기본: 200)
        """
        super().__init__(name, params or {})
        self.stock_ticker = self.params.get("stock_ticker", "TQQQ")
        self.bond_ticker = self.params.get("bond_ticker", "BIL")
        self.ma_period = self.params.get("ma_period", 200)
        self.current_holding = None

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        거래 신호 생성
        
        주식 데이터를 기준으로 n일선을 계산하고,
        현재가와 이동평균선 위치에 따라 주식/채권 전환 신호 생성
        
        Args:
            data: OHLCV 데이터프레임 (주식 종목 데이터)
        
        Returns:
            신호가 추가된 데이터프레임
            - Signal = 1: 초기 매수 또는 전환 필요
            - Signal = 0: 보유
        """
        if not self.validate_data(data):
            raise ValueError("데이터 유효성 검증 실패")
        
        df = data.copy()
        df["Signal"] = 0
        df["TargetTicker"] = None  # 각 날짜의 목표 종목 저장
        
        ma_column = f"MA{self.ma_period}"
        df[ma_column] = df["Close"].rolling(window=self.ma_period, min_periods=1).mean()
        
        first_close = df.iloc[0]["Close"]
        first_ma = df.iloc[0][ma_column]
        
        if first_close >= first_ma:
            df.iloc[0, df.columns.get_loc("Signal")] = 1
            df.iloc[0, df.columns.get_loc("TargetTicker")] = self.stock_ticker
            self.current_holding = self.stock_ticker
        else:
            df.iloc[0, df.columns.get_loc("Signal")] = 1
            df.iloc[0, df.columns.get_loc("TargetTicker")] = self.bond_ticker
            self.current_holding = self.bond_ticker
        
        for idx in range(1, len(df)):
            prev_close = df.iloc[idx - 1]["Close"]
            prev_ma = df.iloc[idx - 1][ma_column]
            curr_close = df.iloc[idx]["Close"]
            curr_ma = df.iloc[idx][ma_column]
            
            prev_below = prev_close < prev_ma
            curr_above = curr_close >= curr_ma
            
            prev_above = prev_close >= prev_ma
            curr_below = curr_close < curr_ma
            
            if (prev_below and curr_above) or (prev_above and curr_below):
                df.iloc[idx, df.columns.get_loc("Signal")] = 1
                if curr_above:
                    target = self.stock_ticker
                    self.current_holding = self.stock_ticker
                else:
                    target = self.bond_ticker
                    self.current_holding = self.bond_ticker
                df.iloc[idx, df.columns.get_loc("TargetTicker")] = target
            else:
                # 신호가 없어도 이전 목표 종목 유지
                prev_target = df.iloc[idx - 1, df.columns.get_loc("TargetTicker")]
                df.iloc[idx, df.columns.get_loc("TargetTicker")] = prev_target
        
        signal_count = (df["Signal"] == 1).sum()
        logger.info(
            f"{self.ma_period}일선 전략 신호 생성 완료: {len(df)}개 일봉, "
            f"전환 신호 {signal_count}회"
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
        
        이동평균선 전략:
        - n일선 위: 주식 100%, 채권 0%
        - n일선 아래: 채권 100%, 주식 0%
        
        전환 시: 기존 보유 종목 전량 매도 후 목표 종목 100% 매수
        
        Args:
            portfolio_value: 포트폴리오 가치
            price: 현재가
            signal: 신호 (1=전환 필요, 0=보유)
            **kwargs: 추가 파라미터
                - ticker: 현재 거래하는 종목
                - current_quantity: 현재 보유 수량
                - commission_rate: 수수료율
        
        Returns:
            거래 수량 (양수=매수, 음수=매도, 0=보유)
        """
        if signal == 0:
            return 0
        
        ticker = kwargs.get("ticker", None)
        current_quantity = kwargs.get("current_quantity", 0)
        commission_rate = kwargs.get("commission_rate", 0.001)
        
        if ticker is None or self.current_holding is None:
            return 0
        
        if signal == 1:
            # 목표 종목: 100% 매수
            if ticker == self.current_holding:
                target_value = portfolio_value * (1 - commission_rate)
                target_quantity = int(target_value / price)
                quantity_diff = target_quantity - current_quantity
                return quantity_diff
            # 목표 종목이 아닌 종목: 전량 매도
            else:
                if current_quantity > 0:
                    return -current_quantity
        
        return 0

