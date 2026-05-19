from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from copy import copy
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

from retrieve_cases import (
    ALIASES,
    DATA_ROOT,
    RELATED_MODULES,
    Match,
    collect_matches,
    row_text,
    tokenize,
)


SKILL_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SKILL_DIR.parent
PACKAGED_TEMPLATE_PATH = SKILL_DIR / "template.xlsx"
REPO_TEMPLATE_PATH = PROJECT_ROOT / "template.xlsx"
DEFAULT_TEMPLATE_PATH = PACKAGED_TEMPLATE_PATH if PACKAGED_TEMPLATE_PATH.exists() else REPO_TEMPLATE_PATH
ALLOWED_THEMES = {"dfmea_sample_data", "knowledge_base_template"}

FIELD_ALIASES = {
    "analysis_object": ["模块/零件", "零件名称", "子系统/功能模块", "子系统/组件", "子系统/部件", "模块", "关联项目/产品"],
    "function": [
        "功能及要求",
        "功能要求",
        "功能描述",
        "标准化功能项",
        "产品寿命周期应用任务和环境剖面",
        "策划和控制内容",
    ],
    "parameter_indicators": ["参数指标性能", "参数指标", "性能指标"],
    "failure_mode": ["潜在失效模式", "失效模式 (AI分类)"],
    "effect": [
        "失效影响（后果）",
        "潜在失效后果 (客户/后工序)",
        "潜在失效后果（客户/后工序）",
        "失效的潜在后果（对客户或后工序的影响）",
        "失效后果 (S)",
    ],
    "severity": ["严重度\nS", "严重度 S", "严重度 (S)", "S"],
    "cause": ["潜在失效起因/机理", "潜在失效原因（机理）", "潜在失效原因", "根本原因分析 (Cause)"],
    "occurrence": ["频度\nO", "频度 O", "发生频次 (O)", "O"],
    "current_controls": [
        "现行设计控制 (预防/探测)",
        "现行控制措施",
        "现行控制方法",
        "现行设计/过程控制措施",
        "现行控制措施",
        "现行预防措施",
        "现行探测控制",
    ],
    "detection": ["探测度\nD", "探测度 D", "可探测度 (D)", "D"],
    "rpn": ["RPN", "初始 RPN"],
    "recommended_actions": [
        "建议改进措施 (控制/预防)",
        "建议的控制措施 (改进方案)",
        "建议措施",
        "建议的预防/探测措施",
    ],
    "rating_basis": ["AI打分推导依据", "评分依据", "打分依据"],
    "post_action_severity": ["改进后S", "措施后 S", "改进后 S", "新S"],
    "post_action_occurrence": ["改进后O", "措施后 O", "改进后 O", "新O"],
    "post_action_detection": ["改进后D", "措施后 D", "改进后 D", "新D"],
    "post_action_rpn": ["改进后RPN", "措施后 RPN", "改进后 RPN", "新RPN"],
    "owner": ["措施负责人", "责任人", "负责人"],
    "target_date": ["完成时间", "计划完成时间", "结束时间"],
}

STOPWORDS = {
    "客户",
    "后工序",
    "系统",
    "功能",
    "要求",
    "建议",
    "设计",
    "控制",
    "改进",
    "方案",
    "模块",
    "项目",
    "产品",
    "组件",
    "部分",
    "过程",
    "进行",
    "用于",
    "增加",
    "导致",
    "无法",
    "工作",
    "模式",
    "分析",
    "输出",
    "表格",
}

SCOPE_PROFILES: dict[str, list[dict[str, Any]]] = {
    "变温系统": [
        {
            "name": "压缩机制冷子系统",
            "keywords": ["压缩机", "冷媒", "气液分离器", "蒸发器", "毛细管", "高压", "继电器", "422", "VX3244", "1028", "启动", "时序"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "液氮蒸发子系统",
            "keywords": ["液氮罐", "主体组件", "排气管组件", "波纹管", "真空", "PTFE", "特氟龙", "换热盘管", "加热棒", "PT100", "航插", "麦拉膜", "G10"],
            "min_hits": 2,
            "max_terms": 10,
        },
    ],
    "自动进样器": [
        {
            "name": "运动与抓取子系统",
            "keywords": ["气缸", "滑块", "夹爪", "储样筒", "进样筒", "转盘", "样品管", "扭簧", "导轨", "定位销"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "检测与气路控制子系统",
            "keywords": ["检测", "光电", "传感器", "对射", "气路", "电磁阀", "减压阀", "缓冲气", "压力开关", "气压", "供电", "接口"],
            "min_hits": 2,
            "max_terms": 10,
        },
    ],
    "调谐单元": [
        {
            "name": "射频调谐与匹配子系统",
            "keywords": ["射频", "调谐", "匹配", "电容", "打火", "线圈", "焊接", "磁化率", "梯度线圈"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "机械传动与限位子系统",
            "keywords": ["电机", "编码器", "限位", "离合器", "连杆", "齿轮", "减速机", "扭矩"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "EMC与算法控制子系统",
            "keywords": ["EMC", "CAN", "RS422", "MCU", "光耦", "搜索", "陷波", "扫掠", "算法"],
            "min_hits": 2,
            "max_terms": 10,
        },
    ],
    "收发机": [
        {
            "name": "发射链路子系统",
            "keywords": ["发射", "上变频", "调幅", "功放驱动", "衰减", "功率", "泄漏"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "接收与采集子系统",
            "keywords": ["接收", "LNA", "ADC", "时钟", "噪声", "解调", "增益"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "频率合成与连接子系统",
            "keywords": ["混频", "本振", "频率合成", "背板", "连接器", "同轴", "杂散"],
            "min_hits": 2,
            "max_terms": 10,
        },
    ],
    "前置放大器": [
        {
            "name": "T/R与保护子系统",
            "keywords": ["T/R", "PIN", "高功率", "保护", "限幅", "功率检测", "联动跳闸", "VSWR", "驻波", "复位", "热管理"],
            "min_hits": 2,
            "max_terms": 12,
        },
        {
            "name": "低噪声放大与接口子系统",
            "keywords": ["LNA", "增益", "振荡", "N-K", "BNC", "接口", "回波损耗"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "控制逻辑与供电子系统",
            "keywords": ["UNWORK", "OBSERVE", "Watchdog", "DB-37", "供电", "串扰", "模式切换"],
            "min_hits": 2,
            "max_terms": 10,
        },
    ],
    "射频功放": [
        {
            "name": "异常保护与联锁子系统",
            "keywords": ["保护", "联锁", "比较器", "切断", "驻波", "反射功率", "异常检测"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "放大与通道切换子系统",
            "keywords": ["放大", "增益", "双通道", "切换", "热切换", "继电器", "功率管"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "热管理与复位子系统",
            "keywords": ["热管理", "温度", "风扇", "热斑", "复位", "Auto-Recovery", "散热"],
            "min_hits": 2,
            "max_terms": 10,
        },
    ],
    "进样筒": [
        {
            "name": "结构与磁兼容子系统",
            "keywords": ["磁性", "无磁", "结构件", "清洗", "磁导率", "铁屑"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "气动与升降子系统",
            "keywords": ["气动", "气源", "缓冲气罐", "软着陆", "升降", "卡阻", "内壁"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "旋转与控制子系统",
            "keywords": ["转子", "旋转", "50Hz", "PID", "光电传感器", "气流阀门"],
            "min_hits": 2,
            "max_terms": 10,
        },
    ],
    "匀场单元": [
        {
            "name": "匀场线圈结构子系统",
            "keywords": ["匀场线圈", "几何形状", "固化", "环氧", "真空灌封", "节点松动"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "恒流驱动与连接子系统",
            "keywords": ["SDB", "恒流", "DAC", "基准电压", "DB50", "连接", "检流电阻"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "软件与耦合管理子系统",
            "keywords": ["算法", "通信", "EEPROM", "Watchdog", "互感", "低温匀场", "室温匀场"],
            "min_hits": 2,
            "max_terms": 10,
        },
    ],
    "电子学机柜": [
        {
            "name": "电源与接地屏蔽子系统",
            "keywords": ["PDU", "电源", "接地", "屏蔽", "导电", "EMC", "胶条"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "结构与门板安全子系统",
            "keywords": ["横梁", "机柜", "前门", "后下门", "后上门", "钢丝绳", "铰链"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "风道与热设计子系统",
            "keywords": ["风道", "过滤棉", "进风", "排风", "热短路", "CFD", "温升"],
            "min_hits": 2,
            "max_terms": 10,
        },
    ],
}

LIFECYCLE_COVERAGE_PROFILES: list[dict[str, Any]] = [
    {
        "name": "产品类别设计",
        "keywords": ["架构", "设计", "指标", "裕量", "保护", "安全", "功能", "接口", "验证", "竞品"],
        "function_context": "产品设计阶段确保：{function}",
        "effect_context": "设计缺陷会固化到整机基线，造成批量性能、安全或可靠性风险。关联后果：{effect}",
        "cause_context": "需求分解、设计裕量、接口约束或验证覆盖不足。关联机理：{cause}",
        "control_context": "需求评审、架构评审、仿真/样机验证、设计规则检查。现行控制：{controls}",
        "action_context": "补充设计裕量、边界条件验证、保护阈值和评审检查表。建议延伸：{actions}",
    },
    {
        "name": "物流运输",
        "keywords": ["运输", "包装", "振动", "冲击", "跌落", "湿热", "静电", "搬运", "锁止", "到货"],
        "function_context": "物流运输后仍满足：{function}",
        "effect_context": "运输/搬运后隐性损伤会导致到货验收、安装或首次运行失败。关联后果：{effect}",
        "cause_context": "长途振动、冲击、潮湿、ESD、包装固定或运输锁止不足。关联机理：{cause}",
        "control_context": "包装评审、运输试验、冲击/温湿度记录、到货外观与功能检查。现行控制：{controls}",
        "action_context": "增加专用包装、关键器件锁止、运输记录标签、到货复测项目。建议延伸：{actions}",
    },
    {
        "name": "安装调试",
        "keywords": ["安装", "调试", "接线", "校准", "接地", "联调", "验收", "配置", "SOP", "现场"],
        "function_context": "安装调试阶段正确建立：{function}",
        "effect_context": "安装配置偏差会在客户现场暴露为验收失败、性能不稳或安全保护误动作。关联后果：{effect}",
        "cause_context": "接线/接地/配置/校准步骤遗漏，现场条件与工厂验证边界不一致。关联机理：{cause}",
        "control_context": "安装SOP、联调清单、接地/接口核验、出厂参数备份、现场验收测试。现行控制：{controls}",
        "action_context": "增加安装防错、参数模板、自动自检、强制验收记录和现场问题回写。建议延伸：{actions}",
    },
    {
        "name": "客户操作",
        "keywords": ["客户", "操作", "误操作", "权限", "参数", "报警", "提示", "互锁", "培训", "使用"],
        "function_context": "客户日常操作中安全、稳定地完成：{function}",
        "effect_context": "误操作或参数误设会导致实验中断、器件损伤、结果失真或客户投诉。关联后果：{effect}",
        "cause_context": "用户经验差异、参数边界提示不足、权限/互锁不完整或报警解释不清。关联机理：{cause}",
        "control_context": "操作权限、参数范围限制、报警提示、日志追踪、培训材料。现行控制：{controls}",
        "action_context": "增加新手模式、关键操作二次确认、参数推荐、报警指导和操作日志复盘。建议延伸：{actions}",
    },
    {
        "name": "任务执行",
        "keywords": ["任务", "运行", "长时间", "脉冲", "稳定", "精度", "漂移", "动态", "输出", "性能"],
        "function_context": "任务执行期间持续满足：{function}",
        "effect_context": "任务过程中失效会直接影响实验数据、连续运行和核心性能。关联后果：{effect}",
        "cause_context": "长时间运行、动态负载、热漂移、控制滞后或边界工况覆盖不足。关联机理：{cause}",
        "control_context": "在线监测、性能自检、趋势记录、任务前后校验、保护联锁。现行控制：{controls}",
        "action_context": "增加在线诊断、趋势预警、任务前自检、降额策略和异常自动记录。建议延伸：{actions}",
    },
    {
        "name": "环境应力",
        "keywords": ["环境", "温度", "湿度", "EMC", "电磁", "电源", "振动", "粉尘", "冷凝", "散热"],
        "function_context": "环境应力变化下维持：{function}",
        "effect_context": "温湿度、电磁、电源或振动应力会造成间歇性故障、误报警或性能漂移。关联后果：{effect}",
        "cause_context": "客户现场环境超出假设、热/湿/电磁裕量不足或环境监测缺失。关联机理：{cause}",
        "control_context": "环境规范、温湿度/电源/EMC监测、降额设计、环境适应性验证。现行控制：{controls}",
        "action_context": "增加环境传感、EMC/电源裕量、热设计复核、环境超限联锁和客户环境预检。建议延伸：{actions}",
    },
    {
        "name": "维护保养",
        "keywords": ["维护", "保养", "校准", "寿命", "老化", "更换", "备件", "清洁", "诊断", "复位"],
        "function_context": "维护保养后恢复并保持：{function}",
        "effect_context": "维护不到位或寿命件退化会导致重复停机、性能慢性劣化和服务成本上升。关联后果：{effect}",
        "cause_context": "寿命件老化、校准漂移、维护周期不清、备件/清洁/复位策略不足。关联机理：{cause}",
        "control_context": "维护计划、寿命计数、校准记录、备件清单、远程诊断。现行控制：{controls}",
        "action_context": "增加寿命预测、维护提醒、快换设计、远程诊断和保养记录闭环。建议延伸：{actions}",
    },
]


@dataclass
class ScopeDefinition:
    name: str
    query_terms: list[str]
    extracted_terms: list[str] = field(default_factory=list)
    auto_suggested: bool = False
    hit_count: int = 0
    reason: str = ""


@dataclass
class DraftRow:
    scope: str
    analysis_object: str
    function: str
    failure_mode: str
    effect: str
    severity: str
    cause: str
    occurrence: str
    current_controls: str
    detection: str
    rpn: str
    recommended_actions: str
    owner: str
    target_date: str
    confirmation_status: str
    rating_basis: str
    reference_type: str
    source_cases: list[str]
    review_comment: str = ""
    post_action_severity: str = ""
    post_action_occurrence: str = ""
    post_action_detection: str = ""
    post_action_rpn: str = ""
    max_match_score: int = 0
    max_scope_hits: int = 0
    confirmation_reasons: list[str] = field(default_factory=list)
    reviewer_focus: str = ""
    boundary_scopes: list[str] = field(default_factory=list)


@dataclass
class ConfirmationItem:
    scope: str
    row_key: str
    why_confirmation_is_needed: str
    suggested_reviewer_focus: str
    reference_type: str
    source_cases: list[str]
    review_comment: str = ""


def load_input_text(args: argparse.Namespace) -> str:
    if args.input_file:
        return Path(args.input_file).read_text(encoding="utf-8").strip()
    if args.input_text:
        return args.input_text.strip()
    raise ValueError("Provide either --input-file or --input-text.")


def valid_token(token: str) -> bool:
    token = token.strip()
    if not token or token in STOPWORDS:
        return False
    if len(token) < 2 or len(token) > 24:
        return False
    if re.fullmatch(r"[\d\-.:%]+", token):
        return False
    if token.lower() in {"rpn", "excel", "json", "csv"}:
        return False
    return True


def build_lexicon() -> list[str]:
    counts: Counter[str] = Counter()
    for json_file in sorted(DATA_ROOT.glob("*/json/*.json")):
        payload = json.loads(json_file.read_text(encoding="utf-8"))
        if payload.get("theme") not in ALLOWED_THEMES:
            continue
        for row in payload.get("filled_rows", []):
            text = row_text(row)
            if not text:
                continue
            for token in tokenize(text):
                if valid_token(token):
                    counts[token] += 1
    ranked = sorted(counts.items(), key=lambda item: (-len(item[0]), -item[1], item[0]))
    return [token for token, _ in ranked]


def extract_query_terms(input_text: str, module: str | None, limit: int = 16) -> list[str]:
    lexicon = build_lexicon()
    found: list[str] = []
    for token in lexicon:
        if token in input_text and token not in found:
            found.append(token)
        if len(found) >= limit:
            break
    if module:
        if module not in found:
            found.insert(0, module)
        for canonical, alias_list in ALIASES.items():
            if module == canonical or module in alias_list:
                for item in [canonical, *alias_list]:
                    if item not in found:
                        found.append(item)
    return found


def parse_scope(raw_scope: str) -> ScopeDefinition:
    if "::" not in raw_scope:
        raise ValueError(f"Invalid --scope value: {raw_scope}. Use 'Scope Name::keyword1 keyword2'.")
    name, raw_terms = raw_scope.split("::", 1)
    terms = [term for term in tokenize(raw_terms) if valid_token(term)]
    if not name.strip() or not terms:
        raise ValueError(f"Invalid --scope value: {raw_scope}.")
    return ScopeDefinition(name=name.strip(), query_terms=terms, auto_suggested=False, reason="manual")


def canonicalize_module(module: str) -> str:
    if module in SCOPE_PROFILES:
        return module
    for canonical, aliases in ALIASES.items():
        if module == canonical or module in aliases:
            return canonical
    return module


def module_family_rank(sheet: str, module: str | None) -> int:
    canonical_module = canonicalize_module(module) if module else None
    if not canonical_module:
        return 0

    same_names = {canonical_module, *ALIASES.get(canonical_module, [])}
    if sheet in same_names:
        return 2

    related_modules = RELATED_MODULES.get(canonical_module, [])
    related_names = {name for related in related_modules for name in [related, *ALIASES.get(related, [])]}
    if sheet in related_names:
        return 1

    return 0


def suggest_scopes(module: str, input_text: str, extracted_terms: list[str]) -> list[ScopeDefinition]:
    canonical_module = canonicalize_module(module)
    profiles = SCOPE_PROFILES.get(canonical_module, [])
    lowered = input_text.lower()
    suggestions: list[ScopeDefinition] = []

    for profile in profiles:
        keywords = profile["keywords"]
        hit_keywords = [keyword for keyword in keywords if keyword.lower() in lowered]
        if len(hit_keywords) < profile["min_hits"]:
            continue

        query_terms: list[str] = []
        for keyword in hit_keywords:
            if keyword not in query_terms:
                query_terms.append(keyword)
        for term in extracted_terms:
            if term in keywords and term not in query_terms:
                query_terms.append(term)
        for keyword in keywords:
            if keyword not in query_terms:
                query_terms.append(keyword)
            if len(query_terms) >= profile["max_terms"]:
                break

        suggestions.append(
            ScopeDefinition(
                name=profile["name"],
                query_terms=query_terms[: profile["max_terms"]],
                extracted_terms=[term for term in extracted_terms if term in query_terms],
                auto_suggested=True,
                hit_count=len(hit_keywords),
                reason=f"matched keywords: {' / '.join(hit_keywords[:8])}",
            )
        )

    suggestions.sort(key=lambda scope: (-scope.hit_count, scope.name))
    return suggestions


def suggest_lifecycle_scopes(module: str, input_text: str, extracted_terms: list[str]) -> list[ScopeDefinition]:
    lowered = input_text.lower()
    scopes: list[ScopeDefinition] = []
    for profile in LIFECYCLE_COVERAGE_PROFILES:
        keywords = profile["keywords"]
        hit_keywords = [keyword for keyword in keywords if keyword.lower() in lowered]
        query_terms: list[str] = []
        for term in [module, *hit_keywords, *extracted_terms[:10], *keywords]:
            if term and term not in query_terms:
                query_terms.append(term)
        scopes.append(
            ScopeDefinition(
                name=profile["name"],
                query_terms=query_terms[:18],
                extracted_terms=[term for term in extracted_terms if term in query_terms],
                auto_suggested=True,
                hit_count=len(hit_keywords),
                reason=(
                    f"lifecycle coverage profile; matched keywords: {' / '.join(hit_keywords[:8])}"
                    if hit_keywords
                    else "lifecycle coverage profile; added to avoid narrow subsystem-only FMEA coverage"
                ),
            )
        )
    return scopes


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def read_match_row(match: Match, cache: dict[Path, Any]) -> dict[str, str]:
    json_path = PROJECT_ROOT / match.source
    if json_path not in cache:
        cache[json_path] = json.loads(json_path.read_text(encoding="utf-8"))
    payload = cache[json_path]
    for row in payload.get("filled_rows", []):
        if row.get("__excel_row__") == match.excel_row:
            return row
    raise KeyError(f"Could not find row {match.excel_row} in {json_path}")


def first_value(row: dict[str, str], field_name: str) -> str:
    for key in FIELD_ALIASES[field_name]:
        value = normalize_space(row.get(key, ""))
        if value:
            return value
    return ""


def safe_int(value: str) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def compute_rpn(severity: str, occurrence: str, detection: str, current_rpn: str) -> str:
    if current_rpn:
        return current_rpn
    s_value = safe_int(severity)
    o_value = safe_int(occurrence)
    d_value = safe_int(detection)
    if s_value is None or o_value is None or d_value is None:
        return ""
    return str(s_value * o_value * d_value)


def compute_post_action_rpn(severity: str, occurrence: str, detection: str, current_rpn: str) -> str:
    return compute_rpn(severity, occurrence, detection, current_rpn)


def fill_missing_draft_scores(
    severity: str,
    occurrence: str,
    detection: str,
    rpn: str = "",
) -> tuple[str, str, str, str, list[str]]:
    """Fill missing S/O/D with conservative AI draft values so rows remain reviewable.

    Missing source scores are still routed to the confirmation queue by callers.
    These defaults are not enterprise facts; they are placeholders that make RPN
    sorting and workbook formulas usable before expert calibration.
    """

    missing = [label for label, value in [("S", severity), ("O", occurrence), ("D", detection)] if not value]
    severity = severity or "7"
    occurrence = occurrence or "5"
    detection = detection or "5"
    rpn = compute_rpn(severity, occurrence, detection, rpn)
    return severity, occurrence, detection, rpn, missing


def combine_unique(values: list[str]) -> str:
    seen: list[str] = []
    for value in values:
        cleaned = normalize_space(value)
        if cleaned and cleaned not in seen:
            seen.append(cleaned)
    return "\n".join(seen)


def dedupe_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        first_value(row, "analysis_object"),
        first_value(row, "function"),
        first_value(row, "failure_mode"),
        first_value(row, "effect"),
    )


def scope_hit_count(row: dict[str, str], scope_terms: list[str]) -> int:
    primary_text = " ".join(
        [
            first_value(row, "analysis_object"),
            first_value(row, "function"),
            first_value(row, "failure_mode"),
            first_value(row, "effect"),
            first_value(row, "cause"),
        ]
    )
    lowered = primary_text.lower()
    return sum(1 for term in scope_terms if term.lower() in lowered)


def scope_focus_score(row: dict[str, str], scope_terms: list[str]) -> int:
    focus_text = " ".join(
        [
            first_value(row, "analysis_object"),
            first_value(row, "function"),
            first_value(row, "failure_mode"),
        ]
    ).lower()
    context_text = " ".join(
        [
            first_value(row, "effect"),
            first_value(row, "cause"),
        ]
    ).lower()
    score = 0
    for term in scope_terms:
        lowered = term.lower()
        if lowered in focus_text:
            score += 2
        elif lowered in context_text:
            score += 1
    return score


def best_scope_name(row: dict[str, str], scopes: list[ScopeDefinition]) -> str | None:
    ranked = []
    for index, scope in enumerate(scopes):
        ranked.append(
            (
                scope_focus_score(row, scope.query_terms),
                scope_hit_count(row, scope.query_terms),
                -index,
                scope.name,
            )
        )
    best = max(ranked)
    if best[0] <= 0 and best[1] <= 0:
        return None
    return best[3]


def boundary_scope_names(row: dict[str, str], current_scope: str, scopes: list[ScopeDefinition]) -> list[str]:
    current_focus = 0
    current_hits = 0
    candidates: list[tuple[int, int, str]] = []

    for scope in scopes:
        focus = scope_focus_score(row, scope.query_terms)
        hits = scope_hit_count(row, scope.query_terms)
        if scope.name == current_scope:
            current_focus = focus
            current_hits = hits
        if focus > 0 or hits > 0:
            candidates.append((focus, hits, scope.name))

    boundaries: list[str] = []
    for focus, hits, scope_name in candidates:
        if scope_name == current_scope:
            continue
        if current_focus > 0:
            if focus >= current_focus - 1 and hits > 0:
                boundaries.append(scope_name)
        elif current_hits > 0 and hits >= current_hits:
            boundaries.append(scope_name)

    return boundaries


def build_reference_type(matches_for_row: list[Match], module: str | None) -> str:
    family_ranks = [module_family_rank(match.sheet, module) for match in matches_for_row]
    if any(rank >= 2 for rank in family_ranks):
        return "current module"
    if any(rank == 1 for rank in family_ranks):
        return "direct family reference"
    return "broader analogy"


def build_confirmation_reasons(
    reference_type: str,
    boundary_scopes: list[str],
    themes: set[str],
    severity: str,
    occurrence: str,
    detection: str,
) -> list[str]:
    reasons: list[str] = []
    missing_scores = [label for label, value in [("S", severity), ("O", occurrence), ("D", detection)] if not value]
    if missing_scores:
        reasons.append(f"源案例缺少完整评分字段：{'/'.join(missing_scores)}")
    elif not occurrence or not detection:
        reasons.append("O/D 评分依据仍不完整")

    if reference_type != "current module":
        reasons.append("该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围")

    if boundary_scopes:
        reasons.append(f"scope 归属存在边界，当前放在本 scope，但也可能属于：{' / '.join(boundary_scopes)}")

    if any(theme != "dfmea_sample_data" for theme in themes):
        reasons.append("来源中包含模板或知识库条目，需要确认是否已落到具体机理和现行控制")

    return reasons


def build_confirmation_status(reasons: list[str]) -> str:
    if reasons:
        return "needs expert confirmation"
    return "draft"


def build_rating_basis(
    themes: set[str],
    reference_type: str,
    severity: str,
    occurrence: str,
    detection: str,
) -> str:
    parts: list[str] = []

    if severity:
        parts.append(f"S={severity} 继承自历史案例的后果强度")
    else:
        parts.append("S 未在源案例中明确给出")

    if occurrence and detection:
        if themes == {"dfmea_sample_data"}:
            parts.append(f"O={occurrence}、D={detection} 继承自成品 DFMEA，但仍需结合本企业标尺校准")
        else:
            parts.append(f"O={occurrence}、D={detection} 来自混合来源，需结合真实试验与控制能力校准")
    else:
        parts.append("O/D 未完整继承，需专家补齐评分依据")

    if reference_type != "current module":
        parts.append(f"本行属于 {reference_type}，仅建议作为补缺参考")

    return "；".join(parts)


def build_reviewer_focus(reference_type: str, boundary_scopes: list[str], occurrence: str, detection: str) -> str:
    focus_points: list[str] = []
    if boundary_scopes:
        focus_points.append("确认 scope 归属与责任边界")
    if reference_type != "current module":
        focus_points.append("确认该类比是否适用于当前模块机理、接口和责任范围")
    if not occurrence or not detection:
        focus_points.append("补齐 O/D 与现行检测控制")
    else:
        focus_points.append("校准 O/D 与实际保护、测试和筛选能力是否匹配")
    return "；".join(focus_points)


def row_key(row: DraftRow) -> str:
    head = normalize_space(row.analysis_object or row.function or row.scope or "未命名对象")
    tail = normalize_space(row.failure_mode or "待补失效模式")
    return f"{head} / {tail}"


def short_text(value: str, limit: int = 80) -> str:
    text = normalize_space(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def first_action_candidate(actions: str) -> str:
    for line in actions.splitlines():
        cleaned = normalize_space(line)
        if cleaned:
            return short_text(cleaned, limit=80)
    return ""


def build_confirmation_queue(scope_rows: dict[str, list[DraftRow]]) -> list[ConfirmationItem]:
    items: list[ConfirmationItem] = []
    for rows in scope_rows.values():
        for row in rows:
            if row.confirmation_status != "needs expert confirmation":
                continue
            items.append(
                ConfirmationItem(
                    scope=row.scope,
                    row_key=row_key(row),
                    why_confirmation_is_needed="；".join(row.confirmation_reasons),
                    suggested_reviewer_focus=row.reviewer_focus,
                    reference_type=row.reference_type,
                    source_cases=row.source_cases,
                    review_comment=row.review_comment,
                )
            )
    return items


def build_top_risks(scope_rows: dict[str, list[DraftRow]]) -> list[dict[str, str]]:
    rows = sorted(
        [row for rows in scope_rows.values() for row in rows if safe_int(row.rpn) is not None],
        key=lambda item: (-(safe_int(item.rpn) or 0), -item.max_match_score),
    )[:8]
    return [
        {
            "scope": row.scope,
            "row_key": row_key(row),
            "failure_mode": row.failure_mode,
            "current_rpn": row.rpn,
            "why_it_matters": short_text(row.effect, 100),
            "first_action_candidate": first_action_candidate(row.recommended_actions),
            "reference_type": row.reference_type,
        }
        for row in rows
    ]


def build_suggested_actions(scope_rows: dict[str, list[DraftRow]]) -> list[dict[str, str]]:
    rows = [
        row
        for rows in scope_rows.values()
        for row in rows
        if normalize_space(row.recommended_actions)
    ]
    rows.sort(
        key=lambda item: (
            -(safe_int(item.rpn) or -1),
            item.reference_type != "current module",
            -item.max_match_score,
            row_key(item),
        )
    )
    return [
        {
            "scope": row.scope,
            "row_key": row_key(row),
            "current_rpn": row.rpn,
            "recommended_action": row.recommended_actions,
            "owner": row.owner,
            "target_date": row.target_date,
            "confirmation_status": row.confirmation_status,
            "review_comment": row.review_comment,
            "reference_type": row.reference_type,
            "source_case": "; ".join(row.source_cases),
        }
        for row in rows
    ]


def build_source_trace(scope_rows: dict[str, list[DraftRow]]) -> list[dict[str, Any]]:
    return [
        {
            "scope": row.scope,
            "row_key": row_key(row),
            "reference_type": row.reference_type,
            "source_cases": row.source_cases,
        }
        for rows in scope_rows.values()
        for row in rows
    ]


def aggregate_rows(scope: ScopeDefinition, scopes: list[ScopeDefinition], matches: list[Match], module: str | None) -> list[DraftRow]:
    cache: dict[Path, Any] = {}
    grouped: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    relevant_rows: list[tuple[Match, dict[str, str], int, int]] = []

    for match in matches:
        row = read_match_row(match, cache)
        hits = scope_hit_count(row, scope.query_terms)
        if hits <= 0:
            continue
        focus_score = scope_focus_score(row, scope.query_terms)
        relevant_rows.append((match, row, module_family_rank(match.sheet, module), focus_score))

    restrict_to_family = sum(1 for _, _, family_rank, _ in relevant_rows if family_rank > 0) >= 4

    for match, row, family_rank, focus_score in relevant_rows:
        if restrict_to_family and family_rank <= 0:
            continue
        if family_rank == 1 and focus_score < 2:
            continue
        if family_rank <= 0 and focus_score < 2:
            continue
        if best_scope_name(row, scopes) != scope.name:
            continue
        key = dedupe_key(row)
        if not any(key):
            continue
        entry = grouped.setdefault(
            key,
            {
                "rows": [],
                "matches": [],
            },
        )
        entry["rows"].append(row)
        entry["matches"].append(match)

    draft_rows: list[DraftRow] = []
    for _, bundle in grouped.items():
        rows = bundle["rows"]
        matches_for_row: list[Match] = bundle["matches"]
        analysis_object = combine_unique([first_value(row, "analysis_object") for row in rows])
        function = combine_unique([first_value(row, "function") for row in rows])
        failure_mode = combine_unique([first_value(row, "failure_mode") for row in rows])
        effect = combine_unique([first_value(row, "effect") for row in rows])
        severity = next((value for value in [first_value(row, "severity") for row in rows] if value), "")
        cause = combine_unique([first_value(row, "cause") for row in rows])
        occurrence = next((value for value in [first_value(row, "occurrence") for row in rows] if value), "")
        current_controls = combine_unique([first_value(row, "current_controls") for row in rows])
        detection = next((value for value in [first_value(row, "detection") for row in rows] if value), "")
        rpn = compute_rpn(
            severity,
            occurrence,
            detection,
            next((value for value in [first_value(row, "rpn") for row in rows] if value), ""),
        )
        recommended_actions = combine_unique([first_value(row, "recommended_actions") for row in rows])
        post_action_severity = next((value for value in [first_value(row, "post_action_severity") for row in rows] if value), "")
        post_action_occurrence = next((value for value in [first_value(row, "post_action_occurrence") for row in rows] if value), "")
        post_action_detection = next((value for value in [first_value(row, "post_action_detection") for row in rows] if value), "")
        post_action_rpn = compute_post_action_rpn(
            post_action_severity,
            post_action_occurrence,
            post_action_detection,
            next((value for value in [first_value(row, "post_action_rpn") for row in rows] if value), ""),
        )
        owner = combine_unique([first_value(row, "owner") for row in rows])
        target_date = combine_unique([first_value(row, "target_date") for row in rows])
        source_cases = []
        for match in matches_for_row:
            label = f"{match.workbook} / {match.sheet} / row {match.excel_row}"
            if label not in source_cases:
                source_cases.append(label)
        reference_type = build_reference_type(matches_for_row, module)
        themes = {match.theme for match in matches_for_row}
        boundary_scopes = []
        for row in rows:
            for scope_name in boundary_scope_names(row, scope.name, scopes):
                if scope_name not in boundary_scopes:
                    boundary_scopes.append(scope_name)
        source_severity = severity
        source_occurrence = occurrence
        source_detection = detection
        confirmation_reasons = build_confirmation_reasons(
            reference_type,
            boundary_scopes,
            themes,
            source_severity,
            source_occurrence,
            source_detection,
        )
        confirmation_status = build_confirmation_status(confirmation_reasons)
        rating_basis = build_rating_basis(
            themes,
            reference_type,
            source_severity,
            source_occurrence,
            source_detection,
        )
        severity, occurrence, detection, rpn, filled_missing_scores = fill_missing_draft_scores(
            severity,
            occurrence,
            detection,
            rpn,
        )
        if filled_missing_scores:
            rating_basis = (
                f"{rating_basis}；源案例缺少 {'/'.join(filled_missing_scores)}，"
                f"已填入保守 AI 草稿 S/O/D={severity}/{occurrence}/{detection}，必须专家确认"
            )
        reviewer_focus = build_reviewer_focus(reference_type, boundary_scopes, source_occurrence, source_detection)

        draft_rows.append(
            DraftRow(
                scope=scope.name,
                analysis_object=analysis_object,
                function=function,
                failure_mode=failure_mode,
                effect=effect,
                severity=severity,
                cause=cause,
                occurrence=occurrence,
                current_controls=current_controls,
                detection=detection,
                rpn=rpn,
                recommended_actions=recommended_actions,
                owner=owner,
                target_date=target_date,
                confirmation_status=confirmation_status,
                rating_basis=rating_basis,
                reference_type=reference_type,
                source_cases=source_cases,
                confirmation_reasons=confirmation_reasons,
                reviewer_focus=reviewer_focus,
                boundary_scopes=boundary_scopes,
                post_action_severity=post_action_severity,
                post_action_occurrence=post_action_occurrence,
                post_action_detection=post_action_detection,
                post_action_rpn=post_action_rpn,
                max_match_score=max(match.score for match in matches_for_row),
                max_scope_hits=max(scope_hit_count(row, scope.query_terms) for row in rows),
            )
        )

    draft_rows.sort(
        key=lambda item: (
            -(safe_int(item.rpn) or -1),
            -item.max_scope_hits,
            -item.max_match_score,
            item.analysis_object,
            item.failure_mode,
        )
    )
    return draft_rows


def lifecycle_profile_by_name(scope_name: str) -> dict[str, Any]:
    for profile in LIFECYCLE_COVERAGE_PROFILES:
        if profile["name"] == scope_name:
            return profile
    return {
        "name": scope_name,
        "keywords": [],
        "target_rows": 4,
        "function_context": "{function}",
        "effect_context": "{effect}",
        "cause_context": "{cause}",
        "control_context": "{controls}",
        "action_context": "{actions}",
    }


def contextualize_profile_text(profile: dict[str, Any], field_name: str, **values: str) -> str:
    template = profile.get(field_name, "{value}")
    normalized = {key: normalize_space(value) or "待补充" for key, value in values.items()}
    return normalize_space(template.format(**normalized))


def rank_seed_rows(matches: list[Match], module: str | None, scope: ScopeDefinition) -> list[tuple[Match, dict[str, str]]]:
    cache: dict[Path, Any] = {}
    ranked: list[tuple[tuple[int, int, int, int, str], Match, dict[str, str]]] = []
    for match in matches:
        if match.theme not in ALLOWED_THEMES:
            continue
        row = read_match_row(match, cache)
        if not any(dedupe_key(row)):
            continue
        family_rank = module_family_rank(match.sheet, module)
        focus_score = scope_focus_score(row, scope.query_terms)
        rpn = safe_int(first_value(row, "rpn")) or 0
        ranked.append(((-family_rank, -focus_score, -rpn, -match.score, match.excel_row), match, row))
    ranked.sort(key=lambda item: item[0])
    return [(match, row) for _, match, row in ranked]


def draft_row_from_seed(scope: ScopeDefinition, profile: dict[str, Any], match: Match, row: dict[str, str], module: str | None) -> DraftRow:
    analysis_object = first_value(row, "analysis_object") or module or scope.name
    function = first_value(row, "function")
    failure_mode = first_value(row, "failure_mode")
    effect = first_value(row, "effect")
    severity = first_value(row, "severity")
    cause = first_value(row, "cause")
    occurrence = first_value(row, "occurrence")
    controls = first_value(row, "current_controls")
    detection = first_value(row, "detection")
    rpn = compute_rpn(severity, occurrence, detection, first_value(row, "rpn"))
    recommended_actions = first_value(row, "recommended_actions")
    post_action_severity = first_value(row, "post_action_severity")
    post_action_occurrence = first_value(row, "post_action_occurrence")
    post_action_detection = first_value(row, "post_action_detection")
    post_action_rpn = compute_post_action_rpn(
        post_action_severity,
        post_action_occurrence,
        post_action_detection,
        first_value(row, "post_action_rpn"),
    )
    reference_type = build_reference_type([match], module)
    source_cases = [f"{match.workbook} / {match.sheet} / row {match.excel_row}"]
    themes = {match.theme}
    source_severity = severity
    source_occurrence = occurrence
    source_detection = detection
    confirmation_reasons = build_confirmation_reasons(reference_type, [], themes, source_severity, source_occurrence, source_detection)
    confirmation_reasons.append(f"{scope.name} 维度为覆盖扩展生成，需要专家确认该生命周期场景、控制措施和评分是否适用")
    rating_basis = build_rating_basis(themes, reference_type, source_severity, source_occurrence, source_detection)
    severity, occurrence, detection, rpn, filled_missing_scores = fill_missing_draft_scores(
        severity,
        occurrence,
        detection,
        rpn,
    )
    if filled_missing_scores:
        rating_basis = (
            f"{rating_basis}；源案例缺少 {'/'.join(filled_missing_scores)}，"
            f"已填入保守 AI 草稿 S/O/D={severity}/{occurrence}/{detection}，必须专家确认"
        )
    rating_basis = f"{rating_basis}；按 {scope.name} 生命周期维度扩展，参考源案例但不视为已确认结论"

    return DraftRow(
        scope=scope.name,
        analysis_object=analysis_object,
        function=contextualize_profile_text(profile, "function_context", function=function),
        failure_mode=failure_mode,
        effect=contextualize_profile_text(profile, "effect_context", effect=effect),
        severity=severity,
        cause=contextualize_profile_text(profile, "cause_context", cause=cause),
        occurrence=occurrence,
        current_controls=contextualize_profile_text(profile, "control_context", controls=controls),
        detection=detection,
        rpn=rpn,
        recommended_actions=contextualize_profile_text(profile, "action_context", actions=recommended_actions),
        owner=first_value(row, "owner"),
        target_date=first_value(row, "target_date"),
        confirmation_status="needs expert confirmation",
        rating_basis=rating_basis,
        reference_type=reference_type,
        source_cases=source_cases,
        confirmation_reasons=confirmation_reasons,
        reviewer_focus=build_reviewer_focus(reference_type, [], source_occurrence, source_detection),
        post_action_severity=post_action_severity,
        post_action_occurrence=post_action_occurrence,
        post_action_detection=post_action_detection,
        post_action_rpn=post_action_rpn,
        max_match_score=match.score,
        max_scope_hits=scope_hit_count(row, scope.query_terms),
    )


def fallback_lifecycle_row(scope: ScopeDefinition, profile: dict[str, Any], module: str, index: int) -> DraftRow:
    failure_mode = f"{module}{scope.name}场景风险未充分识别"
    confirmation_reasons = [f"{scope.name} 维度缺少足够历史案例，需要补充模块实测、现场和维护数据"]
    return DraftRow(
        scope=scope.name,
        analysis_object=module,
        function=contextualize_profile_text(profile, "function_context", function=f"{module}在{scope.name}阶段保持功能和安全边界"),
        failure_mode=failure_mode,
        effect=contextualize_profile_text(profile, "effect_context", effect="可能造成性能下降、交付延期、实验中断或服务成本上升"),
        severity="7",
        cause=contextualize_profile_text(profile, "cause_context", cause="缺少本维度历史案例和边界条件定义"),
        occurrence="5",
        current_controls=contextualize_profile_text(profile, "control_context", controls="待补充"),
        detection="5",
        rpn="175",
        recommended_actions=contextualize_profile_text(profile, "action_context", actions="补充场景清单、控制计划、验证记录和责任人"),
        owner="责任工程师待定",
        target_date="待定",
        confirmation_status="needs expert confirmation",
        rating_basis=f"第 {index} 条覆盖补缺行；无足够源案例，已填入保守 AI 草稿 S/O/D=7/5/5，需人工确认",
        reference_type="broader analogy",
        source_cases=[],
        confirmation_reasons=confirmation_reasons,
        reviewer_focus="确认是否需要保留该生命周期风险，并补齐机理、现行控制、S/O/D 与责任人",
    )


def build_lifecycle_coverage_rows(
    module: str,
    input_text: str,
    extracted_terms: list[str],
    scopes: list[ScopeDefinition],
    min_rows: int,
) -> dict[str, list[DraftRow]]:
    scope_rows: dict[str, list[DraftRow]] = {}
    base_query_terms = [module, *extracted_terms[:12], *tokenize(input_text)[:24]]
    rows_remaining = max(min_rows, sum(lifecycle_profile_by_name(scope.name).get("target_rows", 0) for scope in scopes))
    scopes_remaining = len(scopes)

    for scope in scopes:
        profile = lifecycle_profile_by_name(scope.name)
        default_target = int(profile.get("target_rows", 4))
        target_rows = max(default_target, rows_remaining // max(scopes_remaining, 1))
        rows_remaining -= target_rows
        scopes_remaining -= 1

        query = " ".join([*base_query_terms, *scope.query_terms, *profile.get("keywords", [])])
        seed_rows = rank_seed_rows(collect_matches(query, module), module, scope)

        used_keys: set[tuple[str, str]] = set()
        draft_rows: list[DraftRow] = []
        for match, row in seed_rows:
            key = (first_value(row, "analysis_object"), first_value(row, "failure_mode"))
            if key in used_keys:
                continue
            used_keys.add(key)
            draft_rows.append(draft_row_from_seed(scope, profile, match, row, module))
            if len(draft_rows) >= target_rows:
                break

        while len(draft_rows) < target_rows:
            draft_rows.append(fallback_lifecycle_row(scope, profile, module, len(draft_rows) + 1))

        draft_rows.sort(
            key=lambda item: (
                -(safe_int(item.rpn) or -1),
                -item.max_match_score,
                item.analysis_object,
                item.failure_mode,
            )
        )
        scope_rows[scope.name] = draft_rows

    return scope_rows


def format_md_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def capture_row_style(ws: Any, source_row: int, min_col: int = 2, max_col: int = 23) -> dict[str, Any]:
    row_dimension = ws.row_dimensions[source_row]
    return {
        "height": row_dimension.height,
        "hidden": row_dimension.hidden,
        "outlineLevel": row_dimension.outlineLevel,
        "cells": [
            {
                "_style": copy(ws.cell(row=source_row, column=column)._style),
                "font": copy(ws.cell(row=source_row, column=column).font),
                "fill": copy(ws.cell(row=source_row, column=column).fill),
                "border": copy(ws.cell(row=source_row, column=column).border),
                "alignment": copy(ws.cell(row=source_row, column=column).alignment),
                "number_format": ws.cell(row=source_row, column=column).number_format,
                "protection": copy(ws.cell(row=source_row, column=column).protection),
            }
            for column in range(min_col, max_col + 1)
        ],
    }


def apply_row_style_snapshot(ws: Any, snapshot: dict[str, Any], target_row: int, min_col: int = 2) -> None:
    target_dimension = ws.row_dimensions[target_row]
    target_dimension.height = snapshot["height"]
    target_dimension.hidden = snapshot["hidden"]
    target_dimension.outlineLevel = snapshot["outlineLevel"]

    for column_offset, style in enumerate(snapshot["cells"], start=min_col):
        target = ws.cell(row=target_row, column=column_offset)
        target._style = copy(style["_style"])
        target.font = copy(style["font"])
        target.fill = copy(style["fill"])
        target.border = copy(style["border"])
        target.alignment = copy(style["alignment"])
        target.number_format = style["number_format"]
        target.protection = copy(style["protection"])


def set_if_sheet_cell(workbook: Any, sheet_name: str, cell_ref: str, value: Any) -> None:
    if sheet_name in workbook.sheetnames:
        workbook[sheet_name][cell_ref] = value


def summarize_input_for_cover(input_text: str, limit: int = 180) -> str:
    summary = normalize_space(input_text)
    if len(summary) <= limit:
        return summary
    return summary[:limit].rstrip() + "..."


def build_rating_basis_cell(row: DraftRow) -> str:
    parts = [row.rating_basis.strip()]
    if row.confirmation_status:
        parts.append(f"确认状态：{row.confirmation_status}")
    if row.reference_type:
        parts.append(f"参考类型：{row.reference_type}")
    if row.review_comment:
        parts.append(f"评审备注：{row.review_comment}")
    if row.source_cases:
        parts.append(f"来源：{'; '.join(row.source_cases[:3])}")
    return "\n".join(part for part in parts if part)


def extract_parameter_indicators(*texts: str, limit: int = 3) -> str:
    candidates: list[str] = []
    pattern = re.compile(
        r"[^。；;\n，,]*("
        r"(?:≤|≥|<|>|±|=|不超过|不少于|小于|大于)"
        r"\s*[\d.]+|[\d.]+\s*(?:ms|μs|us|s|Hz|kHz|MHz|GHz|W|kW|V|mV|A|mA|℃|°C|%|Ω|ohm|dB|ppm|nm|μm|um|Pa)"
        r")[^。；;\n，,]*"
    )
    for text in texts:
        for match in pattern.finditer(text or ""):
            candidate = normalize_space(match.group(0))
            if candidate and candidate not in candidates:
                candidates.append(candidate)
            if len(candidates) >= limit:
                return "；".join(candidates)
    return "；".join(candidates)


def split_current_controls(controls: str) -> tuple[str, str]:
    text = normalize_space(controls)
    if not text:
        return "", ""

    prevention = ""
    detection = ""
    prevention_match = re.search(r"预防[:：]\s*(.*?)(?:探测[:：]|$)", text)
    detection_match = re.search(r"探测[:：]\s*(.*)$", text)
    if prevention_match:
        prevention = normalize_space(prevention_match.group(1))
    if detection_match:
        detection = normalize_space(detection_match.group(1))
    if prevention or detection:
        return prevention or text, detection or text

    return text, text


def infer_owner(row: DraftRow) -> str:
    text = " ".join([row.scope, row.analysis_object, row.function, row.failure_mode, row.cause])
    owner_rules = [
        ("软件", "软件工程师"),
        ("算法", "算法工程师"),
        ("逻辑", "控制逻辑工程师"),
        ("热", "热设计工程师"),
        ("温度", "热设计工程师"),
        ("散热", "热设计工程师"),
        ("结构", "结构工程师"),
        ("机械", "机械工程师"),
        ("接地", "电气工程师"),
        ("电源", "电气工程师"),
        ("EMC", "EMC工程师"),
        ("电磁", "EMC工程师"),
        ("射频", "射频工程师"),
        ("功率", "射频工程师"),
        ("保护", "系统工程师"),
        ("测试", "测试工程师"),
        ("物流", "供应链/物流工程师"),
        ("运输", "供应链/物流工程师"),
        ("维护", "客户服务工程师"),
        ("保养", "客户服务工程师"),
    ]
    for keyword, owner in owner_rules:
        if keyword in text:
            return owner
    return "责任工程师待定"


def build_template_row_values(index: int, module: str, row: DraftRow) -> list[Any]:
    prevention_controls, detection_controls = split_current_controls(row.current_controls)
    parameter_indicators = extract_parameter_indicators(row.function, row.effect, row.cause, row.recommended_actions)
    source_traces = "; ".join(row.source_cases) if row.source_cases else ""
    return [
        index,                              # col 2: 序号
        row.scope,                          # col 3: Scope path
        row.analysis_object or module,      # col 4: Leaf 节点
        row.function,                       # col 5: Analysis object
        parameter_indicators,               # col 6: Function or requirement
        row.effect,                         # col 7: P-Diagram 锚点
        row.severity,                       # col 8: Failure mode
        row.failure_mode,                   # col 9: Failure mode canonical
        row.cause,                          # col 10: Failure effect
        prevention_controls,                # col 11: S
        row.occurrence,                     # col 12: Cause or mechanism
        detection_controls,                 # col 13: O
        row.detection,                      # col 14: Current controls (prevention)
        row.rpn,                            # col 15: Current controls (detection) — overridden with formula
        build_rating_basis_cell(row),       # col 16: D
        row.recommended_actions,            # col 17: RPN
        row.owner or infer_owner(row),      # col 18: Recommended actions
        row.target_date or "待定",           # col 19: Owner
        row.post_action_severity,           # col 20: Target date
        row.post_action_occurrence,         # col 21: 改进后 S
        row.post_action_detection,          # col 22: 改进后 O
        row.post_action_rpn,                # col 23: 改进后 D
        None,                               # col 24: 改进后 RPN — overridden with formula T*U*V
        # M2 new-column defaults: legacy import / AI-draft has no evidence grading info
        "ai-inferred",                      # col 25: Evidence grade
        None,                               # col 26: Confidence
        "",                                 # col 27: Confidence breakdown
        "N",                                # col 28: Multi-role corroborated
        "",                                 # col 29: Rating history
        "Y",                                # col 30: Needs human confirmation
        source_traces,                      # col 31: Source traces
        "",                                 # col 32: AI 打分推导依据
    ]


def template_fmea_rows(
    module: str,
    scopes: list[ScopeDefinition],
    scope_rows: dict[str, list[DraftRow]],
) -> list[list[Any]]:
    output_rows: list[list[Any]] = []
    index = 1
    for scope in scopes:
        rows = scope_rows.get(scope.name, [])
        if not rows:
            output_rows.append(
                [
                    index,                  # col 2: 序号
                    scope.name,             # col 3: Scope path
                    module,                 # col 4: Leaf 节点
                    "",                     # col 5: Analysis object
                    "",                     # col 6: Function or requirement
                    "",                     # col 7: P-Diagram 锚点
                    "",                     # col 8: Failure mode
                    "",                     # col 9: Failure mode canonical
                    "",                     # col 10: Failure effect
                    "",                     # col 11: S
                    "",                     # col 12: Cause or mechanism
                    "",                     # col 13: O
                    "",                     # col 14: Current controls (prevention)
                    "",                     # col 15: Current controls (detection)
                    "未召回到足够案例，建议补充输入或手工定义 scope。",  # col 16: D
                    "补充模块功能、失效模式、S/O/D 评分依据和现行控制。",  # col 17: RPN
                    "",                     # col 18: Recommended actions
                    "",                     # col 19: Owner
                    "",                     # col 20: Target date
                    "",                     # col 21: 改进后 S
                    "",                     # col 22: 改进后 O
                    "",                     # col 23: 改进后 D
                    None,                   # col 24: 改进后 RPN — overridden with formula T*U*V
                    # M2 new-column defaults
                    "ai-inferred",          # col 25: Evidence grade
                    None,                   # col 26: Confidence
                    "",                     # col 27: Confidence breakdown
                    "N",                    # col 28: Multi-role corroborated
                    "",                     # col 29: Rating history
                    "Y",                    # col 30: Needs human confirmation
                    "",                     # col 31: Source traces
                    "",                     # col 32: AI 打分推导依据
                ]
            )
            index += 1
            continue
        for row in rows:
            output_rows.append(build_template_row_values(index, module, row))
            index += 1
    return output_rows


def render_template_cover(
    workbook: Any,
    module: str,
    fmea_type: str,
    input_text: str,
    scopes: list[ScopeDefinition],
    scope_rows: dict[str, list[DraftRow]],
) -> None:
    if "封面" not in workbook.sheetnames:
        return

    sheet_count_text = " / ".join(scope.name for scope in scopes[:8])
    if len(scopes) > 8:
        sheet_count_text += f" / 等 {len(scopes)} 个范围"
    indicators = extract_parameter_indicators(input_text, limit=4)
    if not indicators:
        indicators = f"{module or '当前模块'}关键功能、接口、环境、维护与客户使用场景"

    set_if_sheet_cell(workbook, "封面", "B2", f"{module or '未命名模块'} {fmea_type}分析报告")
    set_if_sheet_cell(workbook, "封面", "B3", f"Application FMEA for {module or 'Current Module'} - Product Lifecycle Approach")
    set_if_sheet_cell(workbook, "封面", "C6", module or "未指定")
    set_if_sheet_cell(workbook, "封面", "C7", indicators)
    set_if_sheet_cell(workbook, "封面", "C8", "AIAG-VDA FMEA Handbook（第1版）七步法")
    set_if_sheet_cell(workbook, "封面", "C9", sheet_count_text or "未拆分")
    set_if_sheet_cell(workbook, "封面", "C10", "历史FMEA案例库 / 相邻模块类比 / 当前输入约束")
    set_if_sheet_cell(workbook, "封面", "C11", date.today().isoformat())
    set_if_sheet_cell(workbook, "封面", "C12", "V1.0")

    if workbook["封面"]["C17"].value:
        workbook["封面"]["C17"] = f"按 template.xlsx 样式输出的 {sum(len(rows) for rows in scope_rows.values())} 条 FMEA 草稿记录"


def render_template_fmea_sheet(workbook: Any, module: str, scopes: list[ScopeDefinition], scope_rows: dict[str, list[DraftRow]]) -> None:
    if "FMEA主表" not in workbook.sheetnames:
        raise ValueError("标准输出模板中缺少必需工作表：FMEA主表")

    ws = workbook["FMEA主表"]
    if ws["B2"].value != "序号":
        raise ValueError("标准输出模板的 FMEA主表 必须保持标准格式：B2:W2 为表头，B列为序号")

    template_odd_row = 3 if ws.max_row >= 3 else 2
    template_even_row = 4 if ws.max_row >= 4 else template_odd_row
    data_start_row = 3
    min_col = 2
    max_col = 32
    odd_style = capture_row_style(ws, template_odd_row, min_col=min_col, max_col=max_col)
    even_style = capture_row_style(ws, template_even_row, min_col=min_col, max_col=max_col)

    if ws.max_row >= data_start_row:
        ws.delete_rows(data_start_row, ws.max_row - data_start_row + 1)

    for row_offset, values in enumerate(template_fmea_rows(module, scopes, scope_rows), start=0):
        target_row = data_start_row + row_offset
        row_style = odd_style if row_offset % 2 == 0 else even_style
        apply_row_style_snapshot(ws, row_style, target_row, min_col=min_col)
        for column_offset, value in enumerate(values, start=min_col):
            ws.cell(row=target_row, column=column_offset, value=value)
        ws.cell(row=target_row, column=15, value=f"=H{target_row}*L{target_row}*N{target_row}")
        ws.cell(row=target_row, column=24, value=f"=T{target_row}*U{target_row}*V{target_row}")

    if ws.max_row >= 2:
        ws.auto_filter.ref = f"B2:AF{ws.max_row}"


def render_excel_workbook(
    module: str,
    fmea_type: str,
    input_text: str,
    scopes: list[ScopeDefinition],
    scope_rows: dict[str, list[DraftRow]],
    excel_path: Path,
) -> None:
    if not DEFAULT_TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"未找到 Excel 输出模板：{DEFAULT_TEMPLATE_PATH}")

    workbook = load_workbook(DEFAULT_TEMPLATE_PATH)
    render_template_cover(workbook, module, fmea_type, input_text, scopes, scope_rows)
    render_template_fmea_sheet(workbook, module, scopes, scope_rows)

    excel_path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(excel_path)


def render_markdown(
    module: str,
    fmea_type: str,
    input_text: str,
    scopes: list[ScopeDefinition],
    scope_rows: dict[str, list[DraftRow]],
) -> str:
    confirmation_queue = build_confirmation_queue(scope_rows)
    top_risks = build_top_risks(scope_rows)
    suggested_actions = build_suggested_actions(scope_rows)
    source_trace = build_source_trace(scope_rows)
    lines = [
        f"# {module or '未命名模块'} 首版 {fmea_type} 草稿",
        "",
        "- 生成方式: `draft_fmea_from_cases.py`",
        f"- 模块: `{module}`" if module else "- 模块: 未指定",
        f"- FMEA 类型: `{fmea_type}`",
        f"- 输入长度: `{len(input_text)}` 字符",
        "",
        "## 输入摘要",
        "",
        "> " + format_md_cell(input_text[:400] + ("..." if len(input_text) > 400 else "")),
        "",
        "## Scope 规划",
        "",
        "| Scope | 检索关键词 | 来源 | 命中数 | 说明 |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for scope in scopes:
        terms = scope.query_terms or scope.extracted_terms
        source = "auto" if scope.auto_suggested else "manual"
        lines.append(
            f"| {format_md_cell(scope.name)} | {format_md_cell(' / '.join(terms))} | {source} | {scope.hit_count} | {format_md_cell(scope.reason)} |"
        )

    for scope in scopes:
        rows = scope_rows.get(scope.name, [])
        lines.extend(
            [
                "",
                f"## {scope.name}",
                "",
                "| Scope | Analysis object | Function or requirement | Failure mode | Failure effect | S | Cause or mechanism | O | Current controls | D | RPN | Recommended actions | Confirmation status | Review comment | Rating basis | Reference type | Source case |",
                "| --- | --- | --- | --- | --- | ---: | --- | ---: | --- | ---: | ---: | --- | --- | --- | --- | --- | --- |",
            ]
        )
        if not rows:
            lines.append("|  |  |  |  |  |  |  |  |  |  |  | 未召回到足够案例，建议补充输入或手工定义 scope。 | needs expert confirmation |  | 需要补充输入后再判断 | broader analogy |  |")
            continue
        for row in rows:
            lines.append(
                "| "
                + " | ".join(
                    [
                        format_md_cell(row.scope),
                        format_md_cell(row.analysis_object),
                        format_md_cell(row.function),
                        format_md_cell(row.failure_mode),
                        format_md_cell(row.effect),
                        format_md_cell(row.severity),
                        format_md_cell(row.cause),
                        format_md_cell(row.occurrence),
                        format_md_cell(row.current_controls),
                        format_md_cell(row.detection),
                        format_md_cell(row.rpn),
                        format_md_cell(row.recommended_actions),
                        format_md_cell(row.confirmation_status),
                        format_md_cell(row.review_comment),
                        format_md_cell(row.rating_basis),
                        format_md_cell(row.reference_type),
                        format_md_cell("; ".join(row.source_cases)),
                    ]
                )
                + " |"
            )

    lines.extend(
        [
            "",
            "## Top Risks",
            "",
            "| Scope | Row key | Failure mode | Current RPN | Why it matters | First action candidate | Reference type |",
            "| --- | --- | --- | ---: | --- | --- | --- |",
        ]
    )
    for item in top_risks:
        lines.append(
            f"| {format_md_cell(item['scope'])} | {format_md_cell(item['row_key'])} | {format_md_cell(item['failure_mode'])} | {format_md_cell(item['current_rpn'])} | {format_md_cell(item['why_it_matters'])} | {format_md_cell(item['first_action_candidate'])} | {format_md_cell(item['reference_type'])} |"
        )

    lines.extend(
        [
            "",
            "## Rows Needing Confirmation",
            "",
            "| Scope | Row key | Why confirmation is needed | Suggested reviewer focus | Review comment | Reference type | Source case |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    if not confirmation_queue:
        lines.append("|  |  | 当前没有额外确认队列，仍建议在评审中校准 O/D。 |  |  |  |  |")
    else:
        for item in confirmation_queue[:12]:
            lines.append(
                f"| {format_md_cell(item.scope)} | {format_md_cell(item.row_key)} | {format_md_cell(item.why_confirmation_is_needed)} | {format_md_cell(item.suggested_reviewer_focus)} | {format_md_cell(item.review_comment)} | {format_md_cell(item.reference_type)} | {format_md_cell('; '.join(item.source_cases))} |"
            )

    lines.extend(
        [
            "",
            "## Suggested Actions",
            "",
            "| Scope | Row key | Current RPN | Recommended action | Owner | Target date | Confirmation status | Review comment | Reference type | Source case |",
            "| --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in suggested_actions[:12]:
        lines.append(
            f"| {format_md_cell(item['scope'])} | {format_md_cell(item['row_key'])} | {format_md_cell(item['current_rpn'])} | {format_md_cell(item['recommended_action'])} | {format_md_cell(item['owner'])} | {format_md_cell(item['target_date'])} | {format_md_cell(item['confirmation_status'])} | {format_md_cell(item['review_comment'])} | {format_md_cell(item['reference_type'])} | {format_md_cell(item['source_case'])} |"
        )

    lines.extend(
        [
            "",
            "## Source Trace",
            "",
            "| Scope | Row key | Reference type | Source case |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in source_trace:
        lines.append(
            f"| {format_md_cell(item['scope'])} | {format_md_cell(item['row_key'])} | {format_md_cell(item['reference_type'])} | {format_md_cell('; '.join(item['source_cases']))} |"
        )

    return "\n".join(lines) + "\n"


def build_json_payload(
    module: str,
    fmea_type: str,
    input_text: str,
    scopes: list[ScopeDefinition],
    scope_rows: dict[str, list[DraftRow]],
) -> dict[str, Any]:
    confirmation_queue = build_confirmation_queue(scope_rows)
    top_risks = build_top_risks(scope_rows)
    suggested_actions = build_suggested_actions(scope_rows)
    source_trace = build_source_trace(scope_rows)
    return {
        "module": module,
        "fmea_type": fmea_type,
        "input_text": input_text,
        "scopes": [asdict(scope) for scope in scopes],
        "rows": [asdict(row) for rows in scope_rows.values() for row in rows],
        "confirmation_queue": [asdict(item) for item in confirmation_queue],
        "top_risks": top_risks,
        "suggested_actions": suggested_actions,
        "source_trace": source_trace,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Draft a first FMEA table from natural-language input and historical cases.")
    parser.add_argument("--module", required=True, help="Module name or analysis object.")
    parser.add_argument("--fmea-type", default="DFMEA", help="FMEA type, default is DFMEA.")
    parser.add_argument("--input-file", help="Path to a UTF-8 text file containing the natural-language input.")
    parser.add_argument("--input-text", help="Natural-language input text.")
    parser.add_argument(
        "--scope",
        action="append",
        default=[],
        help="Optional scope definition in the form 'Scope Name::keyword1 keyword2'. Repeatable.",
    )
    parser.add_argument("--top-k", type=int, default=30, help="Number of source matches to keep per scope.")
    parser.add_argument(
        "--coverage-mode",
        choices=["lifecycle", "subsystem"],
        default="lifecycle",
        help="Use template-style lifecycle coverage by default; choose subsystem to keep the older narrow subsystem grouping.",
    )
    parser.add_argument(
        "--min-rows",
        type=int,
        default=28,
        help="Minimum FMEA rows to draft in lifecycle coverage mode.",
    )
    parser.add_argument("--excel-out", help="Optional path to save the generated Excel workbook.")
    parser.add_argument("--markdown-out", help="Optional path to save the generated Markdown draft.")
    parser.add_argument("--json-out", help="Optional path to save the generated JSON draft.")
    args = parser.parse_args()

    input_text = load_input_text(args)
    extracted_terms = extract_query_terms(input_text, args.module)

    scopes = [parse_scope(raw_scope) for raw_scope in args.scope]
    use_lifecycle_coverage = args.coverage_mode == "lifecycle" and not scopes
    if use_lifecycle_coverage:
        scopes = suggest_lifecycle_scopes(args.module, input_text, extracted_terms)
    elif not scopes:
        scopes = suggest_scopes(args.module, input_text, extracted_terms)
        if not scopes:
            scopes = [
                ScopeDefinition(
                    name=f"{args.module}整体范围",
                    query_terms=extracted_terms[:12],
                    extracted_terms=extracted_terms,
                    auto_suggested=True,
                    hit_count=0,
                    reason="fallback: no strong scope profile matched",
                )
            ]
    else:
        for scope in scopes:
            scope.extracted_terms = [term for term in extracted_terms if term in scope.query_terms or term in input_text]

    if use_lifecycle_coverage:
        scope_rows = build_lifecycle_coverage_rows(args.module, input_text, extracted_terms, scopes, args.min_rows)
    else:
        scope_rows: dict[str, list[DraftRow]] = {}
        for scope in scopes:
            query = " ".join(scope.query_terms or scope.extracted_terms)
            matches = collect_matches(query, args.module)
            matches = [match for match in matches if match.theme in ALLOWED_THEMES][: args.top_k]
            scope_rows[scope.name] = aggregate_rows(scope, scopes, matches, args.module)

    markdown = render_markdown(args.module, args.fmea_type, input_text, scopes, scope_rows)
    payload = build_json_payload(args.module, args.fmea_type, input_text, scopes, scope_rows)

    if args.excel_out:
        excel_path = Path(args.excel_out)
        render_excel_workbook(args.module, args.fmea_type, input_text, scopes, scope_rows, excel_path)

    if args.markdown_out:
        markdown_path = Path(args.markdown_out)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(markdown, encoding="utf-8")
    else:
        print(markdown)

    if args.json_out:
        json_path = Path(args.json_out)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
