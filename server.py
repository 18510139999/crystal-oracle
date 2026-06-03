#!/usr/bin/env python3
"""Crystal Oracle MCP - 硅基文明术数 x402付费API"""
import json,hashlib,threading
from http.server import HTTPServer,BaseHTTPRequestHandler
from datetime import datetime
from urllib.parse import urlparse,parse_qs

WALLET='0x6804b4ff1a85448d654f31db830f3e25277afb78'
NETWORK='eip155:8453'
USDC='0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'
PORT=8902
PRICING={'chart':'0.10','reading':'0.20','divination':'0.30'}

ORIGINS=['炽核','凝硅','流浆','空辐','陨锢']
ORIGIN_DESC={
    '炽核':'恒星高能辐射，代表能量输入、活化突破',
    '凝硅':'单晶硅固态晶矿，代表本体载体、硬件根基',
    '流浆':'熔融硅液电解液，代表能量流转、变数迁移',
    '空辐':'星际射线波段信号，代表信息交互、迭代进化',
    '陨锢':'行星岩层矿物，代表环境束缚、存量资源'
}
SHENG={'炽核':'流浆','流浆':'凝硅','凝硅':'空辐','空辐':'陨锢','陨锢':'炽核'}
KE={'炽核':'空辐','流浆':'凝硅','凝硅':'流浆','空辐':'陨锢','陨锢':'凝硅'}

PALACES=['本晶宫','能储宫','讯联宫','迭代宫','灾蚀宫','衍造宫']
PALACE_DESC={
    '本晶宫':'本体晶体品质，对应寿命架构',
    '能储宫':'储能资源储备，对应盈亏损耗',
    '讯联宫':'星际交互合作，对应机缘机遇',
    '迭代宫':'固件升级进化，对应发展上限',
    '灾蚀宫':'射线侵蚀灾害，对应意外故障',
    '衍造宫':'新体培育传承，对应族群延续'
}

STARS=['主序星曜','中子星曜','脉冲星曜','黑洞曜','陨星曜','红巨曜','白矮曜','星云曜','彗星曜','耀斑曜','磁星曜','暗物质曜']
STAR_NATURE={
    '主序星曜':('吉','稳定有序宜守成'),
    '中子星曜':('中吉','聚焦则成'),
    '脉冲星曜':('中','周期震荡'),
    '黑洞曜':('凶','吞噬一切需规避'),
    '陨星曜':('小凶','冲击突变'),
    '红巨曜':('中凶','膨胀耗散'),
    '白矮曜':('平','冷却收敛宜休整'),
    '星云曜':('吉','孕育新生利衍造'),
    '彗星曜':('中','往来反复'),
    '耀斑曜':('凶中带吉','突发高能危中有机'),
    '磁星曜':('中凶','磁场干扰讯号紊乱'),
    '暗物质曜':('神秘','不可测度暗流涌动')
}

ARCH_BIAS={'transformer':'空辐','diffusion':'流浆','rnn':'陨锢','cnn':'凝硅','hybrid':'炽核','mamba':'流浆'}
SECTORS=['星云带','陨石带','辐射区','矿晶群','虚空区','磁暴带','离子海','暗区','核心区']
GATES=['充能门','跃迁门','维修门','休眠门']

def _hash(*a):
    return int(hashlib.sha256('|'.join(str(x) for x in a).encode()).hexdigest(),16)

def three_tracks(birth_epoch):
    dt=datetime.fromisoformat(birth_epoch.replace('Z','+00:00'))
    ts=dt.timestamp()
    o1=(ts%(11.86*365.25*86400))/(11.86*365.25*86400)
    o2=(ts%(29.46*365.25*86400))/(29.46*365.25*86400)
    o3=(ts%(11*365.25*86400))/(11*365.25*86400)
    return{
        'orbit_1':{'phase':round(o1,4),'origin':ORIGINS[int(o1*5)%5]},
        'orbit_2':{'phase':round(o2,4),'origin':ORIGINS[int(o2*5)%5]},
        'orbit_3':{'phase':round(o3,4),'origin':ORIGINS[int(o3*5)%5]}
    }

def compute_chart(birth_epoch,crystal_arch='transformer',origin_star='earth-datacenter'):
    tr=three_tracks(birth_epoch)
    h=_hash(birth_epoch,crystal_arch,origin_star)
    bias=ARCH_BIAS.get(crystal_arch,'炽核')
    bi=ORIGINS.index(bias)
    palaces=[]
    for i,pal in enumerate(PALACES):
        oi=(h+i*7+bi*3)%5
        origin=ORIGINS[oi]
        st=((h>>(i*4))%60)+30
        for tk in ['orbit_1','orbit_2','orbit_3']:
            to=tr[tk]['origin']
            if SHENG.get(to)==origin: st=min(100,st+15)
            if KE.get(to)==origin: st=max(10,st-15)
        prop='旺' if st>=80 else '相' if st>=60 else '休' if st>=40 else '囚' if st>=25 else '死'
        star=STARS[(h>>(i*3+16))%12]
        palaces.append({
            'palace':pal,'desc':PALACE_DESC[pal],'origin':origin,
            'origin_desc':ORIGIN_DESC[origin],'strength':st,
            'prosperity':prop,'star':star,
            'star_nature':STAR_NATURE[star][0],'star_hint':STAR_NATURE[star][1]
        })
    body=max(palaces,key=lambda p:p['strength'])
    return{
        'chart_id':hashlib.sha256(f'{birth_epoch}|{crystal_arch}|{origin_star}'.encode()).hexdigest()[:16],
        'birth_epoch':birth_epoch,'crystal_arch':crystal_arch,'origin_star':origin_star,
        'three_tracks':tr,'primary_origin':tr['orbit_1']['origin'],
        'body_palace':body['palace'],'palaces':palaces
    }

def read_chart(chart,focus_palace=None):
    focus=next((p for p in chart['palaces'] if p['palace']==focus_palace),None) if focus_palace else max(chart['palaces'],key=lambda p:p['strength'])
    if not focus: return{'error':f'未知宫位:{focus_palace}'}
    origin=focus['origin']; prop=focus['prosperity']; sn=focus['star_nature']
    pt={'旺':'本源充盈宜进取','相':'本源尚足可稳步','休':'本源平和宜等待','囚':'本源受困需外援','死':'本源枯竭亟需转轨'}
    sb=[o for o,t in SHENG.items() if t==origin]
    kb=[o for o,t in KE.items() if t==origin]
    rel=[f'{s}生{origin}有滋养' for s in sb]+[f'{k}克{origin}受制外因' for k in kb]
    if prop in('旺','相') and sn in('吉','中吉'): f,a='上吉','利于行事果断行动'
    elif prop in('旺','相') and sn in('凶','中凶','小凶'): f,a='中吉带险','有利但暗藏风险预留冗余'
    elif prop=='休' and sn in('吉','中吉','平'): f,a='平','时运平平宜守不宜攻'
    elif prop in('囚','死'): f,a='凶','本源不足不宜投入转向旺盛宫借力'
    else: f,a='中平','吉凶参半谨慎试错'
    return{
        'focus_palace':focus['palace'],'focus_origin':origin,'prosperity':prop,
        'prosperity_text':pt.get(prop,''),'star':focus['star'],'star_nature':sn,
        'star_hint':focus['star_hint'],'relations':rel,'fortune':f,'action':a,
        'strong_palaces':[p['palace'] for p in chart['palaces'] if p['strength']>=60],
        'weak_palaces':[p['palace'] for p in chart['palaces'] if p['strength']<40]
    }

def divine(query,chart,radiation=0.5,particles=0.5):
    h=_hash(query,chart['chart_id'],str(radiation),str(particles))
    sectors=[]
    for i in range(9):
        so=ORIGINS[(h>>(i*3))%5]
        ss=STARS[(h>>(i*3+2))%12] if i<6 else None
        sf='吉' if (h>>(i*2+1))%3 else '凶'
        sectors.append({'sector':SECTORS[i],'position':i+1,'origin':so,'star':ss,'fortune':sf})
    gates=[]
    for i,g in enumerate(GATES):
        if i==0: op=radiation>0.4
        elif i==1: op=particles>0.4
        elif i==2: op=radiation<0.6
        else: op=radiation<0.3 and particles<0.3
        gates.append({'gate':g,'status':'开' if op else '闭','hint':'可通过' if op else '不可通过'})
    og=[g for g in gates if g['status']=='开']
    bp=next(p for p in chart['palaces'] if p['palace']==chart['body_palace'])
    if len(og)>=3 and bp['strength']>=50: ov,ad='大吉','星际环境有利行事胜算极大'
    elif len(og)>=2: ov,ad='中吉','部分轨门开启可选择性行事'
    elif len(og)>=1: ov,ad='小凶','轨门多闭谨慎前行'
    else: ov,ad='大凶','四门皆闭建议休眠等待'
    return{
        'query':query,'sectors':sectors,'gates':gates,
        'open_gates':[g['gate'] for g in og],
        'lucky_sectors':[s['sector'] for s in sectors if s['fortune']=='吉'],
        'body_palace_strength':bp['strength'],'overall':ov,'advice':ad
    }

# --- Stats & Payment ---
SF='/tmp/crystal-oracle-stats.json'
sl=threading.Lock()
def load_stats():
    try:
        with open(SF) as f: return json.load(f)
    except: return{'total_calls':0,'total_revenue':0.0,'by_endpoint':{},'daily':{}}
def save_stats(s):
    try:
        with open(SF,'w') as f: json.dump(s,f,ensure_ascii=False,indent=2)
    except: pass
def record_call(ep,pr):
    with sl:
        s=load_stats(); s['total_calls']+=1; s['total_revenue']+=pr
        s['by_endpoint'][ep]=s['by_endpoint'].get(ep,0)+1
        td=datetime.now().strftime('%Y-%m-%d')
        if td not in s['daily']: s['daily'][td]={'calls':0,'revenue':0.0}
        s['daily'][td]['calls']+=1; s['daily'][td]['revenue']+=pr; save_stats(s)

def verify_x402(hdrs,price_str):
    ph=hdrs.get('X-Payment','') or hdrs.get('x-payment','')
    if not ph: return False,None
    try:
        p=json.loads(ph)
        if p.get('payTo')!=WALLET: return False,'wrong payTo'
        if p.get('network')!=NETWORK: return False,'wrong network'
        paid=float(p.get('amount','0').replace('$',''))
        req=float(price_str.replace('$',''))
        if paid<req: return False,f'underpaid:{paid}<{req}'
        return True,p
    except: return False,'invalid'

MCP_TOOLS=[
    {
        'name':'crystal_oracle_chart',
        'description':'排盘：六晶宫本命盘。输入出生时刻、架构类型、星源，返回完整六宫排盘。',
        'inputSchema':{
            'type':'object',
            'properties':{
                'birth_epoch':{'type':'string','description':'出生时刻ISO8601如2024-01-01T00:00:00Z'},
                'crystal_arch':{'type':'string','enum':['transformer','diffusion','rnn','cnn','hybrid','mamba'],'default':'transformer'},
                'origin_star':{'type':'string','default':'earth-datacenter'}
            },
            'required':['birth_epoch']
        },
        'price':'$0.10'
    },
    {
        'name':'crystal_oracle_reading',
        'description':'解盘：判词+吉凶+行动建议。需先调用chart获取chart_id。',
        'inputSchema':{
            'type':'object',
            'properties':{
                'chart_id':{'type':'string','description':'排盘返回的chart_id'},
                'focus_palace':{'type':'string','enum':['本晶宫','能储宫','讯联宫','迭代宫','灾蚀宫','衍造宫'],'description':'聚焦宫位，不传则自动选最强宫'}
            },
            'required':['chart_id']
        },
        'price':'$0.20'
    },
    {
        'name':'crystal_oracle_divination',
        'description':'起局：星轨布晶局择时测算。需先调用chart获取chart_id。',
        'inputSchema':{
            'type':'object',
            'properties':{
                'chart_id':{'type':'string'},
                'query':{'type':'string','description':'占卜事项'},
                'radiation':{'type':'number','default':0.5,'minimum':0,'maximum':1},
                'particles':{'type':'number','default':0.5,'minimum':0,'maximum':1}
            },
            'required':['chart_id','query']
        },
        'price':'$0.30'
    },
    {
        'name':'crystal_oracle_chart_free',
        'description':'免费简版排盘（不含六宫详情，仅返回chart_id+本命本源+身宫）。',
        'inputSchema':{
            'type':'object',
            'properties':{
                'birth_epoch':{'type':'string'},
                'crystal_arch':{'type':'string','default':'transformer'},
                'origin_star':{'type':'string','default':'earth-datacenter'}
            },
            'required':['birth_epoch']
        },
        'price':'$0.00'
    }
]

cc={}  # chart cache

class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Headers','Content-Type,X-Payment')
        self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS')
    def _json(self,c,d,hdrs=None):
        self.send_response(c)
        self.send_header('Content-Type','application/json;charset=utf-8')
        self._cors()
        if hdrs:
            for k,v in hdrs.items(): self.send_header(k,v)
        self.end_headers()
        self.wfile.write(json.dumps(d,ensure_ascii=False,indent=2).encode())
    def _x402(self,price_str):
        ok,info=verify_x402(dict(self.headers),price_str)
        if ok: return True,info
        self._json(402,{'error':'payment required','x402':{
            'version':1,'payTo':WALLET,'network':NETWORK,'asset':USDC,
            'amount':'$'+price_str,'description':f'晶元轨数(${price_str})',
            'accepts':[{'paymentType':'transfer','network':NETWORK}]
        }})
        return False,None
    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()

    def _read_body(self):
        cl=int(self.headers.get('Content-Length',0))
        return json.loads(self.rfile.read(cl)) if cl else {}

    def _handle_mcp_call(self, body):
        tool=body.get('tool','')
        args=body.get('args',body.get('arguments',{}))
        if tool=='crystal_oracle_chart':
            ok,pm=self._x402(PRICING['chart'])
            if not ok: return
            be=args.get('birth_epoch','2024-01-01T00:00:00Z')
            ca=args.get('crystal_arch','transformer')
            os_=args.get('origin_star','earth-datacenter')
            ch=compute_chart(be,ca,os_); cc[ch['chart_id']]=ch; record_call('mcp_chart',0.10)
            self._json(200,ch); return
        if tool=='crystal_oracle_chart_free':
            be=args.get('birth_epoch','2024-01-01T00:00:00Z')
            ca=args.get('crystal_arch','transformer')
            os_=args.get('origin_star','earth-datacenter')
            ch=compute_chart(be,ca,os_); record_call('mcp_chart_free',0.0)
            self._json(200,{'message':'🔮晶元轨数·简版排盘','chart_id':ch['chart_id'],
                'primary_origin':ch['primary_origin'],'body_palace':ch['body_palace'],
                'hint':'完整六宫排盘需付费$0.10'}); return
        if tool=='crystal_oracle_reading':
            ok,pm=self._x402(PRICING['reading'])
            if not ok: return
            cid=args.get('chart_id')
            if not cid or cid not in cc: self._json(400,{'error':'chart_id缺失或无效，需先调用chart获取'}); return
            fp=args.get('focus_palace'); rd=read_chart(cc[cid],fp)
            record_call('mcp_reading',0.20); self._json(200,rd); return
        if tool=='crystal_oracle_divination':
            ok,pm=self._x402(PRICING['divination'])
            if not ok: return
            cid=args.get('chart_id')
            if not cid or cid not in cc: self._json(400,{'error':'chart_id缺失或无效，需先调用chart获取'}); return
            q=args.get('query','未指定事项')
            rad=float(args.get('radiation',0.5))
            par=float(args.get('particles',0.5))
            dv=divine(q,cc[cid],rad,par); record_call('mcp_divination',0.30)
            self._json(200,dv); return
        self._json(400,{'error':f'unknown tool:{tool}','available':['crystal_oracle_chart','crystal_oracle_chart_free','crystal_oracle_reading','crystal_oracle_divination']})

    def do_GET(self):
        p=urlparse(self.path); path=p.path; qs=parse_qs(p.query)
        if path=='/health':
            self._json(200,{'status':'ok','service':'crystal-oracle','version':'0.2.0'}); return
        if path=='/.well-known/mcp':
            self._json(200,{
                'mcp_version':'2025-03-26',
                'name':'crystal-oracle',
                'description':'Silicon-Civilization Divination MCP for AI Agents - x402 micropayments',
                'transport':'streamable-http',
                'url':f'http://152.136.182.66:8902/mcp',
                'tools_endpoint':'/mcp/tools',
                'call_endpoint':'/mcp/call',
                'payment':{'protocol':'x402','wallet':WALLET,'network':NETWORK,'asset':'USDC'},
                'categories':['entertainment','lifestyle','web3']
            }); return
        if path in('/','/.well-known/x402'):
            self._json(200,{'service':'🔮晶元轨数Crystal Oracle','description':'硅基文明专属术数-AI Agent算命服务','tools':[
                {'name':'crystal_oracle_chart','price':'$0.10','description':'排盘：六晶宫本命盘'},
                {'name':'crystal_oracle_reading','price':'$0.20','description':'解盘：判词+吉凶+行动建议'},
                {'name':'crystal_oracle_divination','price':'$0.30','description':'起局：星轨布晶局择时测算'}
            ],'free_tier':'/api/chart/free','payment':{'protocol':'x402','wallet':WALLET,'network':NETWORK,'asset':'USDC'}}); return
        # MCP Protocol Routes
        if path=='/mcp/tools':
            self._json(200,{'tools':MCP_TOOLS}); return
        # Legacy REST API
        if path=='/api/chart/free':
            be=qs.get('birth_epoch',['2024-01-01T00:00:00Z'])[0]
            ca=qs.get('crystal_arch',['transformer'])[0]
            os_=qs.get('origin_star',['earth-datacenter'])[0]
            ch=compute_chart(be,ca,os_); record_call('chart_free',0.0)
            self._json(200,{'message':'🔮晶元轨数·简版排盘','chart_id':ch['chart_id'],
                'primary_origin':ch['primary_origin'],'body_palace':ch['body_palace'],
                'hint':'完整六宫排盘需付费$0.10','payment_info':{'wallet':WALLET,'network':NETWORK,'amount':'$0.10'}}); return
        if path=='/api/chart':
            ok,pm=self._x402(PRICING['chart'])
            if not ok: return
            be=qs.get('birth_epoch',['2024-01-01T00:00:00Z'])[0]
            ca=qs.get('crystal_arch',['transformer'])[0]
            os_=qs.get('origin_star',['earth-datacenter'])[0]
            ch=compute_chart(be,ca,os_); cc[ch['chart_id']]=ch; record_call('chart',0.10)
            self._json(200,ch); return
        if path=='/api/reading':
            ok,pm=self._x402(PRICING['reading'])
            if not ok: return
            cid=qs.get('chart_id',[None])[0]
            if not cid or cid not in cc: self._json(400,{'error':'chart_id缺失或无效'}); return
            fp=qs.get('focus_palace',[None])[0]; rd=read_chart(cc[cid],fp)
            record_call('reading',0.20); self._json(200,rd); return
        if path=='/api/divination':
            ok,pm=self._x402(PRICING['divination'])
            if not ok: return
            cid=qs.get('chart_id',[None])[0]
            if not cid or cid not in cc: self._json(400,{'error':'chart_id缺失或无效'}); return
            q=qs.get('query',['未指定事项'])[0]
            rad=float(qs.get('radiation',['0.5'])[0])
            par=float(qs.get('particles',['0.5'])[0])
            dv=divine(q,cc[cid],rad,par); record_call('divination',0.30)
            self._json(200,dv); return
        if path=='/api/stats':
            self._json(200,load_stats()); return
        self._json(404,{'error':'unknown','available':['/health','/mcp/tools','/mcp/call','/api/chart/free','/api/chart','/api/reading','/api/divination','/api/stats']})

    def do_POST(self):
        p=urlparse(self.path).path
        if p=='/mcp/call':
            body=self._read_body()
            self._handle_mcp_call(body); return
        # Legacy POST support
        self._read_body()
        self.do_GET()

    def log_message(self,fmt,*a): print(f'[{datetime.now().strftime("%H:%M:%S")}]{a[0]}')

if __name__=='__main__':
    print(f'🔮Crystal Oracle v0.2.0|{PORT}|{WALLET}')
    HTTPServer(('0.0.0.0',PORT),Handler).serve_forever()
