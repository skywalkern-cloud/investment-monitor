// 投资监控仪表盘 - 入口文件
// 龙五负责

import { useState, useEffect } from 'react';
import { Dashboard } from './components/Dashboard';
import { MetricData, defaultData } from './data/marketData';

function App() {
  const [data, setData] = useState<MetricData>(defaultData);
  const [lastUpdate, setLastUpdate] = useState<string>(new Date().toLocaleString());
  const [loading, setLoading] = useState<boolean>(true);

  // 获取实时数据
  useEffect(() => {
    const fetchData = async () => {
      try {
        // 从静态JSON文件获取数据（可由GitHub Actions定时更新）
        const response = await fetch('/data/market-data.json');
        const result = await response.json();
        
        if (result.data) {
          // 将API数据格式转换为组件期望的格式
          const apiData = result.data;
          const metaData = result.meta || {};
          // 用真实数据替换全部字段（真实数据覆盖，否则为NA）
          setData(formatApiData(apiData, metaData));
          setLastUpdate(result.timestamp || new Date().toLocaleString());
        }
      } catch (error) {
        console.error('获取数据失败:', error);
        // 使用默认数据
      } finally {
        setLoading(false);
      }
    };

    // 格式化API数据为组件格式
    // 关键：先设置所有字段为NA，再只覆盖有真实数据的字段
    const formatApiData = (apiData: any, metaData: any = {}): MetricData => {
      // 从defaultData深拷贝
      const result = JSON.parse(JSON.stringify(defaultData));
      
      // 30指标v3.0：真实数据源的字段（精简版）
      const realDataFields = [
        // 维度1: 宏观经济（11个）
        'gdp', 'cpi', 'pmi', 'servicePmi', 'ppi', 'interest', 'retail', 'socialFinance', 'export', 'm2', 'unemployment',
        'nonfarm', 'corePCE',
        // 维度2: 地缘政治（1个）
        'epu',
        // 维度3: 生产生活（3个）
        'electricity', 'retail', 'property',
        // 维度4: 流动性（6个有数据）
        'northbound', 'southbound', 'fedBalance', 'dollarIndex', 'cny', 'us10y',
        // 维度5: 市场情绪（5个有数据）
        'vix', 'margin', 'turnover', 'fundPosition', 'etfFlow',
        // 维度6: 供应链（3个有数据）
        'oil', 'bdi', 'export',
        // 维度7: 人口结构（1个）
        'leverageRate',
        // 维度8: 尾部风险（1个）
        'foodIndex',
      ];
      const globeFields = ['oil', 'bdi', 'us10y', 'dollarIndex', 'epu'];
      const usaFields = ['vix', 'unemployment', 'nonfarm', 'corePCE'];
      
      // 首先将所有字段设置为NA（遍历result的所有key）
      Object.keys(result).forEach(key => {
        (result as any)[key] = { value: "NA", country: (result as any)[key].country };
      });
      
      // 然后用真实数据覆盖
      realDataFields.forEach(key => {
        if (apiData[key] !== undefined && apiData[key] !== null && apiData[key] !== "NA") {
          let country = '🇨🇳';
          if (globeFields.includes(key)) country = '🌐';
          if (usaFields.includes(key)) country = '🇺🇸';
          // 合并值和meta数据
          const meta = metaData[key] || {};
          (result as any)[key] = { 
            value: apiData[key], 
            country,
            date: meta.date || null,
            dateLabel: meta.dateLabel || '-',
            yoy: meta.yoy,
            yoyLabel: meta.yoyLabel || '-',
            mom: meta.mom,
            momLabel: meta.momLabel || '-',
          };
        }
      });
      
      return result;
    };

    fetchData();

    // 每小时自动刷新数据
    const interval = setInterval(fetchData, 3600000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-[#0D1117] min-h-screen">
      {loading ? (
        <div className="flex items-center justify-center h-screen">
          <div className="text-[#8B949E]">加载中...</div>
        </div>
      ) : (
        <Dashboard data={data} lastUpdate={lastUpdate} />
      )}
    </div>
  );
}

export default App;
