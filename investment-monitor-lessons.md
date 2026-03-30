# 投资监控仪表盘项目经验教训

## 日期：2026-03-29

---

## 一、项目概述

**目标**：部署龙六设计的55指标投资监控仪表盘到Vercel，接入真实数据源

**最终状态**：
- Vercel部署成功：https://investment-monitor-five.vercel.app/
- GitHub仓库：https://github.com/skywalkern-cloud/investment-monitor
- 真实数据源：6个（GDP、CPI、PMI、LPR、人民币、原油），其余显示NA

---

## 二、核心教训

### 1. 团队协作问题

| 问题 | 教训 |
|------|------|
| 龙五单独干活，没有和龙六沟通 | 重要功能变更前必须和设计者确认 |
| 没有代码审查流程 | 团队开发必须有review环节 |
| 没有本地测试就推送到生产 | 每次修改必须本地build测试通过 |

### 2. 数据显示逻辑错误

**问题**：没有数据源的字段显示预设值，而非NA

**错误代码**：
```typescript
// ❌ 错误：只处理了有真实数据的字段，其他保留defaultData的预设值
const formatApiData = (apiData: any): Partial<MetricData> => {
  const formatted: any = {};
  realDataFields.forEach(key => {
    if (apiData[key] !== "NA") {
      formatted[key] = { value: apiData[key], country };
    } else {
      formatted[key] = { value: "NA" as any, country };  // 只设置这6个，其他字段没用
    }
  });
  return formatted;
};
setData({ ...defaultData, ...formatApiData(apiData) });  // 合并后defaultData的预设值全保留了
```

**正确代码**：
```typescript
// ✅ 正确：先遍历所有55个指标设为NA，再只覆盖有真实数据的
const formatApiData = (apiData: any): MetricData => {
  const result = JSON.parse(JSON.stringify(defaultData));
  
  // 第一步：所有55个字段都设为NA
  Object.keys(result).forEach(key => {
    (result as any)[key] = { value: "NA", country: (result as any)[key].country };
  });
  
  // 第二步：只覆盖有真实数据的6个字段
  realDataFields.forEach(key => {
    if (apiData[key] !== undefined && apiData[key] !== null && apiData[key] !== "NA") {
      (result as any)[key] = { value: apiData[key], country };
    }
  });
  
  return result;
};
setData(formatApiData(apiData));  // 直接用，不用合并
```

### 3. 部署流程问题

| 问题 | 教训 |
|------|------|
| Vercel build失败多次 | 先确保本地build成功再推送 |
| 推送了dist文件夹到GitHub | 应该只推送源码，让Vercel构建 |
| 没有配置vercel.json | 静态React项目需要配置framework |

**正确部署流程**：
1. 本地`npm run build`测试通过
2. 推送源码到GitHub
3. Vercel自动检测并构建
4. 验证部署状态

---

## 三、技术要点

### React + TypeScript + Vite

- 使用`JSON.parse(JSON.stringify())`深拷贝对象
- TypeScript类型：`value: number | string | "NA"`
- Vite构建输出到`dist/`
- Vercel配置：`{"framework": "vite"}`

### 数据格式

```typescript
// 55指标的数据结构
interface LabeledMetric {
  value: number | string | "NA";
  country: CountryTag;  // '🇨🇳' | '🇺🇸' | '🌐'
}

// API返回格式
{
  "timestamp": "2026-03-29T14:00:00Z",
  "data": {
    "gdp": 5.0,
    "cpi": 1.3,
    // ...
  },
  "sources": {...}
}
```

### 静态数据更新

目前方案：
1. Python脚本从AKShare/腾讯获取数据
2. 生成`public/data/market-data.json`
3. 推送源码到GitHub
4. Vercel自动部署

未来改进：
- 使用GitHub Actions定时更新数据
- 或使用服务端API实时获取

---

## 四、Token记录

| 服务 | Token |
|------|-------|

---

## 五、检查清单

今后类似项目必须完成：

- [ ] 设计文档确认（和设计者同步）
- [ ] 本地build测试通过
- [ ] 代码review
- [ ] 推送源码（不推送dist）
- [ ] 验证Vercel部署状态
- [ ] 浏览器测试（强制刷新Ctrl+Shift+R）
- [ ] 数据显示验证（NA正确显示）

---

## 六、团队成员

- **龙五**：开发、部署
- **龙六**：设计55指标体系

---

*文档创建时间：2026-03-29*
*存放位置：GitHub /workspace-memory/investment-monitor-lessons.md*