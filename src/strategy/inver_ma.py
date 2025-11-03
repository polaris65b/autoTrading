"""
Inverse MA 전략
200일선 위: QQQ:TQQQ 1:1 비율, 밴딩 리밸런싱
200일선 아래: TQQQ 100% 보유
단, 200일선 아래에서 TQQQ로 전환 후 QQQ 전고점 회복까지 TQQQ 매도 금지
"""

from typing import Dict, Optional
import pandas as pd
from loguru import logger

from src.strategy.base import BaseStrategy


class InverseMAStrategy(BaseStrategy):
    """
    Inverse MA 전략
    
    로직:
    - 200일선 위: QQQ 50% + TQQQ 50% (밴딩 리밸런싱)
    - 200일선 아래: TQQQ 100% 보유
    - 특별 조건: BELOW 모드 진입 시점의 QQQ 전고점을 추적하고,
                 QQQ가 그 전고점을 회복할 때까지 TQQQ 매도 금지
    """
    
    def __init__(self, name: str = "InverseMA", params: Optional[Dict] = None):
        """
        초기화
        
        Args:
            name: 전략 이름
            params: 전략 파라미터
                - base_ticker: 이동평균선 계산 기준 종목 (기본: "QQQ")
                - qqq_ticker: QQQ 종목 (기본: "QQQ")
                - tqqq_ticker: TQQQ 종목 (기본: "TQQQ")
                - ma_period: 이동평균 기간 (기본: 200)
                - stock1_pct: QQQ 목표 비율 (기본: 0.5 = 50%)
                - stock2_pct: TQQQ 목표 비율 (기본: 0.5 = 50%)
                - band_threshold: 밴딩 임계값 (기본: 0.05 = 5%)
                - below_mode: 200일선 아래 모드 선택 (기본: "tqqq")
                    - "tqqq": TQQQ 100% 보유 (현재 방식)
                    - "cash": 현금 보유
                    - "covered_call": 커버드콜 ETF 보유 (QYLD, JEPI 등)
                - covered_call_ticker: 커버드콜 ETF 티커 (below_mode="covered_call"일 때 사용, 기본: "QYLD")
        """
        super().__init__(name, params or {})
        self.base_ticker = self.params.get("base_ticker", "QQQ")
        self.qqq_ticker = self.params.get("qqq_ticker", "QQQ")
        self.tqqq_ticker = self.params.get("tqqq_ticker", "TQQQ")
        self.ma_period = self.params.get("ma_period", 200)
        self.stock1_pct = self.params.get("stock1_pct", 0.5)
        self.stock2_pct = self.params.get("stock2_pct", 0.5)
        self.band_threshold = self.params.get("band_threshold", 0.05)
        
        self.current_mode = None
        self.qqq_peak_price = None
        self.below_entry_date = None
        self.use_bond = False
        
        self.below_mode = self.params.get("below_mode", "tqqq")
        self.covered_call_ticker = self.params.get("covered_call_ticker", "QYLD")
        
        if self.below_mode not in ["tqqq", "cash", "covered_call"]:
            logger.warning(f"잘못된 below_mode: {self.below_mode}, 기본값 'tqqq' 사용")
            self.below_mode = "tqqq"
        
        if abs(self.stock1_pct + self.stock2_pct - 1.0) > 0.01:
            logger.warning(f"목표 비율의 합이 1.0이 아닙니다: {self.stock1_pct + self.stock2_pct} (자동 조정)")
            total_pct = self.stock1_pct + self.stock2_pct
            self.stock1_pct = self.stock1_pct / total_pct
            self.stock2_pct = self.stock2_pct / total_pct
        
        self.stock_ticker = self.base_ticker
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        거래 신호 생성
        
        기준 종목(QQQ) 데이터를 기준으로:
        1. 200일 이동평균선 계산
        2. 200일선 위/아래 판단
        3. BELOW 모드 진입 시 QQQ 전고점 추적
        4. 신호 생성:
           - 200일선 위: QQQ:TQQQ 리밸런싱 모드 (Signal=3)
           - 200일선 아래: TQQQ 보유 (Signal=1)
        
        Args:
            data: OHLCV 데이터프레임 (기준 종목 데이터)
        
        Returns:
            신호가 추가된 데이터프레임
            - Signal = 1: 200일선 아래로 전환 (TQQQ 전환)
            - Signal = 3: 200일선 위 모드 유지 (리밸런싱 체크)
            - QQQPeak: BELOW 모드 진입 시점의 QQQ 전고점
            - PeakRecovered: QQQ 전고점 회복 여부
        """
        if not self.validate_data(data):
            raise ValueError("데이터 유효성 검증 실패")
        
        df = data.copy()
        df["Signal"] = 0
        df["QQQPeak"] = None
        df["PeakRecovered"] = False
        
        ma_column = f"MA{self.ma_period}"
        df[ma_column] = df["Close"].rolling(window=self.ma_period, min_periods=1).mean()
        
        first_close = df.iloc[0]["Close"]
        first_ma = df.iloc[0][ma_column]
        
        if first_close >= first_ma:
            df.iloc[0, df.columns.get_loc("Signal")] = 3
            self.current_mode = "ABOVE"
            self.qqq_peak_price = None
            self.below_entry_date = None
        else:
            df.iloc[0, df.columns.get_loc("Signal")] = 1
            self.current_mode = "BELOW"
            self.qqq_peak_price = first_close
            self.below_entry_date = df.index[0]
            df.iloc[0, df.columns.get_loc("QQQPeak")] = self.qqq_peak_price
        
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
                df.iloc[idx, df.columns.get_loc("Signal")] = 3
                self.current_mode = "ABOVE"
                self.qqq_peak_price = None
                self.below_entry_date = None
            elif prev_above_ma and curr_below_ma:
                df.iloc[idx, df.columns.get_loc("Signal")] = 1
                self.current_mode = "BELOW"
                self.qqq_peak_price = prev_close
                self.below_entry_date = df.index[idx - 1]
                df.iloc[idx, df.columns.get_loc("QQQPeak")] = self.qqq_peak_price
            elif curr_above_ma:
                df.iloc[idx, df.columns.get_loc("Signal")] = 3
                self.current_mode = "ABOVE"
                if self.qqq_peak_price is not None and curr_close >= self.qqq_peak_price:
                    df.iloc[idx, df.columns.get_loc("PeakRecovered")] = True
                    self.qqq_peak_price = None
                    self.below_entry_date = None
            else:
                df.iloc[idx, df.columns.get_loc("Signal")] = 0
                self.current_mode = "BELOW"
                if self.qqq_peak_price is not None:
                    if curr_close >= self.qqq_peak_price:
                        df.iloc[idx, df.columns.get_loc("PeakRecovered")] = True
                        self.qqq_peak_price = None
                        self.below_entry_date = None
                    else:
                        df.iloc[idx, df.columns.get_loc("QQQPeak")] = self.qqq_peak_price
        
        signal_count = (df["Signal"] == 1).sum()
        rebalance_signals = (df["Signal"] == 3).sum()
        peak_recovered_count = df["PeakRecovered"].sum()
        
        logger.info(
            f"Inverse MA 전략 신호 생성 완료: {len(df)}개 일봉, "
            f"전환 신호 {signal_count}회, 리밸런싱 체크 {rebalance_signals}회, "
            f"전고점 회복 {peak_recovered_count}회"
        )
        
        return df
    
    def check_banding_rebalance(
        self,
        portfolio_value: float,
        current_qqq_value: float,
        current_tqqq_value: float,
        qqq_price: float,
        tqqq_price: float,
        qqq_quantity: int,
        tqqq_quantity: int
    ) -> tuple[bool, Optional[str]]:
        """
        밴딩 리밸런싱 필요 여부 체크 (200일선 위 모드)
        
        Args:
            portfolio_value: 전체 포트폴리오 가치
            current_qqq_value: QQQ 현재 가치
            current_tqqq_value: TQQQ 현재 가치
            qqq_price: QQQ 현재가
            tqqq_price: TQQQ 현재가
            qqq_quantity: QQQ 보유 수량
            tqqq_quantity: TQQQ 보유 수량
        
        Returns:
            (리밸런싱 필요 여부, 리밸런싱이 필요한 티커)
        """
        if portfolio_value == 0:
            return False, None
        
        current_qqq_pct = current_qqq_value / portfolio_value if portfolio_value > 0 else 0
        current_tqqq_pct = current_tqqq_value / portfolio_value if portfolio_value > 0 else 0
        
        diff_qqq = abs(current_qqq_pct - self.stock1_pct)
        diff_tqqq = abs(current_tqqq_pct - self.stock2_pct)
        
        if diff_qqq >= self.band_threshold or diff_tqqq >= self.band_threshold:
            if diff_qqq >= diff_tqqq:
                return True, self.qqq_ticker
            else:
                return True, self.tqqq_ticker
        
        return False, None
    
    def is_peak_recovered(self, qqq_price: float) -> bool:
        """
        QQQ 전고점 회복 여부 확인
        
        Args:
            qqq_price: 현재 QQQ 가격
        
        Returns:
            전고점 회복 여부
        """
        if self.qqq_peak_price is None:
            return True
        
        return qqq_price >= self.qqq_peak_price
    
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
                - cash: 현재 현금
                - commission_rate: 수수료율
                - mode: 현재 모드 ("ABOVE" 또는 "BELOW")
                - current_qqq_value: QQQ 현재 가치
                - current_tqqq_value: TQQQ 현재 가치
                - qqq_price: QQQ 현재가
        
        Returns:
            거래 수량 (양수=매수, 음수=매도, 0=보유)
        """
        if signal == 0:
            return 0
        
        if price <= 0 or pd.isna(price):
            return 0
        
        ticker = kwargs.get("ticker", None)
        current_quantity = kwargs.get("current_quantity", 0)
        cash = kwargs.get("cash", portfolio_value)
        commission_rate = kwargs.get("commission_rate", 0.001)
        mode = kwargs.get("mode", self.current_mode)
        current_qqq_value = kwargs.get("current_qqq_value", 0.0)
        current_tqqq_value = kwargs.get("current_tqqq_value", 0.0)
        qqq_price = kwargs.get("qqq_price", 0.0)
        
        if ticker is None or mode is None:
            return 0
        
        if signal == 1:
            if mode == "BELOW":
                if self.below_mode == "tqqq":
                    if ticker == self.tqqq_ticker:
                        target_value = portfolio_value * (1 - commission_rate)
                        target_quantity = int(target_value / price) if price > 0 else 0
                        quantity_diff = target_quantity - current_quantity
                        if quantity_diff < 0 and not self.is_peak_recovered(qqq_price):
                            return 0
                        return quantity_diff
                    else:
                        if current_quantity > 0:
                            return -current_quantity
                elif self.below_mode == "cash":
                    if current_quantity > 0:
                        return -current_quantity
                elif self.below_mode == "covered_call":
                    if ticker == self.covered_call_ticker:
                        target_value = portfolio_value * (1 - commission_rate)
                        target_quantity = int(target_value / price) if price > 0 else 0
                        quantity_diff = target_quantity - current_quantity
                        return quantity_diff
                    else:
                        if current_quantity > 0:
                            return -current_quantity
        
        elif signal == 3:
            if mode == "ABOVE":
                if ticker == self.qqq_ticker:
                    target_value = portfolio_value * self.stock1_pct * (1 - commission_rate)
                    target_quantity = int(target_value / price) if price > 0 else 0
                    quantity_diff = target_quantity - current_quantity
                    return quantity_diff
                elif ticker == self.tqqq_ticker:
                    target_value = portfolio_value * self.stock2_pct * (1 - commission_rate)
                    target_quantity = int(target_value / price) if price > 0 else 0
                    quantity_diff = target_quantity - current_quantity
                    return quantity_diff
                else:
                    if current_quantity > 0:
                        return -current_quantity
        
        elif signal == 0:
            if mode == "BELOW":
                if self.below_mode == "tqqq":
                    if ticker == self.tqqq_ticker:
                        if not self.is_peak_recovered(qqq_price):
                            return 0
                elif self.below_mode == "cash":
                    if current_quantity > 0:
                        return -current_quantity
                elif self.below_mode == "covered_call":
                    if ticker == self.covered_call_ticker:
                        return 0
                    elif current_quantity > 0:
                        return -current_quantity
        
        return 0

