"""
QQQ 200일선 기반 TQQQ/QID 전략
200일선 위: TQQQ 보유
200일선 밑: QID 보유
"""

from typing import Dict, Optional
import pandas as pd
from loguru import logger

from src.strategy.base import BaseStrategy


class QQQTQQQIDMAStrategy(BaseStrategy):
    """
    QQQ 200일선 기반 TQQQ/QID 전략
    
    로직:
    - QQQ 200일선 위: TQQQ 100% 보유
    - QQQ 200일선 밑: QID 100% 보유
    """
    
    def __init__(self, name: str = "QQQTQQQIDMA", params: Optional[Dict] = None):
        """
        초기화
        
        Args:
            name: 전략 이름
            params: 전략 파라미터
                - base_ticker: 이동평균선 계산 기준 종목 (기본: "QQQ")
                - tqqq_ticker: TQQQ 종목 (기본: "TQQQ")
                - qid_ticker: QID 종목 (기본: "QID")
                - ma_period: 이동평균 기간 (기본: 200)
        """
        super().__init__(name, params or {})
        self.base_ticker = self.params.get("base_ticker", "QQQ")
        self.tqqq_ticker = self.params.get("tqqq_ticker", "TQQQ")
        self.qid_ticker = self.params.get("qid_ticker", "QID")
        self.ma_period = self.params.get("ma_period", 200)
        
        self.current_mode = None  # "ABOVE" 또는 "BELOW"
        self.current_holding = None
        
        # 백테스팅 엔진 호환성
        self.stock_ticker = self.base_ticker
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        거래 신호 생성
        
        기준 종목(QQQ) 데이터를 기준으로:
        1. 200일 이동평균선 계산
        2. 200일선 위/아래 판단
        3. 신호 생성:
           - 200일선 위: TQQQ 보유 모드 (Signal=1, TargetTicker=TQQQ)
           - 200일선 아래: QID 보유 모드 (Signal=1, TargetTicker=QID)
        
        Args:
            data: OHLCV 데이터프레임 (기준 종목 QQQ 데이터)
        
        Returns:
            신호가 추가된 데이터프레임
            - Signal = 1: 모드 전환 필요 (초기 진입 포함)
            - Signal = 0: 보유
            - TargetTicker: 목표 종목 (TQQQ 또는 QID)
            - Mode: 현재 모드 ("ABOVE" 또는 "BELOW")
        """
        if not self.validate_data(data):
            raise ValueError("데이터 유효성 검증 실패")
        
        df = data.copy()
        df["Signal"] = 0
        df["TargetTicker"] = None
        df["Mode"] = None
        
        ma_column = f"MA{self.ma_period}"
        df[ma_column] = df["Close"].rolling(window=self.ma_period, min_periods=1).mean()
        
        # 첫날 모드 결정 및 초기 매수 신호
        first_close = df.iloc[0]["Close"]
        first_ma = df.iloc[0][ma_column]
        
        if first_close >= first_ma:
            df.iloc[0, df.columns.get_loc("Signal")] = 1
            df.iloc[0, df.columns.get_loc("TargetTicker")] = self.tqqq_ticker
            df.iloc[0, df.columns.get_loc("Mode")] = "ABOVE"
            self.current_mode = "ABOVE"
            self.current_holding = self.tqqq_ticker
        else:
            df.iloc[0, df.columns.get_loc("Signal")] = 1
            df.iloc[0, df.columns.get_loc("TargetTicker")] = self.qid_ticker
            df.iloc[0, df.columns.get_loc("Mode")] = "BELOW"
            self.current_mode = "BELOW"
            self.current_holding = self.qid_ticker
        
        # 이후 날짜들 처리
        for idx in range(1, len(df)):
            prev_close = df.iloc[idx - 1]["Close"]
            prev_ma = df.iloc[idx - 1][ma_column]
            curr_close = df.iloc[idx]["Close"]
            curr_ma = df.iloc[idx][ma_column]
            
            prev_below = prev_close < prev_ma
            curr_above = curr_close >= curr_ma
            
            prev_above = prev_close >= prev_ma
            curr_below = curr_close < curr_ma
            
            # 모드 전환 체크
            if (prev_below and curr_above) or (prev_above and curr_below):
                df.iloc[idx, df.columns.get_loc("Signal")] = 1
                if curr_above:
                    target = self.tqqq_ticker
                    mode = "ABOVE"
                    self.current_holding = self.tqqq_ticker
                else:
                    target = self.qid_ticker
                    mode = "BELOW"
                    self.current_holding = self.qid_ticker
                df.iloc[idx, df.columns.get_loc("TargetTicker")] = target
                df.iloc[idx, df.columns.get_loc("Mode")] = mode
                self.current_mode = mode
            else:
                # 신호가 없어도 이전 목표 종목 유지
                if curr_above:
                    df.iloc[idx, df.columns.get_loc("TargetTicker")] = self.tqqq_ticker
                    df.iloc[idx, df.columns.get_loc("Mode")] = "ABOVE"
                else:
                    df.iloc[idx, df.columns.get_loc("TargetTicker")] = self.qid_ticker
                    df.iloc[idx, df.columns.get_loc("Mode")] = "BELOW"
        
        above_count = (df["Mode"] == "ABOVE").sum()
        below_count = (df["Mode"] == "BELOW").sum()
        signal_count = (df["Signal"] == 1).sum()
        
        logger.info(
            f"QQQ TQQQ/QID 전략 신호 생성 완료: {len(df)}개 일봉, "
            f"ABOVE 모드 {above_count}일, BELOW 모드 {below_count}일, "
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
        
        Args:
            portfolio_value: 포트폴리오 가치
            price: 현재가
            signal: 신호 (1=모드 전환, 0=보유)
            **kwargs: 추가 파라미터
                - current_quantity: 현재 보유 수량
                - commission_rate: 수수료율
                - ticker: 현재 거래하는 종목 (TQQQ 또는 QID)
        
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
        
        # Signal=1일 때는 목표 종목 100% 보유
        target_value = portfolio_value * (1 - commission_rate)
        target_quantity = int(target_value / price) if price > 0 else 0
        
        quantity_diff = target_quantity - current_quantity
        return quantity_diff

