"""这个文件负责计算机会分和三个子分。"""

from __future__ import annotations

import config


def calculate_velocity_score(recent_count: int, history_count: int) -> int:
    """近期频次相对历史越高，速度分越高。"""

    if recent_count <= 0:
        return 0
    if history_count <= 0:
        return clamp_score(recent_count * 30)
    growth_ratio = recent_count / history_count
    return clamp_score(round(growth_ratio * 25))


def calculate_search_gap_score(trends_interest: int | None) -> int:
    """Google Trends 热度越低，搜索空白分越高；查不到时给中性分。"""

    if trends_interest is None:
        return 50
    return clamp_score(100 - trends_interest)


def calculate_source_diversity_score(source_count: int) -> int:
    """三个数据源都出现时满分，一个来源出现时约 33 分。"""

    return clamp_score(round((source_count / 3) * 100))


def calculate_opportunity_score(velocity_score: int, search_gap_score: int, source_diversity_score: int) -> int:
    """按配置权重计算最终机会分。"""

    weighted_score = (
        config.WEIGHT_VELOCITY * velocity_score
        + config.WEIGHT_SEARCH_GAP * search_gap_score
        + config.WEIGHT_SOURCE_DIVERSITY * source_diversity_score
    )
    return clamp_score(round(weighted_score))


def build_trend_note(recent_count: int, history_count: int, trends_interest: int | None) -> str:
    """生成给页面展示的英文趋势说明。"""

    if trends_interest is None:
        search_part = "Google Trends data was unavailable in the latest run."
    elif trends_interest <= 20:
        search_part = "Google search interest is still low, so the content window looks open."
    elif trends_interest <= 50:
        search_part = "Google search interest is forming, but the topic is not saturated yet."
    else:
        search_part = "Google search interest is already visible, so move quickly."

    return (
        f"Recent mentions: {recent_count}; historical mentions: {history_count}. "
        f"{search_part}"
    )


def clamp_score(value: int | float) -> int:
    """保证分数永远在 0-100 之间。"""

    return max(0, min(100, int(round(value))))
