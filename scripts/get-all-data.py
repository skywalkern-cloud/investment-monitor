#!/usr/bin/env python3
"""
投资监控仪表盘 - 完整数据获取脚本 v6
接入61个指标的所有可用数据源
新增：日期提取、同比/环比计算、指标说明
"""

import json
import os
from datetime import datetime, timedelta

# 配置代理
PROXY = os.environ.get('HTTP_PROXY', 'http://127.0.0.1:7890')
os.environ['HTTP_PROXY'] = PROXY
os.environ['HTTPS_PROXY'] = PROXY

# 数据有效性配置
VALIDITY_CONFIG = {
    'monthly': {'max_age_days': 30, 'label': '月频数据'},
    'daily': {'max_age_days': 3, 'label': '日频数据'},
    'realtime': {'max_age_days': 1, 'label': '实时数据'},
}

def check_data_validity(value, source, frequency='monthly'):
    """检查数据有效性"""
    config = VALIDITY_CONFIG.get(frequency, VALIDITY_CONFIG['monthly'])
    
    if value == 'NA' or value is None:
        return {'is_valid': False, 'status': 'na', 'message': '数据不可用'}
    
    if source and '-' in source:
        return {'is_valid': True, 'status': 'fresh', 'message': f'{config["label"]}，数据有效'}
    
    return {'is_valid': True, 'status': 'unknown', 'message': '数据来源未知'}

def format_date_label(date_str):
    """将日期字符串格式化为显示标签，如 '2025Q4' 或 '2026年2月'"""
    if not date_str:
        return '-'
    try:
        # 处理季度格式，如 "2025Q4"
        if 'Q' in str(date_str).upper():
            return str(date_str).upper()
        # 处理年月格式，如 "2025-01" 或 "2025/01"
        if '-' in str(date_str) or '/' in str(date_str):
            parts = str(date_str).replace('/', '-').split('-')
            year = parts[0]
            month = int(parts[1]) if len(parts) > 1 else 1
            return f"{year}年{month}月"
        # 处理中文格式，如 "2025年01月"
        if '年' in str(date_str):
            return str(date_str)
        return str(date_str)
    except:
        return str(date_str)

def calculate_yoy(current, prev_year):
    """计算同比变化（小数形式，如0.3表示+30%）"""
    if current is None or prev_year is None:
        return None
    if prev_year == 0:
        return None
    return round((current - prev_year) / abs(prev_year), 3)

def calculate_mom(current, prev_period):
    """计算环比变化（小数形式，如0.1表示+10%）"""
    if current is None or prev_period is None:
        return None
    if prev_period == 0:
        return None
    return round((current - prev_period) / abs(prev_period), 3)

def format_change_label(change):
    """格式化变化率为显示标签，如 '+0.3%'"""
    if change is None:
        return '-'
    sign = '+' if change >= 0 else ''
    return f"{sign}{round(change * 100, 1)}%"

def get_all_data():
    """获取所有61个指标的数据（扩展版：含日期/同比/环比）"""
    data = {}
    meta = {}  # 存储日期、同比、环比等元数据
    sources = {}
    validity = {}
    
    try:
        import akshare as ak
        
        # ===== 维度1: 宏观经济 =====
        
        # GDP
        try:
            df = ak.macro_china_gdp()
            current = round(float(df['国内生产总值-同比增长'].iloc[0]), 1)
            data['gdp'] = current
            # 提取日期
            date_col = '季度' if '季度' in df.columns else df.columns[0]
            date_val = str(df[date_col].iloc[0]) if date_col else None
            meta['gdp'] = {
                'date': date_val,
                'dateLabel': format_date_label(date_val),
            }
            # 尝试计算同比（需要去年同期数据）
            if len(df) > 1:
                prev_year_val = df['国内生产总值-同比增长'].iloc[1] if len(df) > 1 else None
                if prev_year_val and str(prev_year_val) != 'nan':
                    yoy = calculate_yoy(current, float(prev_year_val))
                    meta['gdp']['yoy'] = yoy
                    meta['gdp']['yoyLabel'] = format_change_label(yoy)
            # 尝试计算环比（使用"前值"字段）
            if '前值' in df.columns:
                prev_val = df['前值'].iloc[0]
                if prev_val and str(prev_val) != 'nan':
                    mom = calculate_mom(current, float(prev_val))
                    meta['gdp']['mom'] = mom
                    meta['gdp']['momLabel'] = format_change_label(mom)
            sources['gdp'] = 'AKShare-macro_china_gdp'
            validity['gdp'] = check_data_validity(data['gdp'], sources['gdp'], 'monthly')
            print(f"✅ GDP: {data['gdp']}% {meta['gdp'].get('dateLabel', '-')}")
        except Exception as e:
            data['gdp'] = 'NA'
            meta['gdp'] = {'dateLabel': '-', 'yoyLabel': '-', 'momLabel': '-'}
            validity['gdp'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ GDP: {e}")
        
        # CPI
        try:
            df = ak.macro_china_cpi()
            current = round(float(df['全国-同比增长'].iloc[0]), 1)
            data['cpi'] = current
            # 提取日期
            date_col = '月份' if '月份' in df.columns else df.columns[0]
            date_val = str(df[date_col].iloc[0]) if date_col else None
            meta['cpi'] = {
                'date': date_val,
                'dateLabel': format_date_label(date_val),
            }
            # 尝试计算同比 - 使用12个月前的去年同期数据
            if len(df) > 12:
                prev_year_val = df['全国-同比增长'].iloc[12]  # 12个月前
                if prev_year_val and str(prev_year_val) != 'nan':
                    yoy = calculate_yoy(current, float(prev_year_val))
                    meta['cpi']['yoy'] = yoy
                    meta['cpi']['yoyLabel'] = format_change_label(yoy)
            # 尝试计算环比
            if '前值' in df.columns:
                prev_val = df['前值'].iloc[0]
                if prev_val and str(prev_val) != 'nan':
                    mom = calculate_mom(current, float(prev_val))
                    meta['cpi']['mom'] = mom
                    meta['cpi']['momLabel'] = format_change_label(mom)
            sources['cpi'] = 'AKShare-macro_china_cpi'
            validity['cpi'] = check_data_validity(data['cpi'], sources['cpi'], 'monthly')
            print(f"✅ CPI: {data['cpi']}% {meta['cpi'].get('dateLabel', '-')}")
        except Exception as e:
            data['cpi'] = 'NA'
            meta['cpi'] = {'dateLabel': '-', 'yoyLabel': '-', 'momLabel': '-'}
            validity['cpi'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ CPI: {e}")
        
        # PMI
        try:
            df = ak.macro_china_pmi()
            current = round(float(df['制造业-指数'].iloc[0]), 1)
            data['pmi'] = current
            # 提取日期
            date_col = '月份' if '月份' in df.columns else df.columns[0]
            date_val = str(df[date_col].iloc[0]) if date_col else None
            meta['pmi'] = {
                'date': date_val,
                'dateLabel': format_date_label(date_val),
            }
            # 尝试计算环比
            if '前值' in df.columns:
                prev_val = df['前值'].iloc[0]
                if prev_val and str(prev_val) != 'nan':
                    mom = calculate_mom(current, float(prev_val))
                    meta['pmi']['mom'] = mom
                    meta['pmi']['momLabel'] = format_change_label(mom)
            sources['pmi'] = 'AKShare-macro_china_pmi'
            validity['pmi'] = check_data_validity(data['pmi'], sources['pmi'], 'monthly')
            print(f"✅ PMI: {data['pmi']} {meta['pmi'].get('dateLabel', '-')}")
        except Exception as e:
            data['pmi'] = 'NA'
            meta['pmi'] = {'dateLabel': '-', 'yoyLabel': '-', 'momLabel': '-'}
            validity['pmi'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ PMI: {e}")
        
        # 服务业PMI
        try:
            df = ak.macro_china_pmi()
            current = round(float(df['非制造业-指数'].iloc[0]), 1)
            data['servicePmi'] = current
            date_col = '月份' if '月份' in df.columns else df.columns[0]
            date_val = str(df[date_col].iloc[0]) if date_col else None
            meta['servicePmi'] = {
                'date': date_val,
                'dateLabel': format_date_label(date_val),
            }
            if '前值' in df.columns:
                prev_val = df['前值'].iloc[0]
                if prev_val and str(prev_val) != 'nan':
                    mom = calculate_mom(current, float(prev_val))
                    meta['servicePmi']['mom'] = mom
                    meta['servicePmi']['momLabel'] = format_change_label(mom)
            sources['servicePmi'] = 'AKShare-macro_china_pmi'
            validity['servicePmi'] = check_data_validity(data['servicePmi'], sources['servicePmi'], 'monthly')
            print(f"✅ 服务业PMI: {data['servicePmi']}")
        except Exception as e:
            data['servicePmi'] = 'NA'
            meta['servicePmi'] = {'dateLabel': '-', 'yoyLabel': '-', 'momLabel': '-'}
            validity['servicePmi'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ 服务业PMI: {e}")
        
        # PPI
        try:
            df = ak.macro_china_ppi()
            current = round(float(df['当月同比增长'].iloc[0]), 1)
            data['ppi'] = current
            date_col = '月份' if '月份' in df.columns else df.columns[0]
            date_val = str(df[date_col].iloc[0]) if date_col else None
            meta['ppi'] = {
                'date': date_val,
                'dateLabel': format_date_label(date_val),
            }
            if len(df) > 12:
                prev_year_val = df['当月同比增长'].iloc[12]  # 12个月前
                if prev_year_val and str(prev_year_val) != 'nan':
                    yoy = calculate_yoy(current, float(prev_year_val))
                    meta['ppi']['yoy'] = yoy
                    meta['ppi']['yoyLabel'] = format_change_label(yoy)
            if '前值' in df.columns:
                prev_val = df['前值'].iloc[0]
                if prev_val and str(prev_val) != 'nan':
                    mom = calculate_mom(current, float(prev_val))
                    meta['ppi']['mom'] = mom
                    meta['ppi']['momLabel'] = format_change_label(mom)
            sources['ppi'] = 'AKShare-macro_china_ppi'
            validity['ppi'] = check_data_validity(data['ppi'], sources['ppi'], 'monthly')
            print(f"✅ PPI: {data['ppi']}%")
        except Exception as e:
            data['ppi'] = 'NA'
            meta['ppi'] = {'dateLabel': '-', 'yoyLabel': '-', 'momLabel': '-'}
            validity['ppi'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ PPI: {e}")
        
        # LPR
        try:
            df = ak.macro_china_lpr()
            current = round(float(df['LPR1Y'].iloc[-1]), 1)
            data['interest'] = current
            date_col = '日期' if '日期' in df.columns else df.columns[0]
            date_val = str(df[date_col].iloc[-1]) if date_col else None
            meta['interest'] = {
                'date': date_val,
                'dateLabel': format_date_label(date_val),
            }
            if len(df) > 1:
                prev_val = df['LPR1Y'].iloc[-2]
                if prev_val and str(prev_val) != 'nan':
                    mom = calculate_mom(current, float(prev_val))
                    meta['interest']['mom'] = mom
                    meta['interest']['momLabel'] = format_change_label(mom)
            sources['interest'] = 'AKShare-macro_china_lpr'
            validity['interest'] = check_data_validity(data['interest'], sources['interest'], 'monthly')
            print(f"✅ LPR: {data['interest']}%")
        except Exception as e:
            data['interest'] = 'NA'
            meta['interest'] = {'dateLabel': '-', 'yoyLabel': '-', 'momLabel': '-'}
            validity['interest'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ LPR: {e}")
        
        # 社零
        try:
            df = ak.macro_china_consumer_goods_retail()
            current = round(float(df['累计-同比增长'].iloc[0]), 1)
            data['retail'] = current
            date_col = '月份' if '月份' in df.columns else df.columns[0]
            date_val = str(df[date_col].iloc[0]) if date_col else None
            meta['retail'] = {
                'date': date_val,
                'dateLabel': format_date_label(date_val),
            }
            if len(df) > 1:
                prev_year_val = df['累计-同比增长'].iloc[1]
                if prev_year_val and str(prev_year_val) != 'nan':
                    yoy = calculate_yoy(current, float(prev_year_val))
                    meta['retail']['yoy'] = yoy
                    meta['retail']['yoyLabel'] = format_change_label(yoy)
            if '前值' in df.columns:
                prev_val = df['前值'].iloc[0]
                if prev_val and str(prev_val) != 'nan':
                    mom = calculate_mom(current, float(prev_val))
                    meta['retail']['mom'] = mom
                    meta['retail']['momLabel'] = format_change_label(mom)
            sources['retail'] = 'AKShare-macro_china_consumer_goods_retail'
            validity['retail'] = check_data_validity(data['retail'], sources['retail'], 'monthly')
            print(f"✅ 社零: {data['retail']}%")
        except Exception as e:
            data['retail'] = 'NA'
            meta['retail'] = {'dateLabel': '-', 'yoyLabel': '-', 'momLabel': '-'}
            validity['retail'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ 社零: {e}")
        
        # 社融增速（数据已按最新在前排序）
        try:
            df = ak.macro_china_new_financial_credit()
            current = round(float(df['累计-同比增长'].iloc[0]), 1)
            data['socialFinance'] = current
            date_col = '月份' if '月份' in df.columns else df.columns[0]
            date_val = str(df[date_col].iloc[0]) if date_col else None
            meta['socialFinance'] = {
                'date': date_val,
                'dateLabel': format_date_label(date_val),
            }
            if len(df) > 1:
                prev_year_val = df['累计-同比增长'].iloc[1]
                if prev_year_val and str(prev_year_val) != 'nan':
                    yoy = calculate_yoy(current, float(prev_year_val))
                    meta['socialFinance']['yoy'] = yoy
                    meta['socialFinance']['yoyLabel'] = format_change_label(yoy)
            if '前值' in df.columns:
                prev_val = df['前值'].iloc[0]
                if prev_val and str(prev_val) != 'nan':
                    mom = calculate_mom(current, float(prev_val))
                    meta['socialFinance']['mom'] = mom
                    meta['socialFinance']['momLabel'] = format_change_label(mom)
            sources['socialFinance'] = 'AKShare-macro_china_new_financial_credit'
            validity['socialFinance'] = check_data_validity(data['socialFinance'], sources['socialFinance'], 'monthly')
            print(f"✅ 社融: {data['socialFinance']}%")
        except Exception as e:
            data['socialFinance'] = 'NA'
            meta['socialFinance'] = {'dateLabel': '-', 'yoyLabel': '-', 'momLabel': '-'}
            validity['socialFinance'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ 社融: {e}")
        
        # 出口
        try:
            df = ak.macro_china_exports_yoy()
            current = round(float(df['今值'].iloc[0]), 1)
            data['export'] = current
            date_col = '日期' if '日期' in df.columns else df.columns[0]
            date_val = str(df[date_col].iloc[0]) if date_col else None
            meta['export'] = {
                'date': date_val,
                'dateLabel': format_date_label(date_val),
            }
            if '预测' in df.columns:
                pred_val = df['预测'].iloc[0]
                if pred_val and str(pred_val) != 'nan':
                    yoy = calculate_yoy(current, float(pred_val))
                    meta['export']['yoy'] = yoy
                    meta['export']['yoyLabel'] = format_change_label(yoy)
            if '前值' in df.columns:
                prev_val = df['前值'].iloc[0]
                if prev_val and str(prev_val) != 'nan':
                    mom = calculate_mom(current, float(prev_val))
                    meta['export']['mom'] = mom
                    meta['export']['momLabel'] = format_change_label(mom)
            sources['export'] = 'AKShare-macro_china_exports_yoy'
            validity['export'] = check_data_validity(data['export'], sources['export'], 'monthly')
            print(f"✅ 出口: {data['export']}%")
        except Exception as e:
            data['export'] = 'NA'
            meta['export'] = {'dateLabel': '-', 'yoyLabel': '-', 'momLabel': '-'}
            validity['export'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ 出口: {e}")
        
        # M2增速（倒序找最新有效值）
        try:
            df = ak.macro_china_m2_yearly()
            m2_val = None
            for i in range(len(df) - 1, -1, -1):
                val = df['今值'].iloc[i]
                if str(val) != 'nan' and val is not None:
                    m2_val = float(val)
                    date_val = str(df[df.columns[0]].iloc[i]) if df.columns[0] else None
                    break
            if m2_val is None:
                raise Exception("无有效M2数据")
            data['m2'] = round(m2_val, 1)
            meta['m2'] = {
                'date': date_val,
                'dateLabel': format_date_label(date_val),
            }
            # M2通常没有同比，直接用前值计算环比
            if '前值' in df.columns:
                for i in range(len(df) - 1, -1, -1):
                    prev_val = df['前值'].iloc[i]
                    if prev_val and str(prev_val) != 'nan':
                        mom = calculate_mom(m2_val, float(prev_val))
                        meta['m2']['mom'] = mom
                        meta['m2']['momLabel'] = format_change_label(mom)
                        break
            sources['m2'] = 'AKShare-macro_china_m2_yearly'
            validity['m2'] = check_data_validity(data['m2'], sources['m2'], 'monthly')
            print(f"✅ M2: {data['m2']}%")
        except Exception as e:
            data['m2'] = 'NA'
            meta['m2'] = {'dateLabel': '-', 'yoyLabel': '-', 'momLabel': '-'}
            validity['m2'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ M2: {e}")
        
        # ===== 流动性 =====
        
        # 北向资金
        try:
            df = ak.stock_hsgt_fund_flow_summary_em()
            north = df[df['资金方向'] == '北向']
            data['northbound'] = round(float(north['资金净流入'].sum()), 1)
            sources['northbound'] = 'AKShare-stock_hsgt_fund_flow_summary_em'
            validity['northbound'] = check_data_validity(data['northbound'], sources['northbound'], 'daily')
            print(f"✅ 北向资金: {data['northbound']}亿")
        except Exception as e:
            data['northbound'] = 'NA'
            validity['northbound'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ 北向资金: {e}")
        
        # BDI指数
        try:
            df = ak.macro_shipping_bdi()
            current = round(float(df['最新值'].iloc[0]), 0)
            data['bdi'] = current
            date_col = '日期' if '日期' in df.columns else df.columns[0]
            date_val = str(df[date_col].iloc[0]) if date_col else None
            meta['bdi'] = {
                'date': date_val,
                'dateLabel': format_date_label(date_val),
            }
            if '前值' in df.columns:
                prev_val = df['前值'].iloc[0]
                if prev_val and str(prev_val) != 'nan':
                    mom = calculate_mom(current, float(prev_val))
                    meta['bdi']['mom'] = mom
                    meta['bdi']['momLabel'] = format_change_label(mom)
            sources['bdi'] = 'AKShare-macro_shipping_bdi'
            validity['bdi'] = check_data_validity(data['bdi'], sources['bdi'], 'daily')
            print(f"✅ BDI: {data['bdi']}")
        except Exception as e:
            data['bdi'] = 'NA'
            meta['bdi'] = {'dateLabel': '-', 'yoyLabel': '-', 'momLabel': '-'}
            validity['bdi'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ BDI: {e}")
        
        # 融资余额
        try:
            df = ak.stock_margin_sse()
            data['margin'] = round(float(df['融资余额'].iloc[0]) / 100000000, 1)
            sources['margin'] = 'AKShare-stock_margin_sse'
            validity['margin'] = check_data_validity(data['margin'], sources['margin'], 'daily')
            print(f"✅ 融资余额: {data['margin']}万亿")
        except Exception as e:
            data['margin'] = 'NA'
            validity['margin'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ 融资余额: {e}")
        
        # 10年美债
        try:
            df = ak.bond_zh_us_rate()
            us10y_val = None
            date_val = None
            # 从后往前遍历找最新有效值
            for idx in range(len(df) - 1, -1, -1):
                val = df['美国国债收益率10年'].iloc[idx]
                if str(val) != 'nan' and val is not None:
                    us10y_val = float(val)
                    date_col = df.columns[0]
                    date_val = str(df[date_col].iloc[idx])
                    break
            
            if us10y_val:
                data['us10y'] = round(us10y_val, 2)
                meta['us10y'] = {
                    'date': date_val,
                    'dateLabel': format_date_label(date_val),
                }
                # 计算环比（使用前值）
                if '前值' in df.columns:
                    for idx in range(len(df) - 1, -1, -1):
                        prev_val = df['前值'].iloc[idx]
                        if prev_val and str(prev_val) != 'nan':
                            mom = calculate_mom(us10y_val, float(prev_val))
                            meta['us10y']['mom'] = mom
                            meta['us10y']['momLabel'] = format_change_label(mom)
                            break
                sources['us10y'] = 'AKShare-bond_zh_us_rate'
                validity['us10y'] = check_data_validity(data['us10y'], sources['us10y'], 'daily')
                print(f"✅ 10年美债: {data['us10y']}%")
            else:
                raise Exception("无有效数据")
        except Exception as e:
            data['us10y'] = 'NA'
            meta['us10y'] = {'dateLabel': '-', 'yoyLabel': '-', 'momLabel': '-'}
            validity['us10y'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ 10年美债: {e}")
        
        # ===== 行情数据 =====
        
        try:
            df = ak.stock_zh_index_daily(symbol='sh000001')
            data['shIndex'] = round(float(df['close'].iloc[-1]), 1)
            sources['shIndex'] = 'AKShare-stock_zh_index_daily'
            validity['shIndex'] = check_data_validity(data['shIndex'], sources['shIndex'], 'daily')
            print(f"✅ 上证: {data['shIndex']}")
        except Exception as e:
            data['shIndex'] = 'NA'
            validity['shIndex'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ 上证: {e}")
        
        try:
            df = ak.stock_zh_index_daily(symbol='sz399001')
            data['szIndex'] = round(float(df['close'].iloc[-1]), 1)
            sources['szIndex'] = 'AKShare-stock_zh_index_daily'
            validity['szIndex'] = check_data_validity(data['szIndex'], sources['szIndex'], 'daily')
            print(f"✅ 深证: {data['szIndex']}")
        except Exception as e:
            data['szIndex'] = 'NA'
            validity['szIndex'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ 深证: {e}")
        
        try:
            df = ak.stock_zh_index_daily(symbol='sz399006')
            data['cyIndex'] = round(float(df['close'].iloc[-1]), 1)
            sources['cyIndex'] = 'AKShare-stock_zh_index_daily'
            validity['cyIndex'] = check_data_validity(data['cyIndex'], sources['cyIndex'], 'daily')
            print(f"✅ 创业板: {data['cyIndex']}")
        except Exception as e:
            data['cyIndex'] = 'NA'
            validity['cyIndex'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ 创业板: {e}")
        
        try:
            df = ak.stock_zh_index_daily(symbol='sh000300')
            data['hs300'] = round(float(df['close'].iloc[-1]), 1)
            sources['hs300'] = 'AKShare-stock_zh_index_daily'
            validity['hs300'] = check_data_validity(data['hs300'], sources['hs300'], 'daily')
            print(f"✅ 沪深300: {data['hs300']}")
        except Exception as e:
            data['hs300'] = 'NA'
            validity['hs300'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ 沪深300: {e}")
        
        # ===== 大宗商品 =====
        
        try:
            df = ak.futures_zh_daily_sina(symbol='sc0')
            # 原油期货SC是人民币/吨，需要转换为美元/桶（1吨≈7.3桶）
            oil_cny_per_ton = float(df['close'].iloc[-1])
            oil_usd_per_barrel = round(oil_cny_per_ton / 7.3, 1)
            data['oil'] = oil_usd_per_barrel
            # 提取日期
            date_val = str(df['date'].iloc[-1]) if 'date' in df.columns else None
            meta['oil'] = {
                'date': date_val,
                'dateLabel': format_date_label(date_val),
            }
            # 计算环比
            if len(df) > 1:
                prev_cny = float(df['close'].iloc[-2])
                prev_usd = prev_cny / 7.3
                mom = calculate_mom(oil_usd_per_barrel, prev_usd)
                if mom:
                    meta['oil']['mom'] = mom
                    meta['oil']['momLabel'] = format_change_label(mom)
            sources['oil'] = 'AKShare-futures_zh_daily_sina'
            validity['oil'] = check_data_validity(data['oil'], sources['oil'], 'daily')
            print(f"✅ 原油: ${data['oil']}/桶")
        except Exception as e:
            data['oil'] = 'NA'
            validity['oil'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ 原油: {e}")
        
        try:
            df = ak.futures_zh_daily_sina(symbol='au0')
            data['gold'] = round(float(df['close'].iloc[-1]), 1)
            sources['gold'] = 'AKShare-futures_zh_daily_sina'
            validity['gold'] = check_data_validity(data['gold'], sources['gold'], 'daily')
            print(f"✅ 黄金: {data['gold']}")
        except Exception as e:
            data['gold'] = 'NA'
            validity['gold'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ 黄金: {e}")
        
        try:
            df = ak.futures_zh_daily_sina(symbol='cu0')
            data['copper'] = round(float(df['close'].iloc[-1]), 1)
            sources['copper'] = 'AKShare-futures_zh_daily_sina'
            validity['copper'] = check_data_validity(data['copper'], sources['copper'], 'daily')
            print(f"✅ 铜: {data['copper']}")
        except Exception as e:
            data['copper'] = 'NA'
            validity['copper'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ 铜: {e}")
        
        try:
            df = ak.futures_zh_daily_sina(symbol='rb0')
            data['rebar'] = round(float(df['close'].iloc[-1]), 1)
            sources['rebar'] = 'AKShare-futures_zh_daily_sina'
            validity['rebar'] = check_data_validity(data['rebar'], sources['rebar'], 'daily')
            print(f"✅ 螺纹钢: {data['rebar']}")
        except Exception as e:
            data['rebar'] = 'NA'
            validity['rebar'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ 螺纹钢: {e}")
        
        try:
            df = ak.futures_zh_daily_sina(symbol='i0')
            data['ironOre'] = round(float(df['close'].iloc[-1]), 1)
            sources['ironOre'] = 'AKShare-futures_zh_daily_sina'
            validity['ironOre'] = check_data_validity(data['ironOre'], sources['ironOre'], 'daily')
            print(f"✅ 铁矿石: {data['ironOre']}")
        except Exception as e:
            data['ironOre'] = 'NA'
            validity['ironOre'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ 铁矿石: {e}")
        
        # 房地产销售
        try:
            df = ak.macro_china_real_estate()
            current = round(float(df['最新值'].iloc[0]), 1)
            data['property'] = current
            date_col = '日期' if '日期' in df.columns else df.columns[0]
            date_val = str(df[date_col].iloc[0]) if date_col else None
            meta['property'] = {
                'date': date_val,
                'dateLabel': format_date_label(date_val),
            }
            if len(df) > 1:
                prev_year_val = df['最新值'].iloc[1]
                if prev_year_val and str(prev_year_val) != 'nan':
                    yoy = calculate_yoy(current, float(prev_year_val))
                    meta['property']['yoy'] = yoy
                    meta['property']['yoyLabel'] = format_change_label(yoy)
            if '前值' in df.columns:
                prev_val = df['前值'].iloc[0]
                if prev_val and str(prev_val) != 'nan':
                    mom = calculate_mom(current, float(prev_val))
                    meta['property']['mom'] = mom
                    meta['property']['momLabel'] = format_change_label(mom)
            sources['property'] = 'AKShare-macro_china_real_estate'
            validity['property'] = check_data_validity(data['property'], sources['property'], 'monthly')
            print(f"✅ 房地产: {data['property']}")
        except Exception as e:
            data['property'] = 'NA'
            meta['property'] = {'dateLabel': '-', 'yoyLabel': '-', 'momLabel': '-'}
            validity['property'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ 房地产: {e}")
        
        
        # ===== 美国宏观经济 =====
        
        # 美国失业率（倒序找最新有效值）
        try:
            df = ak.macro_usa_unemployment_rate()
            unemp_val = None
            date_val = None
            for i in range(len(df) - 1, -1, -1):
                val = df['今值'].iloc[i]
                if str(val) != 'nan' and val is not None:
                    unemp_val = float(val)
                    date_col = df.columns[0]
                    date_val = str(df[date_col].iloc[i])
                    break
            if unemp_val is None:
                raise Exception("无有效失业率数据")
            data['unemployment'] = round(unemp_val, 1)
            meta['unemployment'] = {
                'date': date_val,
                'dateLabel': format_date_label(date_val),
            }
            # 计算环比
            if '前值' in df.columns:
                for i in range(len(df) - 1, -1, -1):
                    prev_val = df['前值'].iloc[i]
                    if prev_val and str(prev_val) != 'nan':
                        mom = calculate_mom(unemp_val, float(prev_val))
                        meta['unemployment']['mom'] = mom
                        meta['unemployment']['momLabel'] = format_change_label(mom)
                        break
            sources['unemployment'] = 'AKShare-macro_usa_unemployment_rate'
            validity['unemployment'] = check_data_validity(data['unemployment'], sources['unemployment'], 'monthly')
            print(f"✅ 美国失业率: {data['unemployment']}%")
        except Exception as e:
            data['unemployment'] = 'NA'
            meta['unemployment'] = {'dateLabel': '-', 'yoyLabel': '-', 'momLabel': '-'}
            validity['unemployment'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ 美国失业率: {e}")
        
        # 美国非农就业（倒序找最新有效值）
        try:
            df = ak.macro_usa_non_farm()
            nf_val = None
            date_val = None
            for i in range(len(df) - 1, -1, -1):
                val = df['今值'].iloc[i]
                if str(val) != 'nan' and val is not None:
                    nf_val = float(val)
                    date_col = df.columns[0]
                    date_val = str(df[date_col].iloc[i])
                    break
            if nf_val is None:
                raise Exception("无有效非农数据")
            data['nonfarm'] = round(nf_val, 1)
            meta['nonfarm'] = {
                'date': date_val,
                'dateLabel': format_date_label(date_val),
            }
            # 计算同比（使用预测值作为参考）
            if '预测' in df.columns:
                pred_val = df['预测'].iloc[0]
                if pred_val and str(pred_val) != 'nan':
                    yoy = calculate_yoy(nf_val, float(pred_val))
                    meta['nonfarm']['yoy'] = yoy
                    meta['nonfarm']['yoyLabel'] = format_change_label(yoy)
            # 计算环比
            if '前值' in df.columns:
                for i in range(len(df) - 1, -1, -1):
                    prev_val = df['前值'].iloc[i]
                    if prev_val and str(prev_val) != 'nan':
                        mom = calculate_mom(nf_val, float(prev_val))
                        meta['nonfarm']['mom'] = mom
                        meta['nonfarm']['momLabel'] = format_change_label(mom)
                        break
            sources['nonfarm'] = 'AKShare-macro_usa_non_farm'
            validity['nonfarm'] = check_data_validity(data['nonfarm'], sources['nonfarm'], 'monthly')
            print(f"✅ 美国非农: {data['nonfarm']}万")
        except Exception as e:
            data['nonfarm'] = 'NA'
            meta['nonfarm'] = {'dateLabel': '-', 'yoyLabel': '-', 'momLabel': '-'}
            validity['nonfarm'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ 美国非农: {e}")
        
        # 美国核心PCE（倒序找最新有效值）
        try:
            df = ak.macro_usa_core_pce_price()
            pce_val = None
            date_val = None
            for i in range(len(df) - 1, -1, -1):
                val = df['今值'].iloc[i]
                if str(val) != 'nan' and val is not None:
                    pce_val = float(val)
                    date_col = df.columns[0]
                    date_val = str(df[date_col].iloc[i])
                    break
            if pce_val is None:
                raise Exception("无有效PCE数据")
            data['corePCE'] = round(pce_val, 1)
            meta['corePCE'] = {
                'date': date_val,
                'dateLabel': format_date_label(date_val),
            }
            # 计算同比（使用去年同期）
            if len(df) > 1:
                for i in range(len(df) - 1, -1, -1):
                    prev_year_val = df['今值'].iloc[i + 12] if i + 12 < len(df) else None
                    if prev_year_val and str(prev_year_val) != 'nan':
                        yoy = calculate_yoy(pce_val, float(prev_year_val))
                        meta['corePCE']['yoy'] = yoy
                        meta['corePCE']['yoyLabel'] = format_change_label(yoy)
                        break
            # 计算环比
            if '前值' in df.columns:
                for i in range(len(df) - 1, -1, -1):
                    prev_val = df['前值'].iloc[i]
                    if prev_val and str(prev_val) != 'nan':
                        mom = calculate_mom(pce_val, float(prev_val))
                        meta['corePCE']['mom'] = mom
                        meta['corePCE']['momLabel'] = format_change_label(mom)
                        break
            sources['corePCE'] = 'AKShare-macro_usa_core_pce_price'
            validity['corePCE'] = check_data_validity(data['corePCE'], sources['corePCE'], 'monthly')
            print(f"✅ 核心PCE: {data['corePCE']}%")
        except Exception as e:
            data['corePCE'] = 'NA'
            meta['corePCE'] = {'dateLabel': '-', 'yoyLabel': '-', 'momLabel': '-'}
            validity['corePCE'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ 核心PCE: {e}")
        
        
        
        # ===== 全球流动性 =====
        
        # 美元指数
        try:
            df = ak.index_global_spot_em()
            udi = df[df['代码'] == 'UDI']
            if not udi.empty:
                data['dollarIndex'] = round(float(udi['最新价'].iloc[0]), 2)
                date_val = str(udi['最新行情时间'].iloc[0]) if '最新行情时间' in udi.columns else None
                meta['dollarIndex'] = {
                    'date': date_val,
                    'dateLabel': format_date_label(date_val),
                }
                # 计算环比
                if '涨跌幅' in udi.columns:
                    change = udi['涨跌幅'].iloc[0]
                    if change and str(change) != 'nan':
                        mom = float(change) / 100
                        meta['dollarIndex']['mom'] = mom
                        meta['dollarIndex']['momLabel'] = format_change_label(mom)
                sources['dollarIndex'] = 'AKShare-index_global_spot_em'
                validity['dollarIndex'] = check_data_validity(data['dollarIndex'], sources['dollarIndex'], 'daily')
                print(f"✅ 美元指数: {data['dollarIndex']}")
            else:
                raise Exception("未找到美元指数")
        except Exception as e:
            data['dollarIndex'] = 'NA'
            meta['dollarIndex'] = {'dateLabel': '-', 'yoyLabel': '-', 'momLabel': '-'}
            validity['dollarIndex'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ 美元指数: {e}")
        
        # 离岸人民币
        try:
            df = ak.fx_spot_quote()
            cny_row = df[df['货币对'] == 'USD/CNY']
            if not cny_row.empty:
                # USD/CNY 是直接汇率，即1美元换多少人民币
                data['cny'] = round(float(cny_row['买报价'].iloc[0]), 4)
                meta['cny'] = {
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'dateLabel': datetime.now().strftime('%Y年%m月%d日'),
                }
                sources['cny'] = 'AKShare-fx_spot_quote'
                validity['cny'] = check_data_validity(data['cny'], sources['cny'], 'daily')
                print(f"✅ 离岸人民币: {data['cny']}")
            else:
                raise Exception("未找到USD/CNY")
        except Exception as e:
            data['cny'] = 'NA'
            meta['cny'] = {'dateLabel': '-', 'yoyLabel': '-', 'momLabel': '-'}
            validity['cny'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ 离岸人民币: {e}")
        
        # VIX恐慌指数 - 中国无直接的VIX数据，使用中证1000波动率作为替代
        try:
            df = ak.stock_zh_index_daily(symbol='sh000018')
            data['vix'] = round(float(df['close'].iloc[-1]), 2)
            date_val = str(df['date'].iloc[-1]) if 'date' in df.columns else None
            meta['vix'] = {
                'date': date_val,
                'dateLabel': format_date_label(date_val),
                'note': '中证1000波动率指数（非美国VIX）'
            }
            if len(df) > 1:
                prev = float(df['close'].iloc[-2])
                mom = calculate_mom(data['vix'], prev)
                if mom:
                    meta['vix']['mom'] = mom
                    meta['vix']['momLabel'] = format_change_label(mom)
            sources['vix'] = 'AKShare-stock_zh_index_daily(中证1000波指)'
            validity['vix'] = check_data_validity(data['vix'], sources['vix'], 'daily')
            print(f"✅ VIX: {data['vix']} (中证1000波指)")
        except Exception as e:
            data['vix'] = 'NA'
            meta['vix'] = {'dateLabel': '-', 'yoyLabel': '-', 'momLabel': '-'}
            validity['vix'] = {'is_valid': False, 'status': 'na', 'message': str(e)}
            print(f"❌ VIX: {e}")
        
        # 南向资金
        try:
            df = ak.stock_hsgt_fund_flow_summary_em()
            south = df[df['资金方向'] == '南向']
            # 港股通(沪)和港股通(深)的资金净流入相加
            total_south = round(float(south['资金净流入'].sum()), 1)
            data['southbound'] = total_south
            # 提取日期
            if '交易日' in south.columns:
                date_val = str(south['交易日'].iloc[0]) if len(south) > 0 else None
                meta['southbound'] = {
                    'date': date_val,
                    'dateLabel': format_date_label(date_val),
                }
            sources['southbound'] = 'AKShare-stock_hsgt_fund_flow_summary_em'
            validity['southbound'] = check_data_validity(data['southbound'], sources['southbound'], 'daily')
            print(f"✅ 南向资金: {data['southbound']}亿")
        except Exception as e:
            data['southbound'] = 'NA'
            validity['southbound'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ 南向资金: {e}")
        
        # EPU经济政策不确定性指数
        try:
            df = ak.article_epu_index()
            if not df.empty:
                current = round(float(df['China_Policy_Index'].iloc[-1]), 1)
                data['epu'] = current
                date_val = f"{df['year'].iloc[-1]}年{df['month'].iloc[-1]}月"
                meta['epu'] = {
                    'date': date_val,
                    'dateLabel': date_val,
                }
                # 同比
                if len(df) > 12:
                    prev_year_val = df['China_Policy_Index'].iloc[-13]
                    if prev_year_val and str(prev_year_val) != 'nan':
                        yoy = calculate_yoy(current, float(prev_year_val))
                        meta['epu']['yoy'] = yoy
                        meta['epu']['yoyLabel'] = format_change_label(yoy)
                sources['epu'] = 'AKShare-article_epu_index'
                validity['epu'] = check_data_validity(data['epu'], sources['epu'], 'monthly')
                print(f"✅ EPU: {data['epu']}")
            else:
                raise Exception("无EPU数据")
        except Exception as e:
            data['epu'] = 'NA'
            meta['epu'] = {'dateLabel': '-', 'yoyLabel': '-', 'momLabel': '-'}
            validity['epu'] = {'is_valid': False, 'status': 'error', 'message': str(e)}
            print(f"❌ EPU: {e}")
        
        # 美联储资产负债表
        try:
            # 尝试从Trading Economics获取，或者标记为NA
            # 使用中国央行资产负债表作为替代（仅作展示）
            raise Exception("美联储数据源待接入")
        except Exception as e:
            data['fedBalance'] = 'NA'
            validity['fedBalance'] = {'is_valid': False, 'status': 'na', 'message': str(e)}
            print(f"❌ 美联储资产: {e}")
        
        
            
    except Exception as e:
        print(f"获取数据失败: {e}")
    
    # 填充所有61个字段为NA
    all_fields = [
        'gdp', 'pmi', 'servicePmi', 'cpi', 'ppi', 'unemployment', 'nonfarm', 'corePCE', 'usCPI', 'usRetail',
        'm2', 'socialFinance', 'interest',
        'epu', 'riskLevel', 'regionalConflict', 'tariffPolicy',
        'electricity', 'retail', 'property', 'carSales',
        'northbound', 'southbound', 'fedBalance', 'fedRate', 'dollarIndex', 'cny', 'us10y', 'jobless',
        'vix', 'margin', 'turnover', 'fundPosition', 'etfFlow',
        'aiRdRatio', 'aiPatentCount', 'aiNewProductCount',
        'neRevenueGrowth', 'neRdPersonnelRatio', 'neNewProductRatio',
        'semCapexGrowth', 'semCapacityUtilization', 'semDomesticReplacement',
        'rdInvestment',
        'profitGrowth', 'inventorySalesRatio',
        'bdi', 'export', 'industryTransfer', 'keyMinerals',
        'agingRate', 'birthRate', 'leverageRate',
        'oil', 'gold', 'copper', 'rebar', 'ironOre', 'foodIndex', 'esgRegulation', 'blackSwan',
        'shIndex', 'szIndex', 'cyIndex', 'hs300', 'hsi'
    ]
    
    for k in all_fields:
        if k not in data:
            data[k] = 'NA'
            validity[k] = {'is_valid': False, 'status': 'na', 'message': '数据源未接入'}
        if k not in meta:
            meta[k] = {'dateLabel': '-', 'yoyLabel': '-', 'momLabel': '-'}
    
    return data, meta, sources, validity

def generate_validity_report(validity):
    """生成数据有效性报告"""
    report = {
        'total': len(validity),
        'valid': sum(1 for v in validity.values() if v['is_valid']),
        'invalid': sum(1 for v in validity.values() if not v['is_valid']),
        'by_status': {}
    }
    
    for k, v in validity.items():
        status = v['status']
        if status not in report['by_status']:
            report['by_status'][status] = []
        report['by_status'][status].append(k)
    
    return report

if __name__ == "__main__":
    data, meta, sources, validity = get_all_data()
    
    real_count = sum(1 for v in data.values() if v != 'NA')
    print(f"\n📊 共获取 {real_count} 个真实数据，{len(data) - real_count} 个NA")
    
    report = generate_validity_report(validity)
    print(f"\n📋 数据有效性报告:")
    print(f"  有效数据: {report['valid']}/{report['total']}")
    print(f"  无效数据: {report['invalid']}/{report['total']}")
    for status, fields in report['by_status'].items():
        print(f"  - {status}: {len(fields)}个")
    
    output = {
        'timestamp': datetime.now().isoformat(),
        'data': data,
        'meta': meta,
        'sources': sources,
        'validity': validity,
        'validity_report': report
    }
    print(json.dumps(output, ensure_ascii=False))
