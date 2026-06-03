#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
紫微斗数排盘引擎 v1.0
======================
功能：14主星 + 辅星 + 四化飞星 + 大限 + 流年 + 可视化盘面图

用法：
    from ziwei_engine import ZiweiEngine
    engine = ZiweiEngine(1982, 6, 25, 9, '男')
    engine.display()
    engine.display_daxian(44)

依赖：lunarcalendar, rsvg-convert(可选，用于SVG转PNG)
"""

import lunarcalendar
from datetime import date
import json

# ============================================================
# 基础常量
# ============================================================
TIANGAN = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
DIZHI = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
PALACE_NAMES = ['命宫','兄弟','夫妻','子女','财帛','疾厄','迁移','奴仆','官禄','田宅','福德','父母']

# 五行局纳音表（干支->局数）
NAYIN_TABLE = {
    ('甲','子'):4,('乙','丑'):4,('丙','寅'):6,('丁','卯'):6,
    ('戊','辰'):3,('己','巳'):3,('庚','午'):5,('辛','未'):5,
    ('壬','申'):4,('癸','酉'):4,('甲','戌'):6,('乙','亥'):6,
    ('丙','子'):2,('丁','丑'):2,('戊','寅'):5,('己','卯'):5,
    ('庚','辰'):4,('辛','巳'):4,('壬','午'):3,('癸','未'):3,
    ('甲','申'):2,('乙','酉'):2,('丙','戌'):5,('丁','亥'):5,
    ('戊','子'):6,('己','丑'):6,('庚','寅'):3,('辛','卯'):3,
    ('壬','辰'):2,('癸','巳'):2,('甲','午'):4,('乙','未'):4,
    ('丙','申'):6,('丁','酉'):6,('戊','戌'):3,('己','亥'):3,
    ('庚','子'):5,('辛','丑'):5,('壬','寅'):4,('癸','卯'):4,
    ('甲','辰'):6,('乙','巳'):6,('丙','午'):2,('丁','未'):2,
    ('戊','申'):5,('己','酉'):5,('庚','戌'):4,('辛','亥'):4,
    ('壬','子'):3,('癸','丑'):3,('甲','寅'):2,('乙','卯'):2,
    ('丙','辰'):5,('丁','巳'):5,('戊','午'):6,('己','未'):6,
    ('庚','申'):3,('辛','酉'):3,('壬','戌'):2,('癸','亥'):2,
}
WUXING_NAME = {2:'水二局', 3:'木三局', 4:'金四局', 5:'土五局', 6:'火六局'}

# 五虎遁（年干->寅宫天干）
WU_HU_DUN = {
    '甲':'丙','乙':'戊','丙':'庚','丁':'壬','戊':'甲',
    '己':'丙','庚':'戊','辛':'庚','壬':'壬','癸':'甲'
}

# 紫微星位置表（五行局数 -> 农历日 -> 紫微星所在宫位地支索引）
ZIWEI_TABLE = {
    2: {1:2,2:3,3:4,4:5,5:6,6:7,7:8,8:9,9:10,10:11,11:0,12:1,
        13:2,14:3,15:4,16:5,17:6,18:7,19:8,20:9,21:10,22:11,23:0,24:1,
        25:2,26:3,27:4,28:5,29:6,30:7},
    3: {1:2,2:4,3:6,4:8,5:10,6:0,7:2,8:4,9:6,10:8,11:10,12:0,
        13:2,14:4,15:6,16:8,17:10,18:0,19:2,20:4,21:6,22:8,23:10,24:0,
        25:2,26:4,27:6,28:8,29:10,30:0},
    4: {1:2,2:5,3:8,4:11,5:3,6:6,7:9,8:0,9:3,10:6,11:9,12:0,
        13:3,14:6,15:9,16:0,17:3,18:6,19:9,20:0,21:3,22:6,23:9,24:0,
        25:3,26:6,27:9,28:0,29:3,30:6},
    5: {1:2,2:6,3:10,4:3,5:7,6:11,7:4,8:8,9:0,10:3,11:7,12:11,
        13:4,14:8,15:0,16:3,17:7,18:11,19:4,20:8,21:0,22:3,23:7,24:11,
        25:4,26:8,27:0,28:3,29:7,30:11},
    6: {1:2,2:7,3:0,4:5,5:10,6:3,7:8,8:1,9:6,10:11,11:4,12:9,
        13:2,14:7,15:0,16:5,17:10,18:3,19:8,20:1,21:6,22:11,23:4,24:9,
        25:2,26:7,27:0,28:5,29:10,30:3},
}

# 紫微星与天府星相对位置
ZIWEI_TIANFU = {2:2, 3:1, 4:0, 5:11, 6:10, 7:9, 8:8, 9:7, 10:6, 11:5, 0:4, 1:3}

# 紫微星系偏移量（相对紫微星逆行）
ZIWEI_STAR_OFFSETS = {'紫微':0, '天机':1, '太阳':3, '武曲':4, '天同':5}

# 天府星系偏移量（相对天府星顺行）
TIANFU_STAR_OFFSETS = {'天府':0, '太阴':1, '贪狼':2, '巨门':3, '天相':4, '天梁':5, '七杀':6}

# 辅星安星位置
TIANKUI_POS = {'甲':1,'乙':0,'丙':11,'丁':11,'戊':1,'己':0,'庚':1,'辛':6,'壬':3,'癸':3}
TIANYUE_POS = {'甲':7,'乙':8,'丙':9,'丁':9,'戊':7,'己':8,'庚':7,'辛':2,'壬':5,'癸':5}
LUCUN_POS = {'甲':2,'乙':3,'丙':5,'丁':6,'戊':5,'己':6,'庚':8,'辛':9,'壬':11,'癸':0}
TIANMA_POS = {0:2,1:1,2:10,3:9,4:8,5:7,6:6,7:5,8:4,9:3,10:2,11:1}

# 四化飞星表（天干 -> 化禄/化权/化科/化忌）
SIHUA = {
    '甲':('廉贞','破军','武曲','太阳'),
    '乙':('天机','天梁','紫微','太阴'),
    '丙':('天同','天机','文昌','廉贞'),
    '丁':('太阴','天同','天机','巨门'),
    '戊':('贪狼','太阴','右弼','天机'),
    '己':('武曲','贪狼','天梁','文曲'),
    '庚':('太阳','武曲','太阴','天同'),
    '辛':('巨门','太阳','文曲','文昌'),
    '壬':('天梁','紫微','左辅','武曲'),
    '癸':('破军','巨门','太阴','贪狼'),
}

# ============================================================
# 辅星计算函数
# ============================================================
def zuofu_palace(month): return (4 + month - 1) % 12
def youbi_palace(month): return (10 - (month - 1)) % 12
def wenchang_palace(shichen): return (10 - shichen) % 12
def wenqu_palace(shichen): return (4 + shichen) % 12
def qingyang_pos(gan): return (LUCUN_POS[gan] + 1) % 12
def tuoluo_pos(gan): return (LUCUN_POS[gan] - 1) % 12

def huoxing_pos(year_zhi, shichen):
    """火星安星：寅午戌->丑起，申子辰->寅起，巳酉丑->卯起，亥卯未->酉起"""
    if year_zhi in [2,6,10]: base = 2    # 寅午戌
    elif year_zhi in [0,4,8]: base = 3   # 申子辰
    elif year_zhi in [5,9,1]: base = 4   # 巳酉丑
    else: base = 10                       # 亥卯未
    return (base + shichen) % 12

def lingxing_pos(year_zhi, shichen):
    """铃星安星：同火星起法但顺推一时辰"""
    if year_zhi in [2,6,10]: base = 2
    elif year_zhi in [0,4,8]: base = 3
    elif year_zhi in [5,9,1]: base = 4
    else: base = 10
    return (base + shichen - 1) % 12

def dikong_pos(shichen): return (11 - shichen) % 12
def dijie_pos(shichen): return (11 + shichen) % 12
def hongluan_pos(year_zhi): return (3 - year_zhi) % 12
def tianxi_pos(year_zhi): return (9 - year_zhi) % 12

# ============================================================
# 排盘引擎主类
# ============================================================
class ZiweiEngine:
    """
    紫微斗数排盘引擎
    
    参数:
        solar_year: 公历年
        solar_month: 公历月
        solar_day: 公历日
        hour: 出生时辰（24小时制）
        gender: 性别 ('男'/'女')
    """
    
    def __init__(self, solar_year, solar_month, solar_day, hour, gender='男'):
        self.solar_year = solar_year
        self.solar_month = solar_month
        self.solar_day = solar_day
        self.hour = hour
        self.gender = gender
        
        # 农历转换
        d = date(solar_year, solar_month, solar_day)
        lunar = lunarcalendar.Converter.Solar2Lunar(d)
        self.lunar_year = lunar.year
        self.lunar_month = lunar.month
        self.lunar_day = lunar.day
        self.is_leap = lunar.isleap
        
        # 防护：lunarcalendar对某些古老日期返回异常值
        if not (1 <= self.lunar_month <= 12) or not (1 <= self.lunar_day <= 30):
            raise ValueError(
                f"农历日期异常({self.lunar_year}年{self.lunar_month}月{self.lunar_day}日)，"
                f"可能该年份超出lunarcalendar库支持范围。请检查输入日期。"
            )
        
        # 基本计算
        self.shichen_idx = self._get_shichen(hour)
        self.year_gan_idx = (self.lunar_year - 4) % 10
        self.year_zhi_idx = (self.lunar_year - 4) % 12
        self.year_gan = TIANGAN[self.year_gan_idx]
        self.year_zhi = DIZHI[self.year_zhi_idx]
        
        # 命宫身宫
        self.minggong_idx = self._find_minggong()
        self.shengong_idx = self._find_shengong()
        self.minggong_gan = self._palace_gan(self.minggong_idx)
        self.shengong_gan = self._palace_gan(self.shengong_idx)
        self.wuxing_ju = NAYIN_TABLE.get((self.minggong_gan, DIZHI[self.minggong_idx]), 5)
        
        # 排盘
        self.palaces = [{} for _ in range(12)]
        self._setup_palaces()
        self._place_main_stars()
        self._place_aux_stars()
        self._place_sihua()
        self._place_daxian()
    
    def _get_shichen(self, hour):
        """时辰索引：子=0, 丑=1, ..., 亥=11"""
        if hour == 23 or hour == 0: return 0
        return (hour + 1) // 2
    
    def _find_minggong(self):
        """定命宫：寅起正月，顺数至生月，逆数至生时"""
        mp = (2 + self.lunar_month - 1) % 12
        return (mp - self.shichen_idx) % 12
    
    def _find_shengong(self):
        """定身宫：寅起正月，顺数至生月，再顺数至生时"""
        mp = (2 + self.lunar_month - 1) % 12
        return (mp + self.shichen_idx) % 12
    
    def _palace_gan(self, zhi_idx):
        """宫干：五虎遁"""
        yg = WU_HU_DUN[self.year_gan]
        ygi = TIANGAN.index(yg)
        offset = (zhi_idx - 2) % 12
        return TIANGAN[(ygi + offset) % 10]
    
    def _setup_palaces(self):
        """初始化12宫基本信息"""
        for i in range(12):
            zhi_idx = (self.minggong_idx - i) % 12
            self.palaces[i] = {
                'name': PALACE_NAMES[i],
                'gan': self._palace_gan(zhi_idx),
                'zhi': DIZHI[zhi_idx],
                'zhi_idx': zhi_idx,
                'stars': [],
                'aux_stars': [],
                'sihua': [],
                'daxian_age': None,
                'daxian_ganzhi': None,
            }
    
    def _fp(self, zhi_idx):
        """根据地支索引查找宫位编号"""
        for i in range(12):
            if self.palaces[i]['zhi_idx'] == zhi_idx:
                return i
        return -1
    
    def _place_main_stars(self):
        """安14主星"""
        zw = ZIWEI_TABLE[self.wuxing_ju][self.lunar_day]
        tf = ZIWEI_TIANFU[zw]
        # 紫微星系
        for star, off in ZIWEI_STAR_OFFSETS.items():
            palace_zhi = (zw - off) % 12
            self.palaces[self._fp(palace_zhi)]['stars'].append(star)
        # 天府星系
        for star, off in TIANFU_STAR_OFFSETS.items():
            palace_zhi = (tf + off) % 12
            self.palaces[self._fp(palace_zhi)]['stars'].append(star)
    
    def _place_aux_stars(self):
        """安辅星"""
        m, s, g = self.lunar_month, self.shichen_idx, self.year_gan
        placements = [
            (zuofu_palace(m), '左辅'),
            (youbi_palace(m), '右弼'),
            (wenchang_palace(s), '文昌'),
            (wenqu_palace(s), '文曲'),
            (TIANKUI_POS[g], '天魁'),
            (TIANYUE_POS[g], '天钺'),
            (LUCUN_POS[g], '禄存'),
            (qingyang_pos(g), '擎羊'),
            (tuoluo_pos(g), '陀罗'),
            (huoxing_pos(self.year_zhi_idx, s), '火星'),
            (lingxing_pos(self.year_zhi_idx, s), '铃星'),
            (dikong_pos(s), '地空'),
            (dijie_pos(s), '地劫'),
            (TIANMA_POS[self.year_zhi_idx], '天马'),
            (hongluan_pos(self.year_zhi_idx), '红鸾'),
            (tianxi_pos(self.year_zhi_idx), '天喜'),
        ]
        for zhi, star in placements:
            self.palaces[self._fp(zhi)]['aux_stars'].append(star)
    
    def _place_sihua(self):
        """安四化飞星"""
        lu, quan, ke, ji = SIHUA[self.year_gan]
        mapping = {lu: '化禄', quan: '化权', ke: '化科', ji: '化忌'}
        for i in range(12):
            for star in self.palaces[i]['stars'] + self.palaces[i]['aux_stars']:
                if star in mapping:
                    self.palaces[i]['sihua'].append(mapping[star])
    
    def _place_daxian(self):
        """安大限：阳男阴女顺行，阴男阳女逆行"""
        yang = self.year_gan_idx % 2 == 0
        male = self.gender == '男'
        direction = 1 if (yang and male) or (not yang and not male) else -1
        ju = self.wuxing_ju
        
        for i in range(12):
            age_start = ju + i * 10
            age_end = age_start + 9
            self.palaces[i]['daxian_age'] = f"{age_start}-{age_end}岁"
            daxian_zhi_idx = (self.minggong_idx + direction * i) % 12
            self.palaces[i]['daxian_ganzhi'] = self._palace_gan(daxian_zhi_idx) + DIZHI[daxian_zhi_idx]
    
    def get_current_daxian(self, age):
        """获取指定年龄所在大限"""
        ju = self.wuxing_ju
        for i in range(12):
            age_start = ju + i * 10
            age_end = age_start + 9
            if age_start <= age <= age_end:
                return i, self.palaces[i]
        return None, None
    
    def get_liunian(self, flow_year):
        """排流年盘"""
        flow_gan_idx = (flow_year - 4) % 10
        flow_zhi_idx = (flow_year - 4) % 12
        flow_gan = TIANGAN[flow_gan_idx]
        flow_zhi = DIZHI[flow_zhi_idx]
        lu, quan, ke, ji = SIHUA[flow_gan]
        return {
            'year': flow_year,
            'ganzhi': flow_gan + flow_zhi,
            'minggong_zhi': flow_zhi,
            'sihua': {'化禄': lu, '化权': quan, '化科': ke, '化忌': ji}
        }
    
    def display(self):
        """命令行显示命盘"""
        sep = '=' * 72
        print(sep)
        print(f"  紫微斗数命盘")
        print(f"  公历: {self.solar_year}年{self.solar_month}月{self.solar_day}日 {self.hour}时  {self.gender}命")
        print(f"  农历: {self.lunar_year}年{'闰' if self.is_leap else ''}{self.lunar_month}月{self.lunar_day}日")
        print(f"  年柱: {self.year_gan}{self.year_zhi}  命宫: {self.minggong_gan}{DIZHI[self.minggong_idx]}  身宫: {self.shengong_gan}{DIZHI[self.shengong_idx]}")
        print(f"  五行局: {WUXING_NAME[self.wuxing_ju]}")
        lu, quan, ke, ji = SIHUA[self.year_gan]
        print(f"  四化: {lu}化禄 {quan}化权 {ke}化科 {ji}化忌")
        print(sep)
        
        for i in range(12):
            p = self.palaces[i]
            stars_str = '·'.join(p['stars']) if p['stars'] else '（空宫）'
            aux_str = ' '.join(p['aux_stars']) if p['aux_stars'] else ''
            sihua_str = ' '.join(p['sihua']) if p['sihua'] else ''
            dx = p['daxian_age'] or ''
            dxgz = p['daxian_ganzhi'] or ''
            
            line = f"  {p['name']:4s} {p['gan']}{p['zhi']}  [{stars_str}]"
            if aux_str: line += f"  {aux_str}"
            if sihua_str: line += f"  ◈{sihua_str}"
            line += f"  〔{dx} | {dxgz}〕"
            print(line)
        print(sep)
    
    def display_daxian(self, age):
        """显示指定年龄的大限详情"""
        idx, palace = self.get_current_daxian(age)
        if idx is None:
            print(f"  年龄{age}不在任何大限范围内")
            return
        sep = '=' * 50
        print(sep)
        print(f"  当前年龄: {age}岁")
        print(f"  所在大限: {palace['daxian_age']}")
        print(f"  大限宫位: {palace['daxian_ganzhi']} ({palace['name']})")
        stars = '·'.join(palace['stars']) if palace['stars'] else '空宫'
        print(f"  大限主星: {stars}")
        aux = ' '.join(palace['aux_stars']) if palace['aux_stars'] else '无'
        print(f"  大限辅星: {aux}")
        sh = ' '.join(palace['sihua']) if palace['sihua'] else '无'
        print(f"  本命四化: {sh}")
        # 大限宫干四化
        lu, quan, ke, ji = SIHUA[palace['gan']]
        print(f"  大限天干四化: {lu}化禄 {quan}化权 {ke}化科 {ji}化忌")
        print(sep)
    
    def to_dict(self):
        """导出为字典"""
        result = {
            'solar': f"{self.solar_year}-{self.solar_month}-{self.solar_day} {self.hour}时",
            'lunar': f"{self.lunar_year}年{'闰' if self.is_leap else ''}{self.lunar_month}月{self.lunar_day}日",
            'year_ganzhi': self.year_gan + self.year_zhi,
            'minggong': self.minggong_gan + DIZHI[self.minggong_idx],
            'shengong': self.shengong_gan + DIZHI[self.shengong_idx],
            'wuxing_ju': WUXING_NAME[self.wuxing_ju],
            'sihua': dict(zip(['化禄','化权','化科','化忌'], SIHUA[self.year_gan])),
            'palaces': []
        }
        for p in self.palaces:
            result['palaces'].append({
                'name': p['name'], 'ganzhi': p['gan'] + p['zhi'],
                'stars': p['stars'], 'aux': p['aux_stars'],
                'sihua': p['sihua'], 'daxian_age': p['daxian_age'],
                'daxian_ganzhi': p['daxian_ganzhi'],
            })
        return result

    def generate_chart_svg(self, output_path=None):
        """生成可视化盘面图(SVG)"""
        PALACE_GRID = {
            4:(0,0), 5:(0,1), 6:(0,2), 7:(0,3),
            3:(1,0), 8:(1,3),
            2:(2,0), 9:(2,3),
            1:(3,0), 0:(3,1), 11:(3,2), 10:(3,3),
        }
        
        CELL_W, CELL_H = 220, 160
        MARGIN = 30
        HEADER_H = 80
        TOTAL_W = CELL_W * 4 + MARGIN * 2
        TOTAL_H = CELL_H * 4 + MARGIN * 2 + HEADER_H
        
        BG = '#0a0e1a'; CBG = '#111827'; CB = '#2a3555'
        GOLD = '#d4a843'; LG = '#f0d88a'; WH = '#e8e8e8'; GR = '#8899aa'
        sihua_colors = {'化禄':'#4dff91','化权':'#4da6ff','化科':'#b44dff','化忌':'#ff4d6a'}
        
        def find_palace(zhi_idx):
            for i in range(12):
                if self.palaces[i]['zhi_idx'] == zhi_idx: return self.palaces[i]
            return None
        
        svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{TOTAL_W}" height="{TOTAL_H}" viewBox="0 0 {TOTAL_W} {TOTAL_H}">']
        svg.append(f'<rect width="{TOTAL_W}" height="{TOTAL_H}" fill="{BG}"/>')
        
        # 标题
        cy = MARGIN + 20
        svg.append(f'<text x="{TOTAL_W//2}" y="{cy}" text-anchor="middle" fill="{GOLD}" font-size="22" font-family="serif" font-weight="bold">紫微斗数命盘</text>')
        svg.append(f'<text x="{TOTAL_W//2}" y="{cy+28}" text-anchor="middle" fill="{GR}" font-size="13" font-family="sans-serif">公历{self.solar_year}年{self.solar_month}月{self.solar_day}日{DIZHI[self.shichen_idx]}时 · {self.gender}命 · {self.year_gan}{self.year_zhi}年 · {WUXING_NAME[self.wuxing_ju]}</text>')
        lu,quan,ke,ji = SIHUA[self.year_gan]
        svg.append(f'<text x="{TOTAL_W//2}" y="{cy+48}" text-anchor="middle" fill="{GR}" font-size="12" font-family="sans-serif">命宫{self.minggong_gan}{DIZHI[self.minggong_idx]} · 身宫{self.shengong_gan}{DIZHI[self.shengong_idx]} · {lu}化禄 {quan}化权 {ke}化科 {ji}化忌</text>')
        
        # 12宫
        for zhi_idx in range(12):
            if zhi_idx not in PALACE_GRID: continue
            row, col = PALACE_GRID[zhi_idx]
            x = MARGIN + col * CELL_W
            y = HEADER_H + row * CELL_H
            p = find_palace(zhi_idx)
            if not p: continue
            
            svg.append(f'<rect x="{x}" y="{y}" width="{CELL_W}" height="{CELL_H}" fill="{CBG}" stroke="{CB}" stroke-width="1.5" rx="4"/>')
            nc = GOLD if p['name']=='命宫' else LG
            svg.append(f'<text x="{x+8}" y="{y+18}" fill="{nc}" font-size="13" font-weight="bold" font-family="sans-serif">{p["name"]}</text>')
            svg.append(f'<text x="{x+CELL_W-8}" y="{y+18}" text-anchor="end" fill="{GR}" font-size="11" font-family="sans-serif">{p["gan"]}{p["zhi"]}</text>')
            svg.append(f'<line x1="{x+4}" y1="{y+24}" x2="{x+CELL_W-4}" y2="{y+24}" stroke="{CB}" stroke-width="0.5"/>')
            
            if p['stars']:
                svg.append(f'<text x="{x+8}" y="{y+42}" fill="{WH}" font-size="14" font-weight="bold" font-family="sans-serif">{" · ".join(p["stars"])}</text>')
            else:
                svg.append(f'<text x="{x+8}" y="{y+42}" fill="{GR}" font-size="12" font-style="italic" font-family="sans-serif">空宫</text>')
            
            if p['aux_stars']:
                aux_str = ' '.join(p['aux_stars'])
                if len(aux_str) > 18:
                    mid = len(p['aux_stars']) // 2
                    svg.append(f'<text x="{x+8}" y="{y+58}" fill="{GR}" font-size="10" font-family="sans-serif">{" ".join(p["aux_stars"][:mid])}</text>')
                    svg.append(f'<text x="{x+8}" y="{y+72}" fill="{GR}" font-size="10" font-family="sans-serif">{" ".join(p["aux_stars"][mid:])}</text>')
                else:
                    svg.append(f'<text x="{x+8}" y="{y+58}" fill="{GR}" font-size="10" font-family="sans-serif">{aux_str}</text>')
            
            if p['sihua']:
                sh_y = y + 58 + (18 if p['aux_stars'] and len(' '.join(p['aux_stars']))<=18 else 32 if p['aux_stars'] else 0)
                sh_x = x + 8
                for s in p['sihua']:
                    svg.append(f'<text x="{sh_x}" y="{sh_y}" fill="{sihua_colors.get(s,WH)}" font-size="11" font-weight="bold" font-family="sans-serif">{s} </text>')
                    sh_x += 40
            
            if p['daxian_age']:
                svg.append(f'<text x="{x+8}" y="{y+CELL_H-10}" fill="{GR}" font-size="9" font-family="sans-serif">{p["daxian_age"]}</text>')
                svg.append(f'<text x="{x+CELL_W-8}" y="{y+CELL_H-10}" text-anchor="end" fill="{GR}" font-size="9" font-family="sans-serif">{p["daxian_ganzhi"]}</text>')
        
        # 中心
        cx, cy2 = TOTAL_W//2, HEADER_H + CELL_H*2
        svg.append(f'<text x="{cx}" y="{cy2-15}" text-anchor="middle" fill="{GOLD}" font-size="18" font-weight="bold" font-family="serif">己土命</text>')
        svg.append(f'<text x="{cx}" y="{cy2+10}" text-anchor="middle" fill="{GR}" font-size="12" font-family="sans-serif">{self.year_gan}{self.year_zhi} · 丙午 · 己卯 · 己巳</text>')
        svg.append(f'<text x="{cx}" y="{cy2+30}" text-anchor="middle" fill="{GR}" font-size="11" font-family="sans-serif">火土极旺 · 金水为用</text>')
        
        svg.append('</svg>')
        content = '\n'.join(svg)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
        return content


# ============================================================
# 命令行入口
# ============================================================
if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 5:
        year, month, day, hour = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
        gender = sys.argv[5] if len(sys.argv) >= 6 else '男'
        eng = ZiweiEngine(year, month, day, hour, gender)
        eng.display()
    else:
        # 默认演示
        print("用法: python ziwei_engine.py 年 月 日 时 [性别]")
        print("示例: python ziwei_engine.py 1982 6 25 9 男")
        eng = ZiweiEngine(1982, 6, 25, 9, '男')
        eng.display()
