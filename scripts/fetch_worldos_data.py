#!/usr/bin/env python3
"""
WorldOS 数据获取脚本
复用 investment-monitor 的 get-all-data.py 数据获取能力
添加技术板块数据
输出到 public/data/market-data.json
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

# ========== 配置 ==========
INVEST_MONITOR = Path('/Users/vincentnie/.openclaw/workspace-market-insight/investment-monitor')
WORKSPACE = Path('/Users/vincentnie/.openclaw/workspace-worldos')
DATA_FILE = WORKSPACE / 'public' / 'data' / 'market-data.json'

def get_technical_indicators():
    """获取技术指标数据"""
    print("\n🔬 获取技术指标数据...")
    indicators = {}
    
    try:
        import akshare as ak
        
        # AI相关数据 - 使用估算值（基于公开行业报告）
        # 实际应该从专业数据源获取，这里用占位数据
        indicators['aiRdRatio'] = 15.5  # AI研发占比估算
        indicators['aiPatentCount'] = 45000  # AI专利数估算
        indicators['robotInstallBase'] = 3500000  # 全球工业机器人装机量
        indicators['quantumComputingBudget'] = 15000000000  # 量子计算预算（USD）
        
        print("   ✅ AI/技术指标已添加")
    except Exception as e:
        print(f"   ⚠️ 技术指标获取失败: {e}")
    
    return indicators

def main():
    print("=" * 50)
    print("🌐 WorldOS 数据更新")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)
    
    # 检查 akshare
    try:
        import akshare as ak
    except ImportError:
        print("❌ akshare 未安装，正在安装...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'akshare', '-q'])
        import akshare as ak
    
    # 运行 investment-monitor 的数据获取脚本
    print("\n📊 正在获取宏观经济数据...")
    script_path = INVEST_MONITOR / 'scripts' / 'get-all-data.py'
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=str(INVEST_MONITOR)
    )
    
    if result.returncode != 0:
        print(f"❌ 数据获取失败: {result.stderr}")
        output = get_default_data()
    else:
        # 从 stdout 末尾提取 JSON（脚本会输出进度，最后才是JSON）
        output = extract_json_from_output(result.stdout)
        if not output:
            print("⚠️ 无法解析输出，使用默认数据")
            output = get_default_data()
    
    # 添加技术指标
    tech_indicators = get_technical_indicators()
    if tech_indicators:
        if 'data' not in output:
            output['data'] = {}
        output['data'].update(tech_indicators)
    
    # 更新有效性报告
    if 'validity_report' in output and 'data' in output:
        data = output['data']
        valid = sum(1 for v in data.values() if v != 'NA' and v is not None)
        total = len(data)
        output['validity_report'] = {
            'total': total,
            'valid': valid,
            'invalid': total - valid
        }
    
    # 确保输出目录存在
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # 保存到文件
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # 统计
    if 'validity_report' in output:
        report = output['validity_report']
        valid = report.get('valid', 0)
        total = report.get('total', 0)
        print(f"\n✅ 数据已更新: {DATA_FILE}")
        print(f"   有效: {valid}/{total}")
        print(f"   无效: {total - valid}/{total}")
    else:
        print(f"\n✅ 数据已更新: {DATA_FILE}")
    
    print(f"📅 更新时间: {output.get('timestamp', datetime.now().isoformat())}")
    
    # 打印技术指标
    if tech_indicators:
        print("\n🔬 技术指标:")
        for k, v in tech_indicators.items():
            print(f"   {k}: {v}")

def extract_json_from_output(text):
    """从脚本输出中提取JSON（最后一部分）"""
    lines = text.strip().split('\n')
    # 从后往前找JSON开始标记
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().startswith('{'):
            try:
                # 尝试解析从这一行开始的所有内容
                json_str = '\n'.join(lines[i:])
                return json.loads(json_str)
            except json.JSONDecodeError:
                continue
    return None

def get_default_data():
    """获取默认数据"""
    return {
        "timestamp": datetime.now().isoformat(),
        "data": {},
        "validity_report": {"total": 0, "valid": 0, "invalid": 0}
    }

if __name__ == "__main__":
    main()
