"""
적응형 Shannon 전략
평상시 QQQI 100% → 200일선 이탈 시 TQQQ+QQQI Shannon 50:50
"""

from typing import Dict, Optional
import pandas as pd
from loguru import logger

from src.strategy.base import BaseStrategy


class AdaptiveShannonStrategy(BaseStrategy):
    """
    적응형 Shannon 전략
    
    평상시: QQQI 100% (안정적 고배당)
    하락장 (200일선 이탈): TQQQ 50% + QQQI 50% (저점 매수)
    """

    def __init__(self, name: str = "AdaptiveShannon", params: Optional[Dict] = None):
        """
        초기화
        
        Args:
            name: 전략 이름
            params: 전략 파라미터
                - base_ticker: 기준 종목 (200일선 계산용, 기본: "QQQ")
                - stock_ticker: 주식 종목 (기본: "TQQQ")
                - bond_ticker: 채권/배당 종목 (기본: "QQQI")
                - ma_period: 이동평균 기간 (기본: 200)
                - stock_pct: 하락장 시 주식 비율 (기본: 0.5)
                - band_threshold: 리밸런싱 임계값 (기본: 0.1)
        """
        super().__init__(name, params or {})
        self.base_ticker = self.params.get("base_ticker", "QQQ")  # 200일선 계산용
        self.stock_ticker = self.params.get("stock_ticker", "TQQQ")
        self.bond_ticker = self.params.get("bond_ticker", "QQQI")
        self.ma_period = self.params.get("ma_period", 200)
        self.stock_pct = self.params.get("stock_pct", 0.5)
        self.band_threshold = self.params.get("band_threshold", 0.1)
        
        self.current_mode = "SAFE"  # SAFE (QQQI 100%) or SHANNON (50:50)
        self.current_holding = self.bond_ticker
        
        self.use_bond = True  # 항상 bond_ticker 사용

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        거래 신호 생성
        
        Args:
            data: 기준 종목 (QQQ) OHLCV 데이터프레임
        
        Returns:
            신호가 추가된 데이터프레임
            - Signal = 1: 모드 전환
            - Signal = 3: Shannon 리밸런싱 체크
            - Signal = 0: 보유
            - Mode = "SAFE" or "SHANNON"
            - TargetTicker = 목표 보유 종목
        """
        if not self.validate_data(data):
            raise ValueError("데이터 유효성 검증 실패")
        
        df = data.copy()
        df["Signal"] = 0
        df["Mode"] = "SAFE"
        df["TargetTicker"] = self.bond_ticker
        
        # 이동평균 계산
        ma_column = f"MA{self.ma_period}"
        df[ma_column] = df["Close"].rolling(window=self.ma_period, min_periods=1).mean()
        
        # 초기 모드 결정
        first_close = df.iloc[0]["Close"]
        first_ma = df.iloc[0][ma_column]
        
        if first_close >= first_ma:
            # 200일선 위 = SAFE 모드 (QQQI 100%)
            df.iloc[0, df.columns.get_loc("Signal")] = 1
            df.iloc[0, df.columns.get_loc("Mode")] = "SAFE"
            df.iloc[0, df.columns.get_loc("TargetTicker")] = self.bond_ticker
            self.current_mode = "SAFE"
            self.current_holding = self.bond_ticker
        else:
            # 200일선 아래 = SHANNON 모드 (TQQQ+QQQI 50:50)
            df.iloc[0, df.columns.get_loc("Signal")] = 1
            df.iloc[0, df.columns.get_loc("Mode")] = "SHANNON"
            df.iloc[0, df.columns.get_loc("TargetTicker")] = "SHANNON"
            self.current_mode = "SHANNON"
            self.current_holding = "SHANNON"
        
        # 모드 전환 체크
        mode_changes = 0
        for idx in range(1, len(df)):
            curr_close = df.iloc[idx]["Close"]
            curr_ma = df.iloc[idx][ma_column]
            prev_mode = df.iloc[idx - 1]["Mode"]
            
            # 200일선 위/아래 확인
            is_above_ma = curr_close >= curr_ma
            
            # 모드 전환 조건
            if is_above_ma and prev_mode == "SHANNON":
                # 하락장 → 상승장: SHANNON → SAFE
                df.iloc[idx, df.columns.get_loc("Signal")] = 1
                df.iloc[idx, df.columns.get_loc("Mode")] = "SAFE"
                df.iloc[idx, df.columns.get_loc("TargetTicker")] = self.bond_ticker
                self.current_mode = "SAFE"
                mode_changes += 1
            elif not is_above_ma and prev_mode == "SAFE":
                # 상승장 → 하락장: SAFE → SHANNON
                df.iloc[idx, df.columns.get_loc("Signal")] = 1
                df.iloc[idx, df.columns.get_loc("Mode")] = "SHANNON"
                df.iloc[idx, df.columns.get_loc("TargetTicker")] = "SHANNON"
                self.current_mode = "SHANNON"
                mode_changes += 1
            else:
                # 모드 유지
                df.iloc[idx, df.columns.get_loc("Mode")] = prev_mode
                if prev_mode == "SHANNON":
                    # Shannon 모드에서는 매일 리밸런싱 체크
                    df.iloc[idx, df.columns.get_loc("Signal")] = 3
                    df.iloc[idx, df.columns.get_loc("TargetTicker")] = "SHANNON"
                else:
                    # SAFE 모드는 보유만
                    df.iloc[idx, df.columns.get_loc("TargetTicker")] = self.bond_ticker
        
        safe_days = (df["Mode"] == "SAFE").sum()
        shannon_days = (df["Mode"] == "SHANNON").sum()
        
        logger.info(
            f"적응형 Shannon 신호 생성 완료: {len(df)}개 일봉, "
            f"모드 전환 {mode_changes}회, "
            f"SAFE 모드 {safe_days}일, SHANNON 모드 {shannon_days}일"
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
            signal: 신호
            **kwargs: 추가 파라미터
                - ticker: 현재 거래하는 종목
                - current_quantity: 현재 보유 수량
                - mode: 현재 모드 (SAFE or SHANNON)
                - current_stock_value: TQQQ 현재 가치
                - current_bond_value: QQQI 현재 가치
        
        Returns:
            거래 수량 (양수=매수, 음수=매도, 0=보유)
        """
        if signal == 0:
            return 0
        
        ticker = kwargs.get("ticker", None)
        current_quantity = kwargs.get("current_quantity", 0)
        commission_rate = kwargs.get("commission_rate", 0.001)
        mode = kwargs.get("mode", "SAFE")
        
        if signal == 1:
            # 모드 전환
            if mode == "SAFE":
                # QQQI 100% 목표
                if ticker == self.bond_ticker:
                    # QQQI 매수
                    target_value = portfolio_value * (1 - commission_rate)
                    target_quantity = int(target_value / price)
                    return target_quantity - current_quantity
                else:
                    # TQQQ 전량 매도
                    return -current_quantity if current_quantity > 0 else 0
            
            elif mode == "SHANNON":
                # TQQQ 50% + QQQI 50% 목표
                if ticker == self.stock_ticker:
                    # TQQQ 50%
                    target_value = portfolio_value * self.stock_pct
                    target_quantity = int(target_value / price)
                    return target_quantity - current_quantity
                elif ticker == self.bond_ticker:
                    # QQQI 50%
                    target_value = portfolio_value * (1 - self.stock_pct)
                    target_quantity = int(target_value / price)
                    return target_quantity - current_quantity
        
        elif signal == 3:
            # Shannon 모드에서 리밸런싱 체크
            if mode != "SHANNON":
                return 0
            
            current_stock_value = kwargs.get("current_stock_value", 0.0)
            current_bond_value = kwargs.get("current_bond_value", 0.0)
            
            # 현재 비율
            if portfolio_value == 0:
                return 0
            
            # 목표 수량 계산
            if ticker == self.stock_ticker:
                target_value = portfolio_value * self.stock_pct
                target_quantity = int(target_value / price)
            elif ticker == self.bond_ticker:
                target_value = portfolio_value * (1 - self.stock_pct)
                target_quantity = int(target_value / price)
            else:
                return 0
            
            # 밴딩 체크
            current_stock_pct = current_stock_value / portfolio_value
            diff = abs(current_stock_pct - self.stock_pct)
            
            if diff >= self.band_threshold:
                # 리밸런싱 필요
                return target_quantity - current_quantity
        
        return 0

