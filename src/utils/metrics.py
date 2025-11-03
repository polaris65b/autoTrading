"""
성과 지표 계산 유틸리티
Sharpe Ratio, Sortino Ratio, Calmar Ratio 등 리스크 보정 수익률 계산
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252
) -> float:
    """
    Sharpe Ratio 계산
    
    Sharpe Ratio = (평균 수익률 - 무위험 수익률) / 수익률 표준편차
    
    Args:
        returns: 일일 수익률 시리즈
        risk_free_rate: 연무위험 수익률 (기본: 0%)
        periods_per_year: 1년당 거래일 수 (기본: 252일)
    
    Returns:
        Sharpe Ratio
    """
    if len(returns) < 2:
        return 0.0
    
    # 일일 무위험 수익률
    daily_rf = risk_free_rate / periods_per_year
    
    # 연환산 수익률
    mean_return = returns.mean() * periods_per_year
    
    # 연환산 표준편차
    std_return = returns.std() * np.sqrt(periods_per_year)
    
    if std_return == 0:
        return 0.0
    
    return (mean_return - risk_free_rate) / std_return


def calculate_sortino_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252
) -> float:
    """
    Sortino Ratio 계산
    
    Sortino Ratio = (평균 수익률 - 무위험 수익률) / 하락 위험 표준편차
    
    Args:
        returns: 일일 수익률 시리즈
        risk_free_rate: 연무위험 수익률 (기본: 0%)
        periods_per_year: 1년당 거래일 수 (기본: 252일)
    
    Returns:
        Sortino Ratio
    """
    if len(returns) < 2:
        return 0.0
    
    # 일일 무위험 수익률
    daily_rf = risk_free_rate / periods_per_year
    
    # 하락 수익률만 추출
    downside_returns = returns[returns < 0]
    
    if len(downside_returns) == 0:
        # 하락이 전혀 없는 경우 (이론적으로는 무한대)
        return float('inf') if returns.mean() > 0 else 0.0
    
    # 연환산 수익률
    mean_return = returns.mean() * periods_per_year
    
    # 하락 위험 표준편차 (연환산)
    downside_std = downside_returns.std() * np.sqrt(periods_per_year)
    
    if downside_std == 0:
        return 0.0
    
    return (mean_return - risk_free_rate) / downside_std


def calculate_calmar_ratio(
    annualized_return: float,
    max_drawdown: float
) -> float:
    """
    Calmar Ratio 계산
    
    Calmar Ratio = 연환산 수익률 / |최대 낙폭|
    
    Args:
        annualized_return: 연환산 수익률 (%)
        max_drawdown: 최대 낙폭 (%)
    
    Returns:
        Calmar Ratio
    """
    if max_drawdown == 0:
        return 0.0
    
    return annualized_return / abs(max_drawdown)


def calculate_max_drawdown(values: pd.Series) -> Dict[str, float]:
    """
    최대 낙폭 계산 (상세 정보 포함)
    
    Args:
        values: 자산 가치 시리즈
    
    Returns:
        딕셔너리:
            - mdd: 최대 낙폭 (%)
            - mdd_start: 최대 낙폭 시작 날짜
            - mdd_end: 최대 낙폭 종료 날짜
            - peak_value: 최고점 가치
            - trough_value: 최저점 가치
            - recovery_date: 회복 날짜 (없으면 None)
    """
    if len(values) < 2:
        return {
            "mdd": 0.0,
            "mdd_start": None,
            "mdd_end": None,
            "peak_value": values.iloc[0] if len(values) > 0 else 0.0,
            "trough_value": values.iloc[0] if len(values) > 0 else 0.0,
            "recovery_date": None
        }
    
    # 누적 최대값 (지금까지의 최고점)
    cumulative_max = values.expanding().max()
    
    # 낙폭 계산
    drawdown = ((values - cumulative_max) / cumulative_max) * 100
    
    # 최대 낙폭
    max_dd_idx = drawdown.idxmin()
    mdd = drawdown.min()
    
    # 최고점 찾기 (낙폭이 시작되기 전 최고점)
    # max_dd_idx 이전까지의 최고점
    max_dd_position = list(drawdown.index).index(max_dd_idx)
    peak_idx = cumulative_max.iloc[:max_dd_position + 1].idxmax()
    peak_value = values.loc[peak_idx]
    trough_value = values.loc[max_dd_idx]
    
    # 회복 날짜 찾기 (최고점을 다시 돌파한 날짜)
    recovery_date = None
    max_dd_position_in_full = list(values.index).index(max_dd_idx)
    if max_dd_position_in_full < len(values) - 1:
        # 낙폭 이후 데이터에서 회복 여부 확인
        future_values = values.loc[max_dd_idx:]
        recovery_mask = future_values >= peak_value
        
        if recovery_mask.any():
            recovery_date = future_values[recovery_mask].index[0]
    
    return {
        "mdd": mdd,
        "mdd_start": peak_idx,
        "mdd_end": max_dd_idx,
        "peak_value": peak_value,
        "trough_value": trough_value,
        "recovery_date": recovery_date
    }


def calculate_recovery_days(values: pd.Series) -> Optional[int]:
    """
    최대 낙폭 회복까지 걸린 일수 계산
    
    Args:
        values: 자산 가치 시리즈
    
    Returns:
        회복 일수 (회복되지 않았으면 None)
    """
    mdd_info = calculate_max_drawdown(values)
    
    if mdd_info["recovery_date"] is None or mdd_info["mdd_end"] is None:
        return None
    
    return (mdd_info["recovery_date"] - mdd_info["mdd_end"]).days


def calculate_all_metrics(
    equity_curve: pd.DataFrame,
    initial_cash: float,
    risk_free_rate: float = 0.0
) -> Dict[str, float]:
    """
    모든 성과 지표 계산
    
    Args:
        equity_curve: equity curve 데이터프레임 (date 인덱스, total_value 컬럼)
        initial_cash: 초기 자본금
        risk_free_rate: 연무위험 수익률 (기본: 0%)
    
    Returns:
        모든 성과 지표 딕셔너리
    """
    if equity_curve.empty or "total_value" not in equity_curve.columns:
        return {}
    
    values = equity_curve["total_value"]
    
    # 일일 수익률 계산
    returns = values.pct_change().dropna()
    
    # 기본 지표
    total_return = ((values.iloc[-1] / initial_cash) - 1) * 100
    
    days = len(values)
    years = days / 365.25
    annualized_return = ((values.iloc[-1] / initial_cash) ** (1 / years) - 1) * 100 if years > 0 else 0
    
    # MDD 정보
    mdd_info = calculate_max_drawdown(values)
    
    # 리스크 보정 지표
    sharpe = calculate_sharpe_ratio(returns, risk_free_rate)
    sortino = calculate_sortino_ratio(returns, risk_free_rate)
    calmar = calculate_calmar_ratio(annualized_return, mdd_info["mdd"])
    
    # 추가 지표
    recovery_days = calculate_recovery_days(values)
    
    # 승률 계산
    winning_trades_pct = 0.0  # TODO: 거래 내역이 필요한 지표
    
    # 변동성 (연환산)
    volatility = returns.std() * np.sqrt(252) * 100
    
    return {
        "total_return": total_return,
        "annualized_return": annualized_return,
        "max_drawdown": mdd_info["mdd"],
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "calmar_ratio": calmar,
        "volatility": volatility,
        "recovery_days": recovery_days,
        "winning_trades_pct": winning_trades_pct
    }

