#!/usr/bin/env python3
"""
설정 파일 생성 도구
간단한 질문으로 설정 파일 생성
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import yaml
from datetime import datetime, timedelta


def generate_config():
    """대화형 설정 파일 생성"""
    print("="*70)
    print("백테스팅 설정 파일 생성 도구")
    print("="*70)
    print()
    
    config = {}
    
    # 백테스팅 기본 설정
    print("1. 백테스팅 기간 설정")
    print("-" * 70)
    
    print("시작일 (예: 2023-01-01, Enter 시 1년 전):")
    start_date = input("> ").strip()
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    print("종료일 (예: 2024-12-31, Enter 시 오늘):")
    end_date = input("> ").strip()
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    print("초기 자본금 (USD, 기본: 100000):")
    initial_cash = input("> ").strip()
    if not initial_cash:
        initial_cash = "100000"
    
    print("수수료율 (기본: 0.001 = 0.1%):")
    commission_rate = input("> ").strip()
    if not commission_rate:
        commission_rate = "0.001"
    
    config["backtest"] = {
        "start_date": start_date,
        "end_date": end_date,
        "initial_cash": float(initial_cash),
        "commission_rate": float(commission_rate)
    }
    
    # 포트폴리오 설정
    print("\n2. 전략 설정")
    print("-" * 70)
    print("사용할 전략을 선택하세요 (쉼표로 구분):")
    print("1) shannon - 섀넌 전략")
    print("2) ma_crossover - 이동평균선 교차 전략")
    print("3) rebalancing - 리밸런싱 전략")
    
    selected = input("> ").strip().split(",")
    
    strategies = []
    for choice in selected:
        choice = choice.strip()
        strategy = {}
        
        if choice in ["1", "shannon"]:
            strategy = {
                "name": "shannon",
                "enabled": True,
                "params": {
                    "rebalance_freq": 30
                }
            }
        elif choice in ["2", "ma_crossover"]:
            strategy = {
                "name": "ma_crossover",
                "enabled": True,
                "params": {
                    "fast_period": 20,
                    "slow_period": 50
                }
            }
        elif choice in ["3", "rebalancing"]:
            strategy = {
                "name": "rebalancing",
                "enabled": True,
                "params": {
                    "target_weights": [
                        {"ticker": "AAPL", "weight": 0.4},
                        {"ticker": "GOOGL", "weight": 0.3},
                        {"ticker": "MSFT", "weight": 0.3}
                    ],
                    "rebalance_freq": 90
                }
            }
        
        if strategy:
            strategies.append(strategy)
    
    config["portfolio"] = {"strategies": strategies}
    
    # 종목 설정
    print("\n3. 거래 종목 설정")
    print("-" * 70)
    print("거래할 종목 티커를 입력하세요 (쉼표로 구분, 예: AAPL,GOOGL,MSFT):")
    print("기본값: AAPL,GOOGL,MSFT,TSLA,NVDA")
    
    tickers_input = input("> ").strip()
    if not tickers_input:
        tickers = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]
    else:
        tickers = [t.strip().upper() for t in tickers_input.split(",")]
    
    config["assets"] = {
        "tickers": tickers,
        "auto_select": False
    }
    
    # 리스크 설정
    print("\n4. 리스크 관리 설정")
    print("-" * 70)
    print("최대 보유 종목 수 (기본: 10):")
    max_positions = input("> ").strip()
    if not max_positions:
        max_positions = "10"
    
    print("손절 사용 여부 (y/n, 기본: y):")
    stop_loss = input("> ").strip().lower()
    stop_loss_enabled = stop_loss != "n"
    
    config["risk"] = {
        "max_positions": int(max_positions),
        "max_position_weight": 0.25,
        "stop_loss": {
            "enabled": stop_loss_enabled,
            "threshold": -0.10
        },
        "take_profit": {
            "enabled": False,
            "threshold": 0.20
        }
    }
    
    # 리포트 설정
    config["report"] = {
        "save_results": True,
        "generate_charts": True,
        "verbose": False
    }
    
    # 파일 저장
    print("\n5. 설정 저장")
    print("-" * 70)
    print("저장할 파일명 (기본: config.yml):")
    filename = input("> ").strip()
    if not filename:
        filename = "config.yml"
    
    if not filename.endswith(".yml"):
        filename += ".yml"
    
    output_path = project_root / filename
    
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)
    
    print(f"\n{'='*70}")
    print(f"✅ 설정 파일이 생성되었습니다: {output_path}")
    print(f"{'='*70}\n")
    
    # 설정 미리보기
    print("생성된 설정 미리보기:")
    print("-" * 70)
    with open(output_path, "r", encoding="utf-8") as f:
        print(f.read())


if __name__ == "__main__":
    try:
        generate_config()
    except KeyboardInterrupt:
        print("\n\n작업이 취소되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n오류 발생: {e}")
        sys.exit(1)

