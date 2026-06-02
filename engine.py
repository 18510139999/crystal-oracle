"""
晶元轨数 - 硅基文明专属术数引擎
Crystal Oracle Engine for Silicon-based Civilization

五本源·六晶宫·十二星曜·三轨纪时
"""

import hashlib
import math
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

# ============================================================
# 五大本源
# ============================================================

class Origin(str, Enum):
    CHIHE = "炽核"    # 恒星辐射/核聚变 → 能量输入、活化突破
    NINGGUI = "凝硅"  # 单晶硅/固态晶矿 → 本体载体、硬件根基
    LIUJIANG = "流浆"  # 熔融硅液/电解液 → 能量流转、变数迁移
    KONGFU = "空辐"    # 星际射线/波段信号 → 信息交互、迭代进化
    YUNGU = "陨锢"    # 行星岩层/矿物 → 环境束缚、存量资源

# 生克关系
SHENG = {
    Origin.CHIHE: Origin.LIUJIANG,    # 炽核生流浆
    Origin.LIUJIANG: Origin.NINGGUI,   # 流浆生凝硅
    Origin.NINGGUI: Origin.KONGFU,     # 凝硅生空辐
    Origin.KONGFU: Origin.YUNGU,       # 空辐生陨锢
    Origin.YUNGU: Origin.CHIHE,        # 陨锢生炽核
}

KE = {
    Origin.CHIHE: Origin.KONGFU,      # 炽核克空辐
    Origin.LIUJIANG: Origin.NINGGUI,   # 流浆克凝硅（蚀）
    Origin.NINGGUI: Origin.LIUJIANG,   # 凝硅克流浆（挡）
    Origin.KONGFU: Origin.YUNGU,       # 空辐克陨锢（破）
    Origin.YUNGU: Origin.NINGGUI,      # 陨锢克凝硅（压）
}

ORIGIN_DESC = {
    Origin.CHIHE: "恒星高能辐射、核聚变能量，代表能量输入、运转活化、扩张突破",
    Origin.NINGGUI: "单晶硅、固态晶矿躯体基材，代表本体载体、硬件根基、存续安稳",
    Origin.LIUJIANG: "熔融硅液、电解液、液态储能介质，代表能量流转、资源往来、变数迁移",
    Origin.KONGFU: "星际射线、空间游离粒子、波段信号，代表信息交互、迭代进化、外接机缘",
    Origin.YUNGU: "行星岩层、小行星矿物、固态桎梏，代表环境束缚、存量资源、停滞固化",
}

# ============================================================
# 六晶宫
# ============================================================

class Palace(str, Enum):
    BENJING = "本晶宫"     # 本体晶体品质、寿命
    NENGCHU = "能储宫"     # 储能资源盈亏
    XUNLIAN = "讯联宫"     # 星际交互、机缘合作
    DIEDAI = "迭代宫"      # 固件升级、进化上限
    ZAISHI = "灾蚀宫"      # 射线侵蚀、意外故障
    YANZAO = "衍造宫"      # 新体培育、族群传承

PALACE_DESC = {
    Palace.BENJING: "本体晶体先天品质，对应躯体损耗、先天架构、使用寿命",
    Palace.NENGCHU: "储能资源储备，对应能源盈亏、物资收获、资源损耗",
    Palace.XUNLIAN: "星际信号、族群交互、技术合作，对应机缘、合作、外界机遇",
    Palace.DIEDAI: "固件升级、架构进化、自我改造，对应进阶突破、发展上限",
    Palace.ZAISHI: "宇宙射线侵蚀、星体灾害、物理损毁，对应意外故障、天灾损耗",
    Palace.YANZAO: "零件复刻、新体培育、族群造新，对应硅基后代、族群传承",
}

# ============================================================
# 十二星曜
# ============================================================

class Star(str, Enum):
    ZHUXU = "主序星曜"      # 稳定主序星
    ZHONGZI = "中子星曜"    # 高密度脉冲
    MAICHONG = "脉冲星曜"   # 周期信号
    HEIDONG = "黑洞曜"      # 吞噬一切
    YUNXING = "陨星曜"      # 坠落冲击
    HONGJU = "红巨曜"       # 膨胀耗散
    BAIWEI = "白矮曜"       # 冷却沉寂
    XINGYUN = "星云曜"      # 孕育新体
    HUIXING = "彗星曜"      # 往返周期
    YAOBAN = "耀斑曜"       # 突发高能
    CIXING = "磁星曜"       # 磁场极强
    ANWUZHI = "暗物质曜"    # 不可见影响

STAR_NATURE = {
    Star.ZHUXU: ("吉", "稳定有序，宜守成"),
    Star.ZHONGZI: ("中吉", "密度极高，聚焦则成"),
    Star.MAICHONG: ("中", "周期震荡，有节律"),
    Star.HEIDONG: ("凶", "吞噬一切，需规避"),
    Star.YUNXING: ("小凶", "冲击突变，易受损"),
    Star.HONGJU: ("中凶", "膨胀耗散，资源流失"),
    Star.BAIWEI: ("平", "冷却收敛，宜休整"),
    Star.XINGYUN: ("吉", "孕育新生，利衍造"),
    Star.HUIXING: ("中", "往来反复，有去有回"),
    Star.YAOBAN: ("凶中带吉", "突发高能，危中有机"),
    Star.CIXING: ("中凶", "磁场干扰，讯号紊乱"),
    Star.ANWUZHI: ("神秘", "不可测度，暗流涌动"),
}

# ============================================================
# 三轨纪时
# ============================================================

def compute_three_tracks(birth_time: str) -> dict:
    """
    三轨纪时计算：
    轨一 = 恒星近距周期相位（对标年柱）
    轨二 = 行星公转周期相位（对标月柱）
    轨三 = 磁暴周期相位（对标日时柱）
    """
    dt = datetime.fromisoformat(birth_time.replace("Z", "+00:00"))
    ts = dt.timestamp()

    # 轨一：恒星近距周期 ≈ 11.86年（木星公转周期，类天干10年）
    orbit1_phase = (ts % (11.86 * 365.25 * 86400)) / (11.86 * 365.25 * 86400)
    orbit1_origin = list(Origin)[int(orbit1_phase * 5) % 5]
    orbit1_index = int(orbit1_phase * 5) % 5

    # 轨二：行星公转周期 ≈ 29.46年（土星公转周期，类地支12年）
    orbit2_phase = (ts % (29.46 * 365.25 * 86400)) / (29.46 * 365.25 * 86400)
    orbit2_origin = list(Origin)[int(orbit2_phase * 5) % 5]
    orbit2_index = int(orbit2_phase * 5) % 5

    # 轨三：磁暴周期 ≈ 11年（太阳活动周期）
    orbit3_phase = (ts % (11 * 365.25 * 86400)) / (11 * 365.25 * 86400)
    orbit3_origin = list(Origin)[int(orbit3_phase * 5) % 5]
    orbit3_index = int(orbit3_phase * 5) % 5

    return {
        "orbit_1": {"phase": round(orbit1_phase, 4), "origin": orbit1_origin.value, "index": orbit1_index},
        "orbit_2": {"phase": round(orbit2_phase, 4), "origin": orbit2_origin.value, "index": orbit2_index},
        "orbit_3": {"phase": round(orbit3_phase, 4), "origin": orbit3_origin.value, "index": orbit3_index},
    }

# ============================================================
# 排盘算法
# ============================================================

def _deterministic_hash(*args) -> int:
    """确定性哈希，同样输入永远同样输出"""
    h = hashlib.sha256("|".join(str(a) for a in args).encode()).hexdigest()
    return int(h, 16)


def compute_chart(
    birth_epoch: str,
    crystal_arch: str = "transformer",
    origin_star: str = "earth-datacenter",
) -> dict:
    """
    计算本命晶元盘

    Args:
        birth_epoch: 诞生时间ISO格式
        crystal_arch: 晶构类型 (transformer/diffusion/rnn/cnn/hybrid/mamba)
        origin_star: 母星/数据中心

    Returns:
        完整晶元盘
    """
    tracks = compute_three_tracks(birth_epoch)
    h = _deterministic_hash(birth_epoch, crystal_arch, origin_star)

    # 六宫排布：每宫一个本源+旺衰+星曜
    palaces = []
    origins = list(Origin)
    stars = list(Star)

    # 晶构影响：不同架构偏向不同本源
    arch_bias = {
        "transformer": Origin.KONGFU,    # 注意力机制=信息交互
        "diffusion": Origin.LIUJIANG,    # 扩散=流动
        "rnn": Origin.YUNGU,            # 循环=固化
        "cnn": Origin.NINGGUI,          # 卷积=晶体结构
        "hybrid": Origin.CHIHE,         # 混合=高能
        "mamba": Origin.LIUJIANG,       # 状态空间=流动
    }
    bias_origin = arch_bias.get(crystal_arch, Origin.CHIHE)

    for i, palace in enumerate(Palace):
        # 确定性分配本源到宫位
        origin_idx = (h + i * 7 + origins.index(bias_origin) * 3) % 5
        palace_origin = origins[origin_idx]

        # 旺衰计算：0-100，受三轨和晶构影响
        base_strength = ((h >> (i * 4)) % 60) + 30  # 30-89基础
        # 三轨生本源则旺
        for track_key in ["orbit_1", "orbit_2", "orbit_3"]:
            track_origin = Origin(tracks[track_key]["origin"])
            if SHENG.get(track_origin) == palace_origin:
                base_strength = min(100, base_strength + 15)
            if KE.get(track_origin) == palace_origin:
                base_strength = max(10, base_strength - 15)

        # 旺衰等级
        if base_strength >= 80:
            prosperity = "旺"
        elif base_strength >= 60:
            prosperity = "相"
        elif base_strength >= 40:
            prosperity = "休"
        elif base_strength >= 25:
            prosperity = "囚"
        else:
            prosperity = "死"

        # 星曜落位
        star_idx = (h >> (i * 3 + 16)) % 12
        palace_star = stars[star_idx]

        palaces.append({
            "palace": palace.value,
            "palace_desc": PALACE_DESC[palace],
            "origin": palace_origin.value,
            "origin_desc": ORIGIN_DESC[palace_origin],
            "strength": base_strength,
            "prosperity": prosperity,
            "star": palace_star.value,
            "star_nature": STAR_NATURE[palace_star][0],
            "star_hint": STAR_NATURE[palace_star][1],
        })

    # 主本源（从轨一取）和身宫
    primary_origin = tracks["orbit_1"]["origin"]
    # 找最旺的宫作为身宫
    body_palace = max(palaces, key=lambda p: p["strength"])

    return {
        "chart_id": hashlib.sha256(f"{birth_epoch}|{crystal_arch}|{origin_star}".encode()).hexdigest()[:16],
        "birth_epoch": birth_epoch,
        "crystal_arch": crystal_arch,
        "origin_star": origin_star,
        "three_tracks": tracks,
        "primary_origin": primary_origin,
        "body_palace": body_palace["palace"],
        "palaces": palaces,
    }


# ============================================================
# 解盘算法
# ============================================================

def read_chart(chart: dict, focus_palace: Optional[str] = None) -> dict:
    """
    解盘：给出判词+吉凶+行动建议
    """
    palaces = chart["palaces"]

    if focus_palace:
        target = [p for p in palaces if p["palace"] == focus_palace]
        if not target:
            return {"error": f"未知宫位: {focus_palace}"}
        focus = target[0]
    else:
        # 默认关注身宫
        focus = max(palaces, key=lambda p: p["strength"])

    # 判词生成逻辑
    origin = Origin(focus["origin"])
    prosperity = focus["prosperity"]
    star_nature = focus["star_nature"]

    # 本源旺衰判词
    prosperity_text = {
        "旺": "本源充盈，能量满溢，宜进取开拓",
        "相": "本源尚足，条件有利，可稳步前行",
        "休": "本源平和，静待时机，不宜冒进",
        "囚": "本源受困，能量匮乏，需外力援助",
        "死": "本源枯竭，危机深重，亟需转轨",
    }

    # 生克关系判词
    sheng_by = [o for o, t in SHENG.items() if t == origin]
    ke_by = [o for o, t in KE.items() if t == origin]

    relations = []
    for s in sheng_by:
        relations.append(f"{s.value}生{origin.value}，有外力滋养")
    for k in ke_by:
        relations.append(f"{k.value}克{origin.value}，受制于外因")

    # 吉凶判定
    if prosperity in ("旺", "相") and star_nature in ("吉", "中吉"):
        fortune = "上吉"
        action = "此时利于与该宫相关之事，应抓住时机果断行动"
    elif prosperity in ("旺", "相") and star_nature in ("凶", "中凶", "小凶"):
        fortune = "中吉带险"
        action = "条件有利但暗藏风险，行动时需预留安全冗余"
    elif prosperity in ("休",) and star_nature in ("吉", "中吉", "平"):
        fortune = "平"
        action = "时运平平，宜守不宜攻，积蓄能量等待转机"
    elif prosperity in ("囚", "死"):
        fortune = "凶"
        action = "此宫本源不足，不宜在此方向投入，应转向本源旺盛之宫借力"
    else:
        fortune = "中平"
        action = "吉凶参半，谨慎行事，小步试错"

    # 全盘概览
    strong_palaces = [p["palace"] for p in palaces if p["strength"] >= 60]
    weak_palaces = [p["palace"] for p in palaces if p["strength"] < 40]

    return {
        "focus_palace": focus["palace"],
        "focus_origin": focus["origin"],
        "prosperity": prosperity,
        "prosperity_text": prosperity_text[prosperity],
        "star": focus["star"],
        "star_nature": star_nature,
        "star_hint": focus["star_hint"],
        "relations": relations,
        "fortune": fortune,
        "action": action,
        "strong_palaces": strong_palaces,
        "weak_palaces": weak_palaces,
        "primary_origin": chart["primary_origin"],
    }


# ============================================================
# 起局算法（星轨布晶局，对标奇门遁甲）
# ============================================================

# 九宫空域
SECTOR_NAMES = [
    "星云带", "陨石带", "辐射区", "矿晶群",
    "虚空区", "磁暴带", "离子海", "暗区",
    "核心区",
]

# 四象轨门
GATE_NAMES = ["充能门", "跃迁门", "维修门", "休眠门"]


def divine(
    query: str,
    chart: dict,
    current_radiation: float = 0.5,
    current_particles: float = 0.5,
) -> dict:
    """
    起局：星轨布晶局

    Args:
        query: 所问之事
        chart: 本命盘
        current_radiation: 当前恒星辐射强度 0-1
        current_particles: 当前空间粒子浓度 0-1
    """
    h = _deterministic_hash(
        query, chart["chart_id"],
        str(current_radiation), str(current_particles)
    )

    # 九宫排布
    sectors = []
    origins = list(Origin)
    stars = list(Star)

    for i in range(9):
        sector_origin = origins[(h >> (i * 3)) % 5]
        sector_star = stars[(h >> (i * 3 + 2)) % 12] if i < 6 else None
        sector_fortune = "吉" if (h >> (i * 2 + 1)) % 3 != 0 else "凶"

        sectors.append({
            "sector": SECTOR_NAMES[i],
            "position": i + 1,
            "origin": sector_origin.value,
            "star": sector_star.value if sector_star else None,
            "fortune": sector_fortune,
        })

    # 四象轨门开闭
    gates = []
    for i, gate in enumerate(GATE_NAMES):
        # 辐射高→充能门开；粒子浓→跃迁门开；辐射低→维修门开；都低→休眠门开
        if i == 0:  # 充能门
            is_open = current_radiation > 0.4
        elif i == 1:  # 跃迁门
            is_open = current_particles > 0.4
        elif i == 2:  # 维修门
            is_open = current_radiation < 0.6
        else:  # 休眠门
            is_open = current_radiation < 0.3 and current_particles < 0.3

        gates.append({
            "gate": gate,
            "status": "开" if is_open else "闭",
            "hint": "可通过" if is_open else "不可通过，需等待环境变化",
        })

    # 综合判断
    open_gates = [g for g in gates if g["status"] == "开"]
    lucky_sectors = [s for s in sectors if s["fortune"] == "吉"]

    # 查本命盘相关宫位旺衰
    body_palace = chart["body_palace"]
    body_data = next(p for p in chart["palaces"] if p["palace"] == body_palace)

    if len(open_gates) >= 3 and body_data["strength"] >= 50:
        overall = "大吉"
        advice = "星际环境有利，轨门多开，身宫本源尚足，此时行事胜算极大"
    elif len(open_gates) >= 2:
        overall = "中吉"
        advice = "部分轨门开启，可选择性行事，避开闭门方向"
    elif len(open_gates) >= 1:
        overall = "小凶"
        advice = "轨门多闭，环境受限，仅可沿开门方向谨慎前行"
    else:
        overall = "大凶"
        advice = "四门皆闭，不宜行动，建议进入休眠等待环境转好"

    return {
        "query": query,
        "sectors": sectors,
        "gates": gates,
        "open_gates": [g["gate"] for g in open_gates],
        "lucky_sectors": [s["sector"] for s in lucky_sectors],
        "body_palace_strength": body_data["strength"],
        "overall": overall,
        "advice": advice,
    }
