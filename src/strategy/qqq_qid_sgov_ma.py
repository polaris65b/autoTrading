"""
QQQ 200일선 기반 QID/SGOV 전략
200일선 하향 돌파: TQQQ 매도 → QID 50% + SGOV 50% 시작, QID 상승분은 SGOV로 이동
200일선 상향 돌파: SGOV/QID 매도 → TQQQ 매수
"""

from typing import Dict, Optional
import pandas as pd
from loguru import logger

from src.strategy.base import BaseStrategy


class QQQQIDSGOVMAStrategy(BaseStrategy):
    """
    QQQ 200일선 기반 QID/SGOV 전략
    
    로직:
    - 200일선 위 (ABOVE): TQQQ 100% 보유
    - 200일선 아래 (BELOW): QID 50% + SGOV 50% 초기 배분, 이후 QID 상승분은 SGOV로 이동
    """
    
    def __init__(self, name: str = "QQQQIDSGOVMA", params: Optional[Dict] = None):
        """
        초기화
        
        Args:
            name: 전략 이름
            params: 전략 파라미터
                - base_ticker: 이동평균선 계산 기준 종목 (기본: "QQQ")
                - tqqq_ticker: TQQQ 종목 (기본: "TQQQ")
                - qid_ticker: QID 종목 (기본: "QID")
                - sgov_ticker: SGOV 종목 (기본: "SGOV")
                - ma_period: 이동평균 기간 (기본: 200)
                - qid_pct: QID 목표 비율 (기본: 0.5 = 50%)
                - sgov_pct: SGOV 목표 비율 (기본: 0.5 = 50%)
                - rebalance_threshold: 리밸런싱 임계값 (기본: 0.05 = 5%)
        """
        super().__init__(name, params or {})
        self.base_ticker = self.params.get("base_ticker", "QQQ")
        self.tqqq_ticker = self.params.get("tqqq_ticker", "TQQQ")
        self.qid_ticker = self.params.get("qid_ticker", "QID")
        self.sgov_ticker = self.params.get("sgov_ticker", "SGOV")
        self.ma_period = self.params.get("ma_period", 200)
        self.qid_pct = self.params.get("qid_pct", 0.5)
        self.sgov_pct = self.params.get("sgov_pct", 0.5)
        self.rebalance_threshold = self.params.get("rebalance_threshold", 0.05)
        
        self.current_mode = None
        self.initial_qid_value = None
        
        if abs(self.qid_pct + self.sgov_pct - 1.0) > 0.01:
            logger.warning(f"목표 비율의 합이 1.0이 아닙니다: {self.qid_pct + self.sgov_pct} (자동 조정)")
            total_pct = self.qid_pct + self.sgov_pct
            self.qid_pct = self.qid_pct / total_pct
            self.sgov_pct = self.sgov_pct / total_pct
        
        self.stock_ticker = self.base_ticker
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        거래 신호 생성
        
        기준 종목(QQQ) 데이터를 기준으로:
        1. 200일 이동평균선 계산
        2. 200일선 위/아래 판단
        3. 신호 생성:
           - 200일선 위: TQQQ 보유 모드 (Signal=1)
           - 200일선 아래: QID+SGOV 리밸런싱 모드 (Signal=3)
        
        Args:
            data: OHLCV 데이터프레임 (기준 종목 데이터)
        
        Returns:
            신호가 추가된 데이터프레임
            - Signal = 1: 200일선 위로 전환 (TQQQ 전환)
            - Signal = 3: 200일선 아래 모드 유지 (리밸런싱 체크)
            - Mode: 현재 모드 ("ABOVE" 또는 "BELOW")
        """
        if not self.validate_data(data):
            raise ValueError("데이터 유효성 검증 실패")
        
        df = data.copy()
        df["Signal"] = 0
        df["Mode"] = None
        
        ma_column = f"MA{self.ma_period}"
        df[ma_column] = df["Close"].rolling(window=self.ma_period, min_periods=1).mean()
        
        first_close = df.iloc[0]["Close"]
        first_ma = df.iloc[0][ma_column]
        
        if first_close >= first_ma:
            df.iloc[0, df.columns.get_loc("Signal")] = 1
            df.iloc[0, df.columns.get_loc("Mode")] = "ABOVE"
            self.current_mode = "ABOVE"
        else:
            df.iloc[0, df.columns.get_loc("Signal")] = 3
            df.iloc[0, df.columns.get_loc("Mode")] = "BELOW"
            self.current_mode = "BELOW"
        
        for idx in range(1, len(df)):
            curr_close = df.iloc[idx]["Close"]
            curr_ma = df.iloc[idx][ma_column]
            prev_close = df.iloc[idx - 1]["Close"]
            prev_ma = df.iloc[idx - 1][ma_column]
            
            prev_below_ma = prev_close < prev_ma
            curr_above_ma = curr_close >= curr_ma
            prev_above_ma = prev_close >= prev_ma
            curr_below_ma = curr_close < curr_ma
            
            if prev_below_ma and curr_above_ma:
                df.iloc[idx, df.columns.get_loc("Signal")] = 1
                df.iloc[idx, df.columns.get_loc("Mode")] = "ABOVE"
                self.current_mode = "ABOVE"
                self.initial_qid_value = None
            elif prev_above_ma and curr_below_ma:
                df.iloc[idx, df.columns.get_loc("Signal")] = 3
                df.iloc[idx, df.columns.get_loc("Mode")] = "BELOW"
                self.current_mode = "BELOW"
                self.initial_qid_value = None
            elif curr_above_ma:
                df.iloc[idx, df.columns.get_loc("Signal")] = 0
                df.iloc[idx, df.columns.get_loc("Mode")] = "ABOVE"
                self.current_mode = "ABOVE"
            else:
                df.iloc[idx, df.columns.get_loc("Signal")] = 3
                df.iloc[idx, df.columns.get_loc("Mode")] = "BELOW"
                self.current_mode = "BELOW"
        
        signal_count = (df["Signal"] == 1).sum()
        rebalance_signals = (df["Signal"] == 3).sum()
        
        logger.info(
            f"QQQ QID SGOV MA 전략 신호 생성 완료: {len(df)}개 일봉, "
            f"전환 신호 {signal_count}회, 리밸런싱 체크 {rebalance_signals}회 "
            f"(MA={self.ma_period}일)"
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
            signal: 신호 (1=전환, 3=리밸런싱 체크, 0=보유)
            **kwargs: 추가 파라미터
                - ticker: 현재 거래하는 종목
                - current_quantity: 현재 보유 수량
                - commission_rate: 수수료율
                - mode: 현재 모드 ("ABOVE" 또는 "BELOW")
                - current_qid_value: QID 현재 가치
                - current_sgov_value: SGOV 현재 가치
                - qid_price: QID 현재가
                - initial_qid_value: BELOW 모드 진입 시 초기 QID 가치
                - current_tqqq_value: TQQQ 현재 가치
        
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
        current_qid_value = kwargs.get("current_qid_value", 0.0)
        current_sgov_value = kwargs.get("current_sgov_value", 0.0)
        qid_price = kwargs.get("qid_price", 0.0)
        initial_qid_value = kwargs.get("initial_qid_value", None)
        current_tqqq_value = kwargs.get("current_tqqq_value", 0.0)
        
        if ticker is None or mode is None:
            return 0
        
        if signal == 1:
            if mode == "ABOVE":
                if ticker == self.tqqq_ticker:
                    target_value = portfolio_value * (1 - commission_rate)
                    target_quantity = int(target_value / price) if price > 0 else 0
                    quantity_diff = target_quantity - current_quantity
                    return quantity_diff
                else:
                    if current_quantity > 0:
                        return -current_quantity
        
        elif signal == 3:
            if mode == "BELOW":
                if ticker == self.qid_ticker:
                    if initial_qid_value is None:
                        initial_qid_value = portfolio_value * self.qid_pct
                    
                    if current_qid_value > initial_qid_value:
                        excess_value = current_qid_value - initial_qid_value
                        excess_quantity = int(excess_value / price) if price > 0 else 0
                        if excess_quantity > 0:
                            return -excess_quantity
                    elif current_qid_value < initial_qid_value:
                        return 0
                    else:
                        target_value = initial_qid_value * (1 - commission_rate)
                        target_quantity = int(target_value / price) if price > 0 else 0
                        quantity_diff = target_quantity - current_quantity
                        return quantity_diff
                
                elif ticker == self.sgov_ticker:
                    if initial_qid_value is None:
                        initial_qid_value = portfolio_value * self.qid_pct
                    
                    target_sgov_value = portfolio_value - initial_qid_value
                    target_quantity = int(target_sgov_value * (1 - commission_rate) / price) if price > 0 else 0
                    quantity_diff = target_quantity - current_quantity
                    return quantity_diff
                
                else:
                    if current_quantity > 0:
                        return -current_quantity
        
        return 0

