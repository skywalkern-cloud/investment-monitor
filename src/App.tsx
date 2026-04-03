import { useState, useEffect } from 'react'
import { useMarketData, MarketDataSkeleton } from './hooks/useMarketData'
import './index.css'

interface Indicator {
  id: string
  name: string
  value: string
  date: string
  yoy: string
  qoq: string
  region: string
  warningLevel: string | null
}

interface Dimension {
  id: string
  name: string
  icon: string
  indicators: Indicator[]
}

interface MarketData {
  lastUpdate: string
  warningCounts: {
    level1: number
    level2: number
    level3: number
  }
  dimensions: Dimension[]
  decision: {
    liquidity: string
    risk: string
    techTrend: string
    climate: string
    liquidityScore: number
    riskScore: number
    techTrendScore: number
    climateScore: number
    position: string
    mainDirection: string
    avoidDirection: string
  }
}

const WARNING_BORDER_COLORS = {
  level1: 'border-red-500',
  level2: 'border-yellow-500',
  level3: 'border-blue-500',
}

function App() {
  const { data: rawData, isLoading, isStale, error, refetch } = useMarketData()
  const [data, setData] = useState<MarketData | null>(null)

  // 数据转换
  useEffect(() => {
    if (rawData) {
      setData(transformData(rawData))
    }
  }, [rawData])

  if (isLoading || !data) {
    return <MarketDataSkeleton />
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4">
      {/* Header */}
      <header className="text-center mb-6">
        <h1 className="text-3xl font-bold mb-2">📊 WorldOS 全球运行监控系统</h1>
        <div className="flex items-center justify-center gap-4">
          <p className="text-gray-400">最后更新时间：{data.lastUpdate}</p>
          {isStale && (
            <span className="px-2 py-1 text-xs bg-yellow-500/20 text-yellow-400 rounded flex items-center gap-1">
              ⚠️ 数据超过2分钟未更新
            </span>
          )}
          {error && (
            <span className="px-2 py-1 text-xs bg-red-500/20 text-red-400 rounded">
              刷新失败，点击重试
            </span>
          )}
        </div>
        <div className="mt-2">
          <button 
            onClick={refetch}
            className="text-xs text-gray-500 hover:text-gray-300 underline"
          >
            手动刷新
          </button>
        </div>
      </header>

      {/* Warning Summary */}
      <div className="flex justify-center gap-8 mb-6">
        <div className="flex items-center gap-2">
          <span className="w-4 h-4 rounded-full bg-red-500"></span>
          <span>一级预警：{data.warningCounts.level1}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-4 h-4 rounded-full bg-yellow-500"></span>
          <span>二级预警：{data.warningCounts.level2}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-4 h-4 rounded-full bg-blue-500"></span>
          <span>三级预警：{data.warningCounts.level3}</span>
        </div>
      </div>

      {/* 6-Grid Layout - 3列2行六宫格 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {data.dimensions.map(dim => (
          <DimensionCard key={dim.id} dimension={dim} />
        ))}
      </div>

      {/* Decision Support */}
      <DecisionSection decision={data.decision} />
    </div>
  )
}

function DimensionCard({ dimension }: { dimension: Dimension }) {
  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <h2 className="text-xl font-semibold mb-3 flex items-center gap-2">
        <span>{dimension.icon}</span>
        <span>【{dimension.name}】</span>
      </h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-400 border-b border-gray-700">
              <th className="text-left py-2 pr-2">指标</th>
              <th className="text-right py-2 px-2">数值</th>
              <th className="text-right py-2 px-2">日期</th>
              <th className="text-right py-2 px-2">同比</th>
              <th className="text-right py-2 px-2">环比</th>
            </tr>
          </thead>
          <tbody>
            {dimension.indicators.map(ind => (
              <IndicatorRow key={ind.id} indicator={ind} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function IndicatorRow({ indicator }: { indicator: Indicator }) {
  const warningLevel = indicator.warningLevel
  const warningClass = warningLevel 
    ? `border-l-4 ${WARNING_BORDER_COLORS[warningLevel as keyof typeof WARNING_BORDER_COLORS]}` 
    : ''

  return (
    <tr className={`border-b border-gray-700/50 hover:bg-gray-700/30 ${warningClass}`}>
      <td className="py-2 pr-2">
        <div className="flex items-center gap-2">
          <span className="text-xs">{indicator.region}</span>
          <span>{indicator.name}</span>
          {warningLevel === 'level1' && (
            <span className="px-1.5 py-0.5 text-xs bg-red-500/20 text-red-400 rounded">高</span>
          )}
          {warningLevel === 'level2' && (
            <span className="px-1.5 py-0.5 text-xs bg-yellow-500/20 text-yellow-400 rounded">中</span>
          )}
          {warningLevel === 'level3' && (
            <span className="px-1.5 py-0.5 text-xs bg-blue-500/20 text-blue-400 rounded">低</span>
          )}
        </div>
      </td>
      <td className="text-right py-2 px-2 font-mono font-medium">{indicator.value}</td>
      <td className="text-right py-2 px-2 text-gray-400">{indicator.date}</td>
      <td className={`text-right py-2 px-2 ${parseYoY(indicator.yoy) > 0 ? 'text-green-400' : parseYoY(indicator.yoy) < 0 ? 'text-red-400' : 'text-gray-400'}`}>
        {indicator.yoy}
      </td>
      <td className={`text-right py-2 px-2 ${parseYoY(indicator.qoq) > 0 ? 'text-green-400' : parseYoY(indicator.qoq) < 0 ? 'text-red-400' : 'text-gray-400'}`}>
        {indicator.qoq}
      </td>
    </tr>
  )
}

function parseYoY(val: string): number {
  if (val === '-' || !val) return 0
  const num = parseFloat(val.replace('%', '').replace('bp', ''))
  return isNaN(num) ? 0 : num
}

// 数据转换函数：将原始 market-data.json 转换为 App 期望的格式
function transformData(raw: any): MarketData {
  const data = raw.data || {}
  const meta = raw.meta || {}
  
  // 龙六设计：6大维度24指标
  const dimensionConfigs = [
    { id: 'economic', name: '经济产出', icon: '📈', fields: [
      { key: 'gdp', name: '中国GDP增速', region: '🇨🇳' },
      { key: 'pmi', name: '中国PMI', region: '🇨🇳' },
      { key: 'nonfarm', name: '美国GDP增速', region: '🇺🇸' },
      { key: 'servicePmi', name: '服务业PMI', region: '🇨🇳' }
    ]},
    { id: 'inflation', name: '通胀与价格', icon: '💰', fields: [
      { key: 'cpi', name: 'CPI同比', region: '🇨🇳' },
      { key: 'ppi', name: 'PPI同比', region: '🇨🇳' },
      { key: 'usCPI', name: '美国CPI', region: '🇺🇸' },
      { key: 'corePCE', name: '核心PCE', region: '🇺🇸' }
    ]},
    { id: 'money', name: '货币与信用', icon: '🏦', fields: [
      { key: 'interest', name: 'LPR', region: '🇨🇳' },
      { key: 'cny', name: '人民币汇率', region: '🇨🇳' },
      { key: 'm2', name: 'M2增速', region: '🇨🇳' },
      { key: 'fedRate', name: '美联储利率', region: '🇺🇸' }
    ]},
    { id: 'risk', name: '风险与不确定性', icon: '⚠️', fields: [
      { key: 'vix', name: 'VIX指数', region: '🌐' },
      { key: 'epu', name: 'EPU指数', region: '🌐' },
      { key: 'dollarIndex', name: '美元指数', region: '🇺🇸' },
      { key: 'riskLevel', name: '地缘风险', region: '🌐' }
    ]},
    { id: 'tech', name: '技术与生产力', icon: '🔬', fields: [
      { key: 'aiRdRatio', name: 'AI研发占比', region: '🇨🇳' },
      { key: 'aiPatentCount', name: 'AI专利数', region: '🇨🇳' },
      { key: 'robotInstallBase', name: '机器人保有量', region: '🇨🇳' },
      { key: 'quantumComputingBudget', name: '量子计算预算', region: '🌐' }
    ]},
    { id: 'climate', name: '气候与资源', icon: '🌍', fields: [
      { key: 'oil', name: 'WTI原油', region: '🌐' },
      { key: 'gold', name: '黄金价格', region: '🌐' },
      { key: 'copper', name: '伦铜', region: '🌐' },
      { key: 'electricity', name: '用电量', region: '🇨🇳' }
    ]}
  ]
  
  const dimensions: Dimension[] = dimensionConfigs.map(dim => {
    const indicators: Indicator[] = dim.fields.map(field => {
      const rawValue = data[field.key]
      const fieldMeta = meta[field.key] || {}
      
      // 处理值显示
      let displayValue = '-'
      if (rawValue !== undefined && rawValue !== 'NA') {
        if (typeof rawValue === 'number') {
          // 大数值格式化
          if (rawValue >= 1e9) displayValue = (rawValue / 1e9).toFixed(1) + '亿'
          else if (rawValue >= 1e6) displayValue = (rawValue / 1e6).toFixed(1) + '万'
          else displayValue = rawValue.toFixed(2)
        } else {
          displayValue = String(rawValue)
        }
      }
      
      return {
        id: field.key,
        name: field.name,
        value: displayValue,
        date: fieldMeta.dateLabel || '-',
        yoy: fieldMeta.yoyLabel || '-',
        qoq: fieldMeta.momLabel || '-',
        region: field.region,
        warningLevel: null
      }
    })
    
    return { id: dim.id, name: dim.name, icon: dim.icon, indicators }
  })
  
  // 预警计算
  let level1 = 0, level2 = 0, level3 = 0
  
  // VIX > 30 一级预警
  if (data.vix && data.vix > 30) level1++
  // EPU > 500 二级预警
  if (data.epu && data.epu > 500) level2++
  // 油价 > 100 二级预警
  if (data.oil && data.oil > 100) level2++
  
  return {
    lastUpdate: raw.timestamp || '-',
    warningCounts: { level1, level2, level3 },
    dimensions,
    decision: {
      liquidity: data.m2 && data.m2 > 10 ? '宽松' : '适中',
      risk: level1 > 0 ? '偏高' : level2 > 0 ? '中等' : '可控',
      techTrend: data.aiRdRatio && data.aiRdRatio > 10 ? '向好' : '观望',
      climate: data.oil && data.oil > 100 ? '震荡' : '平稳',
      liquidityScore: data.m2 && data.m2 > 10 ? 4 : 3,
      riskScore: level1 > 0 ? 2 : level2 > 0 ? 3 : 4,
      techTrendScore: data.aiRdRatio && data.aiRdRatio > 10 ? 4 : 3,
      climateScore: data.oil && data.oil > 100 ? 2 : 4,
      position: level1 > 0 ? '防守' : '进攻',
      mainDirection: '科技/新能源',
      avoidDirection: '传统能源'
    }
  }
}

function DecisionSection({ decision }: { decision: MarketData['decision'] }) {
  const renderStars = (score: number) => {
    return '★'.repeat(score) + '☆'.repeat(5 - score)
  }

  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <h2 className="text-xl font-semibold mb-4">【投资决策建议】</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <DecisionCard title="流动性" value={decision.liquidity} score={decision.liquidityScore} renderStars={renderStars} />
        <DecisionCard title="风险" value={decision.risk} score={decision.riskScore} renderStars={renderStars} />
        <DecisionCard title="技术趋势" value={decision.techTrend} score={decision.techTrendScore} renderStars={renderStars} />
        <DecisionCard title="气候" value={decision.climate} score={decision.climateScore} renderStars={renderStars} />
      </div>
      <div className="space-y-2 text-lg">
        <p><span className="text-yellow-400">📈 仓位建议：</span>{decision.position}</p>
        <p><span className="text-green-400">🎯 主线方向：</span>{decision.mainDirection}</p>
        <p><span className="text-red-400">⚠️ 规避方向：</span>{decision.avoidDirection}</p>
      </div>
    </div>
  )
}

function DecisionCard({ title, value, score, renderStars }: { title: string, value: string, score: number, renderStars: (n: number) => string }) {
  return (
    <div className="bg-gray-700/50 rounded p-3 text-center">
      <div className="text-gray-400 text-sm">{title}</div>
      <div className="font-medium mb-1">{value}</div>
      <div className="text-yellow-400 text-sm">{renderStars(score)}</div>
    </div>
  )
}

export default App
