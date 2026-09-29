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


def review_course(cfg):
    kind=cfg.get('course_type','subject')
    issues=[]
    if kind not in ('subject','reading','ai_education'):
        issues.append('course_type必须为subject、reading或ai_education')
    selected=cfg.get('ai_case_ids',[])
    if kind=='ai_education':
        known={f'ai_{i:02}' for i in range(1,13)}
        if not isinstance(selected,list) or not selected or any(not isinstance(x,str) or x not in known for x in selected):
            issues.append('ai_case_ids须为ai_01至ai_12的非空列表')
    if cfg.get('classroom','no_students') not in ('live','no_students','有生','无生','有生课堂','无生课堂'):
        issues.append('classroom无效')
    enabled=cfg.get('ai_enabled',True)
    if type(enabled) is not bool:
        issues.append('ai_enabled须为JSON布尔值')
    elif not enabled and cfg.get('ai_style') not in (None,'','none'):
        issues.append('AI关闭与ai_style冲突')
    return {'course_type':kind,'course_ready':not issues,'issues':issues,
            'case_policy':{'subject':'subject_eight','reading':'reading_selected','ai_education':'ai_selected'}.get(kind,'invalid'),
            'ai_case_ids':selected if kind=='ai_education' else []}


def review_intake(cfg):
    issues = []
    if not isinstance(cfg, dict):
        return {'parameters_ready': False, 'timing_ready': False, 'intake_ready': False, 'course_ready': False, 'issues': ['输入必须是对象'], 'not_final_acceptance': True}
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
    course=review_course(cfg)
    return {'parameters_ready': parameters_ready, 'timing_ready': not issues,
            'course_review':course, 'course_ready':course['course_ready'],
            'intake_ready':not issues and course['course_ready'],
            'target_minutes': target, 'sum_minutes': total, 'issues': issues,
            'not_final_acceptance': True,
            'manual_required': ['核对学段和时长原始来源', '核对媒体、思考与转换无遗漏或重复计时', '实际试讲状态如实记录']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    result = review_intake(json.loads(Path(args.config).read_text(encoding='utf-8-sig')))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['intake_ready'] else 1)
