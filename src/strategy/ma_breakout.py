"""
이동평균선 + 전 고점 돌파 전략
n일선 아래: TQQQ 보유
전 고점 돌파 시: QLD로 전환
"""

from typing import Dict, Optional
import pandas as pd
import numpy as np
from loguru import logger

from src.strategy.base import BaseStrategy


class MovingAverageBreakoutStrategy(BaseStrategy):
    """
    이동평균선 + 전 고점 돌파 전략
    
    로직:
    - n일선 아래: TQQQ 보유
    - n일선 위 + 전 고점 돌파: QLD로 전환
    - n일선 위 + 전 고점 미돌파: 이전 보유 종목 유지 (TQQQ 또는 QLD)
    """
    
    def __init__(self, name: str = "MovingAverageBreakout", params: Optional[Dict] = None):
        """
        초기화
        
        Args:
            name: 전략 이름
            params: 전략 파라미터
                - base_ticker: 기준 종목 (이동평균선 계산용, 기본: "TQQQ")
                - conservative_ticker: 보수적 종목 (n일선 아래, 기본: "TQQQ")
                - aggressive_ticker: 공격적 종목 (전 고점 돌파 시, 기본: "QLD")
                - ma_period: 이동평균 기간 (기본: 200)
                - lookback_period: 전 고점 계산 기간 (기본: 252일, 약 1년)
        """
        super().__init__(name, params or {})
        self.base_ticker = self.params.get("base_ticker", "TQQQ")  # 이동평균선 계산 기준 종목
        self.conservative_ticker = self.params.get("conservative_ticker", "TQQQ")  # n일선 아래 시 보유
        self.aggressive_ticker = self.params.get("aggressive_ticker", "QLD")  # 전 고점 돌파 시 보유
        self.ma_period = self.params.get("ma_period", 200)
        self.lookback_period = self.params.get("lookback_period", 252)  # 전 고점 계산 기간
        self.current_holding = None
        
        # 백테스팅 엔진에서 사용할 속성들
        self.stock_ticker = self.base_ticker  # 다중 종목 엔진 호환성
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        거래 신호 생성
        
        기준 종목의 데이터를 기준으로:
        1. n일 이동평균선 계산
        2. 전 고점 (lookback_period일 최고가) 계산
        3. 신호 생성:
           - n일선 아래: conservative_ticker (TQQQ)
           - n일선 위 + 전 고점 돌파: aggressive_ticker (QLD)
           - 그 외: 이전 보유 종목 유지
        
        Args:
            data: OHLCV 데이터프레임 (기준 종목 데이터)
        
        Returns:
            신호가 추가된 데이터프레임
            - Signal = 1: 초기 매수 또는 전환 필요
            - Signal = 0: 보유
            - TargetTicker: 목표 종목 (TQQQ 또는 QLD)
        """
        if not self.validate_data(data):
            raise ValueError("데이터 유효성 검증 실패")
        
        df = data.copy()
        df["Signal"] = 0
        df["TargetTicker"] = None
        
        # 이동평균선 계산
        ma_column = f"MA{self.ma_period}"
        df[ma_column] = df["Close"].rolling(window=self.ma_period, min_periods=1).mean()
        
        # 전 고점 계산 (lookback_period일 최고가)
        high_column = f"High{self.lookback_period}"
        df[high_column] = df["High"].rolling(window=self.lookback_period, min_periods=1).max()
        
        # 이전 전 고점 (돌파 판단용: 이전 시점의 최고가)
        df["PrevHigh"] = df[high_column].shift(1)
        
        # 첫날 처리
        first_close = df.iloc[0]["Close"]
        first_ma = df.iloc[0][ma_column]
        # 첫날은 이전 최고가가 없으므로 첫날 High를 기준으로
        first_prev_high = df.iloc[0]["High"] if len(df) > 0 else first_close
        
        if first_close < first_ma:
            # n일선 아래: conservative_ticker 보유
            df.iloc[0, df.columns.get_loc("Signal")] = 1
            df.iloc[0, df.columns.get_loc("TargetTicker")] = self.conservative_ticker
            self.current_holding = self.conservative_ticker
        elif first_close >= first_ma:
            # n일선 위: 전 고점 돌파 여부 확인
            if first_close > first_prev_high:
                # 전 고점 돌파: aggressive_ticker 보유
                df.iloc[0, df.columns.get_loc("Signal")] = 1
                df.iloc[0, df.columns.get_loc("TargetTicker")] = self.aggressive_ticker
                self.current_holding = self.aggressive_ticker
            else:
                # 전 고점 미돌파: conservative_ticker 보유
                df.iloc[0, df.columns.get_loc("Signal")] = 1
                df.iloc[0, df.columns.get_loc("TargetTicker")] = self.conservative_ticker
                self.current_holding = self.conservative_ticker
        
        # 나머지 날짜 처리
        for idx in range(1, len(df)):
            curr_close = df.iloc[idx]["Close"]
            curr_ma = df.iloc[idx][ma_column]
            curr_high = df.iloc[idx][high_column]
            prev_high = df.iloc[idx]["PrevHigh"]
            
            prev_target = df.iloc[idx - 1, df.columns.get_loc("TargetTicker")]
            prev_close = df.iloc[idx - 1]["Close"]
            prev_ma = df.iloc[idx - 1][ma_column]
            
            # n일선 위치 변화 감지
            prev_below_ma = prev_close < prev_ma
            curr_below_ma = curr_close < curr_ma
            
            # 전 고점 돌파 감지 (이전 최고가를 현재가가 넘었는지)
            prev_below_prev_high = prev_close < prev_high if not pd.isna(prev_high) else True
            curr_above_prev_high = curr_close > prev_high if not pd.isna(prev_high) else False
            
            # 신호 생성 로직
            target = None
            signal = 0
            
            if curr_below_ma:
                # n일선 아래: 항상 conservative_ticker
                target = self.conservative_ticker
                if prev_target != self.conservative_ticker:
                    signal = 1
                    self.current_holding = self.conservative_ticker
            elif not curr_below_ma:
                # n일선 위
                if prev_below_prev_high and curr_above_prev_high:
                    # 전 고점 돌파: aggressive_ticker로 전환
                    target = self.aggressive_ticker
                    if prev_target != self.aggressive_ticker:
                        signal = 1
                        self.current_holding = self.aggressive_ticker
                elif prev_below_ma and not curr_below_ma:
                    # n일선 아래 → 위로 전환: 전 고점 확인
                    if curr_above_prev_high:
                        # 전 고점 돌파 상태: aggressive_ticker
                        target = self.aggressive_ticker
                        signal = 1
                        self.current_holding = self.aggressive_ticker
                    else:
                        # 전 고점 미돌파: conservative_ticker
                        target = self.conservative_ticker
                        signal = 1
                        self.current_holding = self.conservative_ticker
                else:
                    # n일선 위 유지: 이전 목표 종목 유지
                    target = prev_target
            
            if target is None:
                target = prev_target
            
            if signal == 1:
                df.iloc[idx, df.columns.get_loc("Signal")] = 1
            df.iloc[idx, df.columns.get_loc("TargetTicker")] = target
        
        signal_count = (df["Signal"] == 1).sum()
        logger.info(
            f"MA Breakout 전략 신호 생성 완료: {len(df)}개 일봉, "
            f"전환 신호 {signal_count}회 (MA={self.ma_period}일, 전고점={self.lookback_period}일)"
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
        
        전략:
        - 목표 종목: 100% 매수
        - 목표 종목이 아닌 종목: 전량 매도 (반드시 매도 후 매수)
        
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
            # 목표 종목이 아닌 종목: 무조건 전량 매도 (매도 후 매수를 위해)
            else:
                # 보유 수량이 있으면 무조건 매도
                if current_quantity > 0:
                    return -current_quantity
        
        return 0

