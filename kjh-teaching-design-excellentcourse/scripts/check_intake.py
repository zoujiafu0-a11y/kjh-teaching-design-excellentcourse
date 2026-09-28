"""Validate recorded timing, not source authenticity or actual teaching performance."""
import argparse
import json
import math
import re
from pathlib import Path

STAGES = {'小学', '初中', '高中', '中学', 'primary', 'lower_secondary', 'upper_secondary', 'secondary'}
PLACEHOLDER = re.compile(r'(?i)x{2,}|待定|待补|未知|中学\s*[/／]\s*小学|小学\s*[/／]\s*中学')


def meaningful(value):
    return isinstance(value, str) and bool(value.strip()) and not PLACEHOLDER.search(value)


def number(value, zero=False):
    return type(value) in (int, float) and math.isfinite(value) and (value >= 0 if zero else value > 0)


def review_intake(cfg):
    issues = []
    if not isinstance(cfg, dict):
        return {'parameters_ready': False, 'timing_ready': False, 'issues': ['输入必须是对象'], 'not_final_acceptance': True}
    if not isinstance(cfg.get('school_stage'), str) or cfg.get('school_stage') not in STAGES:
        issues.append('缺少明确学段或仍为占位符')
    if not meaningful(cfg.get('school_stage_source')):
        issues.append('缺少学段依据')
    if not meaningful(cfg.get('duration_purpose')):
        issues.append('缺少时长用途：普通课堂、比赛展示或其他明确用途')
    requirement = cfg.get('duration_requirement')
    requirement = requirement if isinstance(requirement, dict) else {}
    low, high = requirement.get('min_minutes'), requirement.get('max_minutes')
    bounds_ok = number(low, zero=True) and number(high) and low <= high
    if not bounds_ok:
        issues.append('时长范围缺失或无效')
    if not meaningful(requirement.get('source')):
        issues.append('缺少通知或用户给定时长的来源')
    target = cfg.get('target_minutes')
    if not number(target):
        issues.append('缺少大于0的具体目标分钟数')
    elif bounds_ok and not low <= target <= high:
        issues.append('具体目标时长超出通知或用户允许范围')
    parameters_ready = not issues
    plan = cfg.get('timing_plan')
    total = None
    if not isinstance(plan, list) or not plan:
        issues.append('缺少环节时间分配')
    elif any(not isinstance(row, dict) or not meaningful(row.get('name')) or not number(row.get('minutes')) for row in plan):
        issues.append('环节名称或分钟数无效')
    else:
        total = sum(row['minutes'] for row in plan)
        if not number(target) or not math.isclose(total, target, rel_tol=0, abs_tol=1e-6):
            issues.append('环节时间合计不等于具体目标时长')
    return {'parameters_ready': parameters_ready, 'timing_ready': not issues,
            'target_minutes': target, 'sum_minutes': total, 'issues': issues,
            'not_final_acceptance': True,
            'manual_required': ['核对学段和时长原始来源', '核对媒体、思考与转换无遗漏或重复计时', '实际试讲状态如实记录']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    result = review_intake(json.loads(Path(args.config).read_text(encoding='utf-8-sig')))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['timing_ready'] else 1)
