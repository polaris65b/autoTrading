#!/usr/bin/env python3
"""
범용 백테스팅 스크립트
설정 파일을 읽어서 백테스팅 실행
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config.loader import load_config
from src.data.collector import StockDataCollector
from src.backtest.simple_engine import SimpleBacktestEngine
from src.backtest.multi_asset_engine import MultiAssetBacktestEngine
from src.strategy.buyhold import BuyHoldStrategy
from src.strategy.shannon import ShannonStrategy
from src.strategy.moving_average import MovingAverageStrategy
from src.strategy.ma_shannon_hybrid import MovingAverageShannonHybridStrategy
from src.strategy.smart_ma_shannon_hybrid import SmartMovingAverageShannonHybridStrategy as SmartMAStrategy
from src.utils.logger import setup_logger
from loguru import logger

# 전략 매핑 (전략 이름 -> 전략 클래스)
STRATEGY_MAP = {
    "buyhold": BuyHoldStrategy,
    "shannon": ShannonStrategy,
    "moving_average": MovingAverageStrategy,
    "ma": MovingAverageStrategy,
    "ma_shannon_hybrid": MovingAverageShannonHybridStrategy,
    "smart_ma_shannon_hybrid": SmartMAStrategy,
}


def run_backtest(config_path: str = "config.yml"):
    """
    백테스팅 실행
    
    Args:
        config_path: 설정 파일 경로
    """
    setup_logger()
    
    logger.info("="*70)
    logger.info("백테스팅 실행")
    logger.info("="*70)
    
    # 1. 설정 로드
    logger.info(f"\n설정 파일 로드: {config_path}")
    try:
        config = load_config(Path(config_path))
    except FileNotFoundError:
        logger.error(f"설정 파일을 찾을 수 없습니다: {config_path}")
        logger.info(f"예제 파일을 복사하세요: cp config.yml.example config.yml")
        return
    
    logger.info(f"백테스팅 기간: {config.backtest.start_date} ~ {config.backtest.end_date}")
    logger.info(f"초기 자본금: ${config.backtest.initial_cash:,.0f}")
    
    # 2. 활성화된 전략 확인
    enabled_strategies = [s for s in config.portfolio.strategies if s.enabled]
    if not enabled_strategies:
        logger.error("활성화된 전략이 없습니다")
        return
    
    # 3. 백테스팅 종목 확인
    tickers = config.assets.tickers
    logger.info(f"\n백테스팅 종목: {', '.join(tickers)}")
    
    # 4. 데이터 수집
    collector = StockDataCollector()
    logger.info(f"\n데이터 수집 중...")
    data_dict = {}
    try:
        for ticker in tickers:
            df = collector.collect_ohlcv(
                ticker=ticker,
                start_date=config.backtest.start_date,
                end_date=config.backtest.end_date
            )
            data_dict[ticker] = df
            logger.info(f"{ticker} 데이터 수집 완료: {len(df)}개 일봉")
    except Exception as e:
        logger.error(f"데이터 수집 실패: {e}")
        return
    
    # 5. 백테스팅 실행 (여러 전략 비교 가능)
    strategy_results = []  # 전략별 결과 저장
    
    for strategy_config in enabled_strategies:
        logger.info("\n" + "="*70)
        logger.info(f"전략: {strategy_config.name}")
        logger.info("="*70)
        
        # 전략 클래스 가져오기
        strategy_class = STRATEGY_MAP.get(strategy_config.name.lower())
        if not strategy_class:
            logger.warning(f"지원하지 않는 전략입니다: {strategy_config.name}")
            logger.info(f"지원되는 전략: {', '.join(STRATEGY_MAP.keys())}")
            continue
        
        # 전략 인스턴스 생성
        strategy_params = strategy_config.params.model_dump() if strategy_config.params else {}
        strategy = strategy_class(name=strategy_config.name, params=strategy_params)
        
        # 다중 종목 사용 여부 확인
        use_multi_asset = False
        
        # Shannon 전략: bond_ticker가 설정된 경우
        if isinstance(strategy, ShannonStrategy) and strategy.use_bond:
            use_multi_asset = True
            if len(tickers) < 2:
                logger.warning(f"{strategy.name}: bond_ticker가 설정되었지만 종목이 1개만 제공되었습니다.")
                logger.warning("다중 종목 백테스팅을 위해 tickers에 주식과 채권 종목을 모두 포함하세요.")
                continue
        
        # MovingAverage 전략: 항상 다중 종목 필요 (주식 + 채권)
        elif isinstance(strategy, MovingAverageStrategy):
            use_multi_asset = True
            if len(tickers) < 2:
                logger.warning(f"{strategy.name}: 주식과 채권 종목이 모두 필요합니다.")
                logger.warning(f"현재 종목: {', '.join(tickers)}")
                logger.warning("assets.tickers에 주식과 채권 종목을 모두 포함하세요 (예: ['TQQQ', 'BIL'])")
                continue
            
            # 전략에 종목 설정 (params에서 가져오거나 기본값 사용)
            if not strategy.stock_ticker or strategy.stock_ticker not in tickers:
                strategy.stock_ticker = tickers[0]
            if not strategy.bond_ticker or strategy.bond_ticker not in tickers:
                strategy.bond_ticker = tickers[1] if len(tickers) > 1 else tickers[0]
        
        # MovingAverageShannonHybrid 전략: 단일 종목 사용
        elif isinstance(strategy, MovingAverageShannonHybridStrategy):
            use_multi_asset = False
            if not strategy.stock_ticker or strategy.stock_ticker not in tickers:
                strategy.stock_ticker = tickers[0]
            if strategy.stock_ticker not in tickers:
                logger.warning(f"{strategy.name}: stock_ticker '{strategy.stock_ticker}'가 assets.tickers에 없습니다.")
                logger.warning(f"사용 가능한 종목: {', '.join(tickers)}")
                continue
        
        # SmartMovingAverageShannonHybrid 전략: 단일 종목 사용
        elif isinstance(strategy, SmartMAStrategy):
            use_multi_asset = False
            if not strategy.stock_ticker or strategy.stock_ticker not in tickers:
                strategy.stock_ticker = tickers[0]
            if strategy.stock_ticker not in tickers:
                logger.warning(f"{strategy.name}: stock_ticker '{strategy.stock_ticker}'가 assets.tickers에 없습니다.")
                logger.warning(f"사용 가능한 종목: {', '.join(tickers)}")
                continue
        
        # 백테스팅 엔진 생성
        if use_multi_asset:
            # 다중 종목 엔진 사용
            required_tickers = []
            
            # 전략별 required_tickers 설정
            if strategy.stock_ticker:
                required_tickers.append(strategy.stock_ticker)
            if strategy.bond_ticker:
                required_tickers.append(strategy.bond_ticker)
            
            # 요구되는 종목이 모두 data_dict에 있는지 확인
            if not all(t in data_dict for t in required_tickers):
                logger.error(f"필요한 종목 데이터가 없습니다: {required_tickers}")
                continue
            
            engine = MultiAssetBacktestEngine(
                tickers=required_tickers,
                initial_cash=config.backtest.initial_cash,
                commission_rate=config.backtest.commission_rate
            )
            engine.set_strategy(strategy)
            
            # 신호 생성
            signals_dict = {}
            
            # MovingAverage 전략은 주식 종목 데이터만 사용하여 신호 생성
            if isinstance(strategy, MovingAverageStrategy):
                stock_data = data_dict[strategy.stock_ticker]
                df_with_signals = strategy.generate_signals(stock_data)
                
                # 주식 종목에 신호 적용
                signals_dict[strategy.stock_ticker] = df_with_signals
                
                # 채권 종목은 신호 없이 빈 데이터프레임 (신호는 주식 기준으로 생성)
                bond_df = data_dict[strategy.bond_ticker].copy()
                bond_df["Signal"] = 0
                signals_dict[strategy.bond_ticker] = bond_df
            
            else:
                # Shannon 등 다른 전략: 각 종목별로 신호 생성
                for ticker in required_tickers:
                    df_with_signals = strategy.generate_signals(data_dict[ticker])
                    signals_dict[ticker] = df_with_signals
            
            engine.set_data(signals_dict)
            
            # 백테스팅 실행
            logger.info("백테스팅 실행 중...")
            try:
                results = engine.run(
                    start_date=config.backtest.start_date,
                    end_date=config.backtest.end_date
                )
                logger.info("백테스팅 완료")
            except Exception as e:
                logger.error(f"백테스팅 실패: {e}")
                import traceback
                traceback.print_exc()
                continue
        else:
            # 단일 종목 엔진 사용
            # BuyHold 전략: stock_ticker가 설정되어 있으면 해당 종목 사용
            if isinstance(strategy, BuyHoldStrategy) and strategy.stock_ticker:
                if strategy.stock_ticker not in tickers:
                    logger.warning(f"{strategy.name}: stock_ticker '{strategy.stock_ticker}'가 assets.tickers에 없습니다.")
                    logger.warning(f"사용 가능한 종목: {', '.join(tickers)}")
                    continue
                ticker = strategy.stock_ticker
            else:
                ticker = tickers[0]
            
            engine = SimpleBacktestEngine(
                ticker=ticker,
                initial_cash=config.backtest.initial_cash,
                commission_rate=config.backtest.commission_rate
            )
            engine.set_strategy(strategy)
            
            # 백테스팅 실행
            logger.info("백테스팅 실행 중...")
            try:
                results = engine.run(data_dict[ticker])
                logger.info("백테스팅 완료")
            except Exception as e:
                logger.error(f"백테스팅 실패: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # 결과 출력
        summary = engine.get_summary()
        
        logger.info("\n" + "-"*70)
        logger.info("결과 요약")
        logger.info("-"*70)
        
        for key, value in summary.items():
            logger.info(f"{key}: {value}")
        
        # 상세 분석
        portfolio = engine.portfolio
        
        logger.info("\n" + "-"*70)
        logger.info("상세 분석")
        logger.info("-"*70)
        
        logger.info(f"총 거래 횟수: {len(portfolio.trades)}")
        if portfolio.trades:
            first_trade = portfolio.trades[0]
            logger.info(f"첫 매수: {first_trade.date.strftime('%Y-%m-%d')} "
                       f"{first_trade.quantity}주 @ ${first_trade.price:.2f}")
            
            if len(portfolio.trades) > 1:
                last_trade = portfolio.trades[-1]
                logger.info(f"마지막 거래: {last_trade.date.strftime('%Y-%m-%d')} "
                           f"{last_trade.action} {last_trade.quantity}주 @ ${last_trade.price:.2f}")
        
        # 보유 종목
        holdings = engine.get_holdings()
        if not holdings.empty:
            logger.info("\n현재 보유 종목:")
            print("\n", holdings.to_string(index=False))
        
        # 수익률 계산
        final_price = results["total_value"].iloc[-1]
        initial_price = results["total_value"].iloc[0]
        total_return_pct = ((final_price / initial_price) - 1) * 100
        
        logger.info(f"\n초기 가치: ${initial_price:,.2f}")
        logger.info(f"최종 가치: ${final_price:,.2f}")
        logger.info(f"총 수익률: {total_return_pct:.2f}%")
        
        # 최고점/최저점
        max_value = results["total_value"].max()
        min_value = results["total_value"].min()
        max_date = results["total_value"].idxmax()
        min_date = results["total_value"].idxmin()
        
        logger.info(f"\n최고점: ${max_value:,.2f} ({max_date.strftime('%Y-%m-%d')})")
        logger.info(f"최저점: ${min_value:,.2f} ({min_date.strftime('%Y-%m-%d')})")
        
        # 최대 낙폭 (Max Drawdown)
        max_drawdown = 0
        peak = results["total_value"].iloc[0]
        
        for value in results["total_value"]:
            if value > peak:
                peak = value
            drawdown = ((value - peak) / peak) * 100
            if drawdown < max_drawdown:
                max_drawdown = drawdown
        
        logger.info(f"최대 낙폭: {max_drawdown:.2f}%")
        
        # 결과 저장 (비교용)
        strategy_results.append({
            "name": strategy_config.name,
            "final_value": final_price,
            "total_return": total_return_pct,
            "annualized_return": summary.get("Annualized Return", "N/A"),
            "total_trades": len(portfolio.trades),
            "max_drawdown": max_drawdown
        })
    
    # 여러 전략 비교 요약 (2개 이상 전략이 있을 때만)
    if len(strategy_results) > 1:
        logger.info("\n" + "="*70)
        logger.info("전략 비교 요약")
        logger.info("="*70)
        
        # 테이블 형식으로 출력
        logger.info(f"\n{'전략':<15} {'최종 자산':<15} {'총 수익률':<12} {'연환산':<12} {'거래 횟수':<10} {'최대 낙폭':<10}")
        logger.info("-" * 80)
        
        for result in strategy_results:
            annualized = result["annualized_return"]
            if isinstance(annualized, str) and annualized.endswith("%"):
                annualized_display = annualized.rstrip("%")
                annualized_num = float(annualized.rstrip("%"))
            else:
                annualized_display = str(annualized)
                annualized_num = float(annualized) if isinstance(annualized, (int, float)) else 0
            
            logger.info(
                f"{result['name']:<15} "
                f"${result['final_value']:>13,.2f} "
                f"{result['total_return']:>11.2f}% "
                f"{annualized_display:>11}% "
                f"{result['total_trades']:>9}회 "
                f"{result['max_drawdown']:>9.2f}%"
            )
        
        # 최고 성과 전략 표시
        def get_annualized_num(x):
            annualized = x["annualized_return"]
            if isinstance(annualized, str) and annualized.endswith("%"):
                return float(annualized.rstrip("%"))
            return float(annualized) if isinstance(annualized, (int, float)) else 0
        
        best_return = max(strategy_results, key=get_annualized_num)
        best_value = max(strategy_results, key=lambda x: x["final_value"])
        
        logger.info("\n" + "-" * 80)
        logger.info(f"최고 연환산 수익률: {best_return['name']} ({best_return['annualized_return']})")
        logger.info(f"최고 최종 자산: {best_value['name']} (${best_value['final_value']:,.2f})")
    
    logger.info("\n" + "="*70)
    logger.info("백테스팅 완료")
    logger.info("="*70)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="백테스팅 실행")
    parser.add_argument(
        "-c", "--config",
        default="config.yml",
        help="설정 파일 경로 (기본: config.yml)"
    )
    
    args = parser.parse_args()
    
    try:
        run_backtest(args.config)
    except KeyboardInterrupt:
        logger.info("\n\n작업이 취소되었습니다.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n오류 발생: {e}")
        sys.exit(1)

