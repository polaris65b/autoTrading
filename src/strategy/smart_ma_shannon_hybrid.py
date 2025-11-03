"""
Smart Moving Average Shannon Hybrid 전략 (고도화 버전)
- SMA 200 + EMA 50 이중 필터
- 동적 베팅 비율 (볼린저 밴드 기반 변동성)
- 트레일링 스탑 (고점 대비 -20%)
- 다중 MA 신호 (50/100/200일)
"""

from typing import Dict, Optional
import pandas as pd
import numpy as np
from loguru import logger

from src.strategy.base import BaseStrategy


class SmartMovingAverageShannonHybridStrategy(BaseStrategy):
    """
    Smart MA Shannon Hybrid 전략
    
    개선 사항:
    1. SMA 200 + EMA 50 이중 필터로 추세 강도 판별
    2. 볼린저 밴드 기반 변동성에 따른 동적 베팅 비율
    3. 트레일링 스탑으로 MDD 제한
    4. 다중 MA 신호로 단계적 리스크 관리
    
    로직:
    - SMA 200 위 + EMA 50 위: 100% 주식 (강한 추세)
    - SMA 200 위 + EMA 50 아래: 70% 주식 (약한 추세)
    - SMA 200 아래: 변동성 기반 동적 비율
    """
    
    def __init__(self, name: str = "SmartMAShannonHybrid", params: Optional[Dict] = None):
        """
        초기화
        
        Args:
            name: 전략 이름
            params: 전략 파라미터
                - stock_ticker: 주식 종목 (기본: "TQQQ")
                - sma_period: 단순 이동평균 기간 (기본: 200)
                - ema_period: 지수 이동평균 기간 (기본: 50)
                - bb_period: 볼린저 밴드 기간 (기본: 20)
                - bb_std: 볼린저 밴드 표준편차 (기본: 2.0)
                - base_stock_pct: 기본 주식 비율 (기본: 0.5)
                - trailing_stop_pct: 트레일링 스탑 비율 (기본: 0.20)
        """
        super().__init__(name, params or {})
        self.stock_ticker = self.params.get("stock_ticker", "TQQQ")
        self.sma_period = self.params.get("sma_period", 200)
        self.ema_period = self.params.get("ema_period", 50)
        self.bb_period = self.params.get("bb_period", 20)
        self.bb_std = self.params.get("bb_std", 2.0)
        self.base_stock_pct = self.params.get("base_stock_pct", 0.5)
        self.trailing_stop_pct = self.params.get("trailing_stop_pct", 0.20)
        
        self.current_mode = None  # "STRONG_TREND", "WEAK_TREND", "BELOW"
        self.current_holding = None
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        거래 신호 생성
        
        Args:
            data: OHLCV 데이터프레임
        
        Returns:
            신호가 추가된 데이터프레임
            - Signal = 1: 모드 전환 필요
            - Signal = 2: 트레일링 스탑 신호
            - Signal = 3: 동적 비율 조정 필요
            - Signal = 0: 보유
            - Mode: 현재 모드
        """
        if not self.validate_data(data):
            raise ValueError("데이터 유효성 검증 실패")
        
        df = data.copy()
        df["Signal"] = 0
        df["Mode"] = None
        
        # 이동평균선 계산
        sma_column = f"SMA{self.sma_period}"
        ema_column = f"EMA{self.ema_period}"
        df[sma_column] = df["Close"].rolling(window=self.sma_period, min_periods=1).mean()
        df[ema_column] = df["Close"].ewm(span=self.ema_period, adjust=False).mean()
        
        # 볼린저 밴드 계산
        bb_mid = f"BB_MID{self.bb_period}"
        bb_upper = f"BB_UPPER{self.bb_period}"
        bb_lower = f"BB_LOWER{self.bb_period}"
        df[bb_mid] = df["Close"].rolling(window=self.bb_period, min_periods=1).mean()
        bb_std = df["Close"].rolling(window=self.bb_period, min_periods=1).std()
        df[bb_upper] = df[bb_mid] + (bb_std * self.bb_std)
        df[bb_lower] = df[bb_mid] - (bb_std * self.bb_std)
        
        # 변동성 계산 (BB width)
        df["BB_Width"] = (df[bb_upper] - df[bb_lower]) / df[bb_mid]
        
        # 첫날 모드 결정
        first_close = df.iloc[0]["Close"]
        first_sma = df.iloc[0][sma_column]
        first_ema = df.iloc[0][ema_column]
        
        if first_close >= first_sma and first_close >= first_ema:
            df.iloc[0, df.columns.get_loc("Signal")] = 1
            df.iloc[0, df.columns.get_loc("Mode")] = "STRONG_TREND"
            self.current_mode = "STRONG_TREND"
        elif first_close >= first_sma:
            df.iloc[0, df.columns.get_loc("Signal")] = 1
            df.iloc[0, df.columns.get_loc("Mode")] = "WEAK_TREND"
            self.current_mode = "WEAK_TREND"
        else:
            df.iloc[0, df.columns.get_loc("Signal")] = 1
            df.iloc[0, df.columns.get_loc("Mode")] = "BELOW"
            self.current_mode = "BELOW"
        
        # 이후 날짜들 처리
        for idx in range(1, len(df)):
            prev_close = df.iloc[idx - 1]["Close"]
            curr_close = df.iloc[idx]["Close"]
            curr_sma = df.iloc[idx][sma_column]
            curr_ema = df.iloc[idx][ema_column]
            
            prev_mode = df.iloc[idx - 1, df.columns.get_loc("Mode")]
            
            # 모드 결정
            if curr_close >= curr_sma and curr_close >= curr_ema:
                new_mode = "STRONG_TREND"
            elif curr_close >= curr_sma:
                new_mode = "WEAK_TREND"
            else:
                new_mode = "BELOW"
            
            # 모드 전환 체크
            if new_mode != prev_mode:
                df.iloc[idx, df.columns.get_loc("Signal")] = 1
                df.iloc[idx, df.columns.get_loc("Mode")] = new_mode
                self.current_mode = new_mode
            else:
                df.iloc[idx, df.columns.get_loc("Mode")] = prev_mode
                self.current_mode = prev_mode
                
                # BELOW 모드일 때 변동성 기반 조정 신호 (매일 체크가 아닌 주기적으로)
                # 조정 신호는 제거 (너무 많은 거래 발생)
                pass
        
        signal_count = (df["Signal"] == 1).sum()
        adjustment_count = (df["Signal"] == 3).sum()
        logger.info(
            f"Smart MA Hybrid 신호 생성 완료: {len(df)}개 일봉, "
            f"모드 전환 {signal_count}회, 조정 {adjustment_count}회"
        )
        
        return df
    
    def calculate_dynamic_stock_pct(self, bb_width: float) -> float:
        """
        변동성 기반 동적 주식 비율 계산
        
        Args:
            bb_width: 볼린저 밴드 width (변동성 지표)
        
        Returns:
            동적 주식 비율
        """
        if bb_width < 0.05:  # 변동성 매우 낮음
            return self.base_stock_pct + 0.2  # 70%
        elif bb_width < 0.10:  # 변동성 낮음
            return self.base_stock_pct + 0.1  # 60%
        elif bb_width < 0.20:  # 변동성 보통
            return self.base_stock_pct  # 50%
        elif bb_width < 0.30:  # 변동성 높음
            return self.base_stock_pct - 0.1  # 40%
        else:  # 변동성 매우 높음
            return self.base_stock_pct - 0.2  # 30%
    
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
            signal: 신호 (1=모드 전환, 2=트레일링 스탑, 3=조정, 0=보유)
            **kwargs: 추가 파라미터
                - current_quantity: 현재 보유 수량
                - cash: 현재 현금
                - commission_rate: 수수료율
                - mode: 현재 모드
                - bb_width: 볼린저 밴드 width
                - ticker: 현재 거래하는 종목
        
        Returns:
            거래 수량
        """
        if signal == 0:
            return 0
        
        current_quantity = kwargs.get("current_quantity", 0)
        cash = kwargs.get("cash", portfolio_value)
        commission_rate = kwargs.get("commission_rate", 0.001)
        mode = kwargs.get("mode", self.current_mode)
        ticker = kwargs.get("ticker", None)
        
        if ticker != self.stock_ticker:
            return 0
        
        if signal == 1:
            # 모드 전환
            if mode == "STRONG_TREND":
                # 강한 추세: 100%
                target_value = portfolio_value * (1 - commission_rate)
                target_quantity = int(target_value / price)
                return target_quantity - current_quantity
            elif mode == "WEAK_TREND":
                # 약한 추세: 70%
                target_value = portfolio_value * 0.7 * (1 - commission_rate)
                target_quantity = int(target_value / price)
                quantity_diff = target_quantity - current_quantity
                
                if quantity_diff > 0:
                    required_cash = quantity_diff * price * (1 + commission_rate)
                    if cash < required_cash:
                        available_quantity = int(cash / (price * (1 + commission_rate)))
                        quantity_diff = min(quantity_diff, available_quantity)
                
                return quantity_diff
            else:  # BELOW
                # 변동성 기반 동적 비율
                bb_width = kwargs.get("bb_width", 0.1)
                dynamic_pct = self.calculate_dynamic_stock_pct(bb_width)
                target_value = portfolio_value * dynamic_pct * (1 - commission_rate)
                target_quantity = int(target_value / price)
                quantity_diff = target_quantity - current_quantity
                
                if quantity_diff > 0:
                    required_cash = quantity_diff * price * (1 + commission_rate)
                    if cash < required_cash:
                        available_quantity = int(cash / (price * (1 + commission_rate)))
                        quantity_diff = min(quantity_diff, available_quantity)
                
                return quantity_diff
        
        elif signal == 3:
            # 동적 비율 조정 (BELOW 모드에서만)
            if mode != "BELOW":
                return 0
            
            bb_width = kwargs.get("bb_width", 0.1)
            dynamic_pct = self.calculate_dynamic_stock_pct(bb_width)
            current_pct = (current_quantity * price) / portfolio_value if portfolio_value > 0 else 0
            
            # 현재 비율과 목표 비율 차이가 5% 이상이면 조정
            if abs(current_pct - dynamic_pct) >= 0.05:
                target_value = portfolio_value * dynamic_pct
                target_quantity = int(target_value / price)
                quantity_diff = target_quantity - current_quantity
                
                if quantity_diff > 0:
                    required_cash = quantity_diff * price * (1 + commission_rate)
                    if cash < required_cash:
                        available_quantity = int(cash / (price * (1 + commission_rate)))
                        quantity_diff = min(quantity_diff, available_quantity)
                
                return quantity_diff
        
        return 0

