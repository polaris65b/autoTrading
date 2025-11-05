"""
QQQ 200EMA 기반 섀넌 전략
200EMA 상향 돌파: QQQ:TQQQ 1:1 (50:50), 10% 밴딩 (45:55)
200EMA 하향 돌파: SGOV:QID 1:1 (50:50), 10% 밴딩 (45:55)
"""

from typing import Dict, Optional
import pandas as pd
import numpy as np
from loguru import logger

from src.strategy.base import BaseStrategy


class QQQEMAShannonStrategy(BaseStrategy):
    """
    QQQ 200EMA 기반 섀넌 전략
    
    로직:
    - 200EMA 위 (ABOVE): QQQ 50% + TQQQ 50% (45:55 밴딩 리밸런싱)
    - 200EMA 아래 (BELOW): SGOV 50% + QID 50% (45:55 밴딩 리밸런싱)
    """
    
    def __init__(self, name: str = "QQQEMAShannon", params: Optional[Dict] = None):
        """
        초기화
        
        Args:
            name: 전략 이름
            params: 전략 파라미터
                - base_ticker: 이동평균선 계산 기준 종목 (기본: "QQQ")
                - qqq_ticker: QQQ 종목 (기본: "QQQ")
                - tqqq_ticker: TQQQ 종목 (기본: "TQQQ")
                - sgov_ticker: SGOV 종목 (기본: "SGOV")
                - qid_ticker: QID 종목 (기본: "QID")
                - ema_period: 지수 이동평균 기간 (기본: 200)
                - above_pct1: ABOVE 모드 종목1 목표 비율 (기본: 0.5 = 50%)
                - above_pct2: ABOVE 모드 종목2 목표 비율 (기본: 0.5 = 50%)
                - below_pct1: BELOW 모드 종목1 목표 비율 (기본: 0.5 = 50%)
                - below_pct2: BELOW 모드 종목2 목표 비율 (기본: 0.5 = 50%)
                - band_threshold: 밴딩 임계값 (기본: 0.10 = 10%)
        """
        super().__init__(name, params or {})
        self.base_ticker = self.params.get("base_ticker", "QQQ")
        self.qqq_ticker = self.params.get("qqq_ticker", "QQQ")
        self.tqqq_ticker = self.params.get("tqqq_ticker", "TQQQ")
        self.sgov_ticker = self.params.get("sgov_ticker", "SGOV")
        self.qid_ticker = self.params.get("qid_ticker", "QID")
        self.ema_period = self.params.get("ema_period", 200)
        self.above_pct1 = self.params.get("above_pct1", 0.5)
        self.above_pct2 = self.params.get("above_pct2", 0.5)
        self.below_pct1 = self.params.get("below_pct1", 0.5)
        self.below_pct2 = self.params.get("below_pct2", 0.5)
        self.band_threshold = self.params.get("band_threshold", 0.10)
        
        self.current_mode = None
        
        if abs(self.above_pct1 + self.above_pct2 - 1.0) > 0.01:
            logger.warning(f"ABOVE 모드 목표 비율의 합이 1.0이 아닙니다: {self.above_pct1 + self.above_pct2} (자동 조정)")
            total_pct = self.above_pct1 + self.above_pct2
            self.above_pct1 = self.above_pct1 / total_pct
            self.above_pct2 = self.above_pct2 / total_pct
        
        if abs(self.below_pct1 + self.below_pct2 - 1.0) > 0.01:
            logger.warning(f"BELOW 모드 목표 비율의 합이 1.0이 아닙니다: {self.below_pct1 + self.below_pct2} (자동 조정)")
            total_pct = self.below_pct1 + self.below_pct2
            self.below_pct1 = self.below_pct1 / total_pct
            self.below_pct2 = self.below_pct2 / total_pct
        
        self.stock_ticker = self.base_ticker
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        거래 신호 생성
        
        기준 종목(QQQ) 데이터를 기준으로:
        1. 200일 지수 이동평균선(EMA) 계산
        2. 200EMA 위/아래 판단
        3. 신호 생성:
           - 200EMA 위: QQQ:TQQQ 리밸런싱 모드 (Signal=3)
           - 200EMA 아래: SGOV:QID 리밸런싱 모드 (Signal=3)
        
        Args:
            data: OHLCV 데이터프레임 (기준 종목 데이터)
        
        Returns:
            신호가 추가된 데이터프레임
            - Signal = 3: 리밸런싱 체크
            - Mode: 현재 모드 ("ABOVE" 또는 "BELOW")
        """
        if not self.validate_data(data):
            raise ValueError("데이터 유효성 검증 실패")
        
        df = data.copy()
        df["Signal"] = 0
        df["Mode"] = None
        
        # 지수 이동평균선(EMA) 계산
        ema_column = f"EMA{self.ema_period}"
        df[ema_column] = df["Close"].ewm(span=self.ema_period, adjust=False).mean()
        
        first_close = df.iloc[0]["Close"]
        first_ema = df.iloc[0][ema_column]
        
        if first_close >= first_ema:
            df.iloc[0, df.columns.get_loc("Signal")] = 3
            df.iloc[0, df.columns.get_loc("Mode")] = "ABOVE"
            self.current_mode = "ABOVE"
        else:
            df.iloc[0, df.columns.get_loc("Signal")] = 3
            df.iloc[0, df.columns.get_loc("Mode")] = "BELOW"
            self.current_mode = "BELOW"
        
        for idx in range(1, len(df)):
            curr_close = df.iloc[idx]["Close"]
            curr_ema = df.iloc[idx][ema_column]
            prev_close = df.iloc[idx - 1]["Close"]
            prev_ema = df.iloc[idx - 1][ema_column]
            
            prev_below_ema = prev_close < prev_ema
            curr_above_ema = curr_close >= curr_ema
            prev_above_ema = prev_close >= prev_ema
            curr_below_ema = curr_close < curr_ema
            
            if prev_below_ema and curr_above_ema:
                df.iloc[idx, df.columns.get_loc("Signal")] = 3
                df.iloc[idx, df.columns.get_loc("Mode")] = "ABOVE"
                self.current_mode = "ABOVE"
            elif prev_above_ema and curr_below_ema:
                df.iloc[idx, df.columns.get_loc("Signal")] = 3
                df.iloc[idx, df.columns.get_loc("Mode")] = "BELOW"
                self.current_mode = "BELOW"
            elif curr_above_ema:
                df.iloc[idx, df.columns.get_loc("Signal")] = 3
                df.iloc[idx, df.columns.get_loc("Mode")] = "ABOVE"
                self.current_mode = "ABOVE"
            else:
                df.iloc[idx, df.columns.get_loc("Signal")] = 3
                df.iloc[idx, df.columns.get_loc("Mode")] = "BELOW"
                self.current_mode = "BELOW"
        
        signal_count = (df["Signal"] == 3).sum()
        
        logger.info(
            f"QQQ EMA Shannon 전략 신호 생성 완료: {len(df)}개 일봉, "
            f"리밸런싱 체크 {signal_count}회 (EMA={self.ema_period}일)"
        )
        
        return df
    
    def check_banding_rebalance(
        self,
        portfolio_value: float,
        current_value1: float,
        current_value2: float,
        price1: float,
        price2: float,
        quantity1: int,
        quantity2: int,
        mode: str
    ) -> tuple[bool, Optional[str]]:
        """
        밴딩 리밸런싱 필요 여부 체크
        
        Args:
            portfolio_value: 전체 포트폴리오 가치
            current_value1: 종목1 현재 가치
            current_value2: 종목2 현재 가치
            price1: 종목1 현재가
            price2: 종목2 현재가
            quantity1: 종목1 보유 수량
            quantity2: 종목2 보유 수량
            mode: 현재 모드 ("ABOVE" 또는 "BELOW")
        
        Returns:
            (리밸런싱 필요 여부, 리밸런싱이 필요한 티커)
        """
        if portfolio_value == 0:
            return False, None
        
        if mode == "ABOVE":
            target_pct1 = self.above_pct1
            target_pct2 = self.above_pct2
            ticker1 = self.qqq_ticker
            ticker2 = self.tqqq_ticker
        else:
            target_pct1 = self.below_pct1
            target_pct2 = self.below_pct2
            ticker1 = self.sgov_ticker
            ticker2 = self.qid_ticker
        
        current_pct1 = current_value1 / portfolio_value if portfolio_value > 0 else 0
        current_pct2 = current_value2 / portfolio_value if portfolio_value > 0 else 0
        
        diff1 = abs(current_pct1 - target_pct1)
        diff2 = abs(current_pct2 - target_pct2)
        
        if diff1 >= self.band_threshold or diff2 >= self.band_threshold:
            if diff1 >= diff2:
                return True, ticker1
            else:
                return True, ticker2
        
        return False, None
    
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
            signal: 신호 (3=리밸런싱 체크, 0=보유)
            **kwargs: 추가 파라미터
                - ticker: 현재 거래하는 종목
                - current_quantity: 현재 보유 수량
                - commission_rate: 수수료율
                - mode: 현재 모드 ("ABOVE" 또는 "BELOW")
                - current_value1: 종목1 현재 가치
                - current_value2: 종목2 현재 가치
        
        Returns:
            거래 수량 (양수=매수, 음수=매도, 0=보유)
        """
        if signal == 0:
            return 0
        
        if price <= 0 or pd.isna(price):
            return 0
        
        ticker = kwargs.get("ticker", None)
        current_quantity = kwargs.get("current_quantity", 0)
        commission_rate = kwargs.get("commission_rate", 0.001)
        mode = kwargs.get("mode", self.current_mode)
        current_value1 = kwargs.get("current_value1", 0.0)
        current_value2 = kwargs.get("current_value2", 0.0)
        
        if ticker is None or mode is None:
            return 0
        
        if signal == 3:
            if mode == "ABOVE":
                if ticker == self.qqq_ticker:
                    target_value = portfolio_value * self.above_pct1 * (1 - commission_rate)
                    target_quantity = int(target_value / price) if price > 0 else 0
                    quantity_diff = target_quantity - current_quantity
                    return quantity_diff
                elif ticker == self.tqqq_ticker:
                    target_value = portfolio_value * self.above_pct2 * (1 - commission_rate)
                    target_quantity = int(target_value / price) if price > 0 else 0
                    quantity_diff = target_quantity - current_quantity
                    return quantity_diff
                else:
                    if current_quantity > 0:
                        return -current_quantity
            elif mode == "BELOW":
                if ticker == self.sgov_ticker:
                    target_value = portfolio_value * self.below_pct1 * (1 - commission_rate)
                    target_quantity = int(target_value / price) if price > 0 else 0
                    quantity_diff = target_quantity - current_quantity
                    return quantity_diff
                elif ticker == self.qid_ticker:
                    target_value = portfolio_value * self.below_pct2 * (1 - commission_rate)
                    target_quantity = int(target_value / price) if price > 0 else 0
                    quantity_diff = target_quantity - current_quantity
                    return quantity_diff
                else:
                    if current_quantity > 0:
                        return -current_quantity
        
        return 0

