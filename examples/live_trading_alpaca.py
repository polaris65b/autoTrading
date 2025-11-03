#!/usr/bin/env python3
"""
Alpaca Paper Trading 예제

실전 매매를 위한 기본 템플릿
"""

import alpaca_trade_api as tradeapi
from datetime import datetime, timedelta
import pandas as pd
import sys
import os

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.strategy.ma_shannon_hybrid import MovingAverageShannonHybridStrategy
from loguru import logger

# API 키 설정 (환경 변수 또는 직접 입력)
API_KEY = os.getenv('ALPACA_API_KEY', 'YOUR_API_KEY')
SECRET_KEY = os.getenv('ALPACA_SECRET_KEY', 'YOUR_SECRET_KEY')


class LiveTradingBot:
    """실전 매매 봇"""
    
    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        """
        초기화
        
        Args:
            api_key: Alpaca API Key
            secret_key: Alpaca Secret Key
            paper: Paper trading 여부 (기본: True)
        """
        # API 연결
        base_url = 'https://paper-api.alpaca.markets' if paper else 'https://api.alpaca.markets'
        self.api = tradeapi.REST(api_key, secret_key, base_url, api_version='v2')
        
        # 전략 초기화
        self.strategy = MovingAverageShannonHybridStrategy(
            name="MA Shannon Hybrid Live",
            params={
                "stock_ticker": "TQQQ",
                "ma_period": 200,
                "stock_pct": 0.5,
                "band_threshold": 0.1
            }
        )
        
        logger.info(f"✅ Live Trading Bot 초기화 완료 (Paper Trading: {paper})")
    
    def check_account(self):
        """계좌 정보 조회"""
        try:
            account = self.api.get_account()
            cash = float(account.cash)
            buying_power = float(account.buying_power)
            portfolio_value = float(account.portfolio_value)
            
            logger.info("=" * 50)
            logger.info("📊 계좌 현황")
            logger.info(f"현금: ${cash:,.2f}")
            logger.info(f"구매력: ${buying_power:,.2f}")
            logger.info(f"포트폴리오 가치: ${portfolio_value:,.2f}")
            logger.info("=" * 50)
            
            return {
                'cash': cash,
                'buying_power': buying_power,
                'portfolio_value': portfolio_value
            }
        except Exception as e:
            logger.error(f"계좌 조회 실패: {e}")
            return None
    
    def get_current_positions(self):
        """현재 포지션 조회"""
        try:
            positions = self.api.list_positions()
            if positions:
                logger.info("📈 현재 보유 포지션:")
                for pos in positions:
                    market_value = float(pos.market_value)
                    pnl_pct = float(pos.unrealized_plpc) * 100
                    logger.info(
                        f"  {pos.symbol}: {pos.qty}주 "
                        f"(평가금: ${market_value:,.2f}, 손익: {pnl_pct:.2f}%)"
                    )
                return positions
            else:
                logger.info("📈 보유 포지션 없음")
                return []
        except Exception as e:
            logger.error(f"포지션 조회 실패: {e}")
            return []
    
    def get_historical_data(self, symbol: str, days: int = 400) -> pd.DataFrame:
        """과거 데이터 수집"""
        try:
            end_date = datetime.now().date() - timedelta(days=1)  # 어제까지
            start_date = end_date - timedelta(days=days)
            
            bars = self.api.get_bars(
                symbol,
                tradeapi.TimeFrame.Day,
                start=start_date.isoformat(),
                end=end_date.isoformat(),
                adjustment='raw'
            ).df
            
            # 컬럼명 변경 (yfinance 형식과 맞춤)
            bars.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            
            logger.info(f"📊 {symbol} 데이터 수집 완료: {len(bars)}일")
            return bars
        except Exception as e:
            logger.error(f"데이터 수집 실패: {e}")
            return pd.DataFrame()
    
    def generate_signals(self, data: pd.DataFrame):
        """트레이딩 신호 생성"""
        try:
            signals = self.strategy.generate_signals(data)
            latest = signals.iloc[-1]
            
            logger.info("=" * 50)
            logger.info("🎯 트레이딩 신호")
            logger.info(f"현재 모드: {latest['Mode']}")
            logger.info(f"신호 타입: {latest['Signal']}")
            logger.info(f"현재가: ${data['Close'].iloc[-1]:.2f}")
            logger.info("=" * 50)
            
            return latest, data['Close'].iloc[-1]
        except Exception as e:
            logger.error(f"신호 생성 실패: {e}")
            return None, None
    
    def execute_trade(self, signal_data, current_price: float, account_info: dict):
        """거래 실행"""
        if signal_data is None:
            logger.warning("신호 데이터가 없어 거래를 건너뜁니다")
            return
        
        signal = signal_data['Signal']
        mode = signal_data['Mode']
        
        try:
            # 현재 TQQQ 포지션 조회
            tqqq_position = self.api.get_position('TQQQ') if self.api.get_position('TQQQ') else None
            
            if signal == 1:  # 모드 전환
                if mode == 'ABOVE':
                    # TQQQ 100% 매수
                    self._buy_tqqq(account_info['buying_power'], current_price, target_pct=0.95)
                else:
                    # TQQQ 50%로 축소
                    if tqqq_position:
                        self._reduce_tqqq_position(tqqq_position)
            elif signal == 3:  # 밴딩 리밸런싱
                if tqqq_position:
                    self._rebalance_tqqq_position(tqqq_position, current_price, mode)
            
        except Exception as e:
            logger.error(f"거래 실행 중 오류: {e}")
    
    def _buy_tqqq(self, buying_power: float, price: float, target_pct: float = 0.95):
        """TQQQ 매수"""
        # 매수 금액 계산
        investment_amount = buying_power * target_pct
        
        # 수량 계산
        qty = int(investment_amount / price)
        
        if qty <= 0:
            logger.warning("매수 수량이 0입니다")
            return
        
        try:
            order = self.api.submit_order(
                symbol='TQQQ',
                qty=qty,
                side='buy',
                type='market',
                time_in_force='day'
            )
            logger.info(f"✅ TQQQ {qty}주 시장가 매수 주문 제출")
            logger.info(f"주문 ID: {order.id}")
        except Exception as e:
            logger.error(f"매수 주문 실패: {e}")
    
    def _reduce_tqqq_position(self, position):
        """TQQQ 포지션 축소 (50% 매도)"""
        current_qty = int(position.qty)
        sell_qty = current_qty // 2
        
        if sell_qty <= 0:
            logger.warning("매도 수량이 0입니다")
            return
        
        try:
            order = self.api.submit_order(
                symbol='TQQQ',
                qty=sell_qty,
                side='sell',
                type='market',
                time_in_force='day'
            )
            logger.info(f"📉 TQQQ {sell_qty}주 시장가 매도 주문 제출")
            logger.info(f"주문 ID: {order.id}")
        except Exception as e:
            logger.error(f"매도 주문 실패: {e}")
    
    def _rebalance_tqqq_position(self, position, price: float, mode: str):
        """TQQQ 포지션 리밸런싱"""
        # TODO: 밴딩 로직 구현
        logger.info("리밸런싱 로직은 나중에 구현 예정")
    
    def run(self):
        """메인 실행 함수"""
        logger.info("🚀 Live Trading Bot 시작")
        
        # 1. 계좌 정보 조회
        account_info = self.check_account()
        if account_info is None:
            logger.error("계좌 정보를 가져올 수 없습니다")
            return
        
        # 2. 현재 포지션 조회
        self.get_current_positions()
        
        # 3. 과거 데이터 수집
        data = self.get_historical_data('TQQQ', days=400)
        if data.empty:
            logger.error("데이터를 가져올 수 없습니다")
            return
        
        # 4. 신호 생성
        signal_data, current_price = self.generate_signals(data)
        if signal_data is None:
            logger.error("신호를 생성할 수 없습니다")
            return
        
        # 5. 거래 실행 (사용자 확인 후)
        logger.info("\n⚠️  실제 거래를 실행하시겠습니까?")
        logger.info("실행하려면 코드에서 주석을 해제하세요")
        
        # execute_trade 함수 호출을 주석 처리 (안전)
        # self.execute_trade(signal_data, current_price, account_info)
        
        logger.info("✅ Live Trading Bot 종료")


def main():
    """메인 함수"""
    # API 키 설정 확인
    if API_KEY == 'YOUR_API_KEY' or SECRET_KEY == 'YOUR_SECRET_KEY':
        logger.error("❌ API 키를 설정해주세요!")
        logger.info("1. Alpaca 계정 생성: https://alpaca.markets/")
        logger.info("2. API 키 발급: Dashboard → Your API Keys")
        logger.info("3. 환경 변수 설정:")
        logger.info("   export ALPACA_API_KEY='your_key'")
        logger.info("   export ALPACA_SECRET_KEY='your_secret'")
        logger.info("")
        logger.info("또는 코드에서 직접 설정:")
        logger.info("   API_KEY = 'your_key'")
        logger.info("   SECRET_KEY = 'your_secret'")
        return
    
    # 봇 실행
    bot = LiveTradingBot(API_KEY, SECRET_KEY, paper=True)
    bot.run()


if __name__ == '__main__':
    main()

