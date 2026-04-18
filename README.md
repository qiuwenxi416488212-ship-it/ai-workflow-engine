# AI Workflow Engine
## 智能工作流自动化引擎 | 让AI工作流变得像说话一样简单

<p align="center">
  <a href="https://pypi.org/project/ai-workflow-engine/">
    <img src="https://img.shields.io/pypi/v/ai-workflow-engine" alt="PyPI">
  </a>
  <img src="https://img.shields.io/github/stars/XiLi/ai-workflow-engine" alt="Stars">
  <img src="https://img.shields.io/github/license/XiLi/ai-workflow-engine" alt="License">
  <img src="https://img.shields.io/pypi/pyversions/ai-workflow-engine" alt="Python">
</p>

---

## 📦 项目简介

**AI Workflow Engine** (智能工作流引擎) 是一套强大的AI工作流自动化框架,让AI工作流变得像说话一样简单!

> 只需用自然语言描述你的需求,AI自动生成完整的工作流代码并执行!

---

## ✨ 核心特性

### 🚀 描述即生成 (一键工作流)

```python
from ai_workflow import run_workflow

# 告诉AI你想做什么
result = run_workflow("""
    1. 爬取网站产品数据
    2. 清洗去重、填充缺失
    3. 存入MySQL数据库
    4. 生成Excel销售报表
    5. 发送到运营邮箱
""")

print(result)
# 自动生成并执行完整工作流!
```

### 🔄 完整的工作流编排

- ✅ 线性执行 - 按顺序完成任务
- ✅ 条件分支 - 根据条件选择路径
- ✅ 并行执行 - 多任务同时运行
- ✅ 循环重试 - 失败自动重试(指数退避)
- ✅ 动态分支 - 根据结果动态选择

### 🤖 智能Agent系统

- ✅ Agent角色定义 - 设定能力和边界
- ✅ AgentTeam团队 - 多Agent协作
- ✅ 任务智能分配 - 自动选择最合适的Agent
- ✅ 记忆系统 - 短期/长期记忆
- ✅ 经验学习 - 从执行中学习

### 📚 RAG知识库

- ✅ 文档向量化 - 支持PDF/Word/MD等格式
- ✅ 智能检索 - 语义搜索
- ✅ 知识图谱RAG - 关系查询和推理
- ✅ 工具调用 - 自动调用搜索/计算器
- ✅ 多轮对话 - 记住对话上下文

### 📊 数据处理Pipeline

- ✅ ETL自动化 - 抽取/转换/加载
- ✅ AI智能清洗 - 自动检测和修复异常
- ✅ 增量处理 - 只处理新增数据
- ✅ 数据血缘 - 追踪数据来源
- ✅ 质量监控 - 实时数据质量

### 🎨 可视化编辑器

- ✅ 拖拽式构建 - 无需写代码
- ✅ Web界面 - 浏览器中设计
- ✅ 代码导出 - 一键生成代码

### 🏪 模板市场

- ✅ 工作流模板 - 分享和下载
- ✅ Agent插件 - 可插拔扩展

### 🌍 多模态支持

- ✅ 图片输入 - 处理图片数据
- ✅ 音频输入 - 处理音频数据
- ✅ 视频输入 - 处理视频数据

### 🧠 智能生成

- ✅ 自然语言生成 - 描述→完整代码
- ✅ 自学习转换 - 学习用户转换规则

---

## 📦 安装

```bash
# 基础安装
pip install pandas requests

# 完整安装
pip install beautifulsoup4 openai anthropic chromadb pypdf
```

---

## 💡 快速开始

### 方式1: 描述需求 (推荐)

```python
from ai_workflow import run_workflow

result = run_workflow("""
    1. 爬取电商网站数据
    2. 清洗去重
    3. 存入MySQL
    4. 生成Excel报表
""")
```

### 方式2: 手动构建

```python
from ai_workflow import Workflow, Step, Condition, ParallelStep

wf = Workflow([
    Step("爬取数据", fetch_data),
    Condition(
        lambda **k: k.get("data"),
        Step("成功", process),
        Step("失败", retry)
    ),
    ParallelStep([
        Step("存库", save_db),
        Step("发邮件", send_email)
    ])
])

wf.run()
```

### 方式3: Agent协作

```python
from ai_workflow import Agent, orchestrate, AgentTeam

team = AgentTeam("研究团队")
team.add_agent(Agent("研究员", capabilities=["search"]))
team.add_agent(Agent("分析师", capabilities=["analyze"]))
team.add_agent(Agent("写手", capabilities=["write"]))

result = team.collaborate("分析AI行业趋势", mode="sequential")
```

### 方式4: RAG知识库

```python
from ai_workflow import KnowledgeBase

kb = KnowledgeBase("公司知识库")
kb.add_document("产品介绍.pdf")
kb.add_text("公司使命: 让AI服务每个人", source="manual")

answer = kb.query("公司的使命是什么?")
print(answer.text)
```

---

## 🏗️ 工作流模式

### 1. 线性执行
```python
wf = Workflow([
    Step("第一步", do_something),
    Step("第二步", do_next),
    Step("第三步", final_step)
])
```

### 2. 条件分支
```python
Condition(
    lambda **k: k.get("status") == "success",
    Step("成功", handle_success),
    Step("失败", handle_failure)
)
```

### 3. 并行执行
```python
ParallelStep([
    Step("任务A", task_a),
    Step("任务B", task_b),
    Step("任务C", task_c)
], max_workers=5)
```

### 4. 版本控制
```python
wf.save_version()      # 保存版本
wf.rollback()          # 回滚
wf.load_version(1)     # 加载历史版本
```

---

## 🤖 Agent示例

### 创建Agent
```python
agent = Agent(
    name="研究员",
    role="负责信息搜集和分析",
    capabilities=["search", "analyze"],
    tools=[search_web],
    knowledge=my_knowledge_base
)

# 执行任务
result = agent.execute("搜索AI最新新闻")

# 学习经验
agent.learn("某个任务", result)
```

### AgentTeam团队
```python
team = AgentTeam("项目组")
team.add_agent(Agent("研究员", capabilities=["search"]))
team.add_agent(Agent("分析师", capabilities=["analyze"]))
team.add_agent(Agent("写手", capabilities=["write"]))

# 智能分配 - 自动选择最合适的Agent
result = team.assign_task("写一篇关于AI的报告")
```

---

## 📚 RAG知识库

### 基础RAG
```python
kb = KnowledgeBase("公司知识库")
kb.add_document("产品介绍.pdf")
kb.add_document("技术文档.docx")

# 查询
answer = kb.query("公司的使命是什么?")
print(answer.text)
print(answer.sources)  # 引用来源
```

### 知识图谱RAG
```python
from ai_workflow import KnowledgeGraphRAG

kg = KnowledgeGraphRAG("公司图谱")
kg.add_entity("产品A", "product", {"price": 100})
kg.add_entity("用户A", "customer", {"level": "VIP"})
kg.add_relation("产品A", "用户A", "购买")

# 查询关系
results = kg.query_relations("产品A")
```

---

## 📊 数据Pipeline

### 基本使用
```python
from ai_workflow import DataPipeline, IncrementalPipeline, AICleaner

# 普通Pipeline
pipeline = DataPipeline("销售分析")
pipeline.add_step("清洗", clean_data)
pipeline.add_step("统计", calculate_stats)
result = pipeline.run(data)

# 增量Pipeline
inc = IncrementalPipeline("增量更新", key_column="id")
result = inc.process_incremental(new_data)

# AI智能清洗
cleaner = AICleaner()
anomalies = cleaner.detect_anomalies(data)
cleaned = cleaner.clean(data, mode='auto')
```

### 数据血缘追踪
```python
from ai_workflow import DataLineage

lineage = DataLineage()
lineage.add_source("订单表", "database")
lineage.add_transform("清洗", "订单表", "clean")
lineage.add_aggregation("统计", ["���洗"])

# 追溯来源
path = lineage.trace_back("统计")
```

---

## 🎨 可视化

### 可视化编辑器
```python
from ai_workflow import VisualEditor

editor = VisualEditor()
editor.add_step("step", "爬取数据", (100, 100))
editor.add_step("step", "清洗数据", (300, 100))
editor.connect(step1['id'], step2['id'])

# 导出代码
code = editor.export_code()
```

### Web编辑器
```python
from ai_workflow import generate_web_editor_html

html = generate_web_editor_html()
# 自动生成Web编辑器HTML
```

---

## 🏪 市场

### 工作流市场
```python
from ai_workflow import WorkflowMarket

market = WorkflowMarket()
templates = market.search("电商")
print(templates[0].description)

# 下载模板
template = market.download(template_id)
```

### Agent市场
```python
from ai_workflow import AgentMarket

market = AgentMarket()
agents = market.search("analyze")

# 安装Agent
agent = market.install(agent_id)
```

---

## 🧠 智能功能

### 自然语言代码生成
```python
from ai_workflow import NLCodeGenerator

gen = NLCodeGenerator()
code = gen.generate("""
    爬取网站数据
    清洗去重
    存入数据库
    生成报告
""")

print(code)  # 完整可运行的代码
```

### 自学习转换
```python
from ai_workflow import SelfLearningConverter

converter = SelfLearningConverter()
converter.learn(input_data, output_data)
# AI学习你的转换习惯

exported = converter.export_rules()
```

---

## ⚙️ 配置

```python
from ai_workflow import Config

# AI模型
Config.set("openai_key", "sk-xxx")
Config.set("model", "gpt-4")

# 工作流
Config.set("max_retries", 3)
Config.set("enable_cache", True)
```

---

## 📋 API参考

### 核心类

| 类 | 功能 |
|------|------|
| `Workflow` | 工作流容器 |
| `Step` | 工作流步骤 |
| `ParallelStep` | 并行执行 |
| `Condition` | 条件分支 |
| `DynamicCondition` | 动态条件 |
| `Agent` | AI智能体 |
| `AgentTeam` | Agent团队 |
| `KnowledgeBase` | RAG知识库 |
| `KnowledgeGraphRAG` | 知识图谱 |
| `DataPipeline` | 数据Pipeline |
| `IncrementalPipeline` | 增量Pipeline |
| `AICleaner` | AI清洗 |
| `DataLineage` | 数据血缘 |
| `VisualEditor` | 可视化编辑 |
| `WorkflowMarket` | 工作流市场 |
| `AgentMarket` | Agent市场 |
| `MultimodalInput` | 多模态输入 |
| `NLCodeGenerator` | 代码生成 |

### 核心函数

| 函数 | 功能 |
|------|------|
| `run_workflow()` | 描述式执行 |
| `create_workflow()` | 创建工作流 |
| `orchestrate()` | Agent编排 |

---

## 🛠️ 依赖

```
pandas
requests
beautifulsoup4

# 可选
openai
anthropic
chromadb
pypdf
```

---

## 📊 示例工作流

### 1. 电商数据采集
```python
run_workflow("""
    1. 爬取电商网站产品数据
    2. 清洗去重、填充缺失
    3. 存入MySQL数据库
    4. 生成Excel销售报表
    5. 发送到运营邮箱
""")
```

### 2. 销售数据分析
```python
run_workflow("""
    1. 从数据库读取销售数据
    2. 按品类统计分析
    3. 生成可视化图表
    4. 输出分析报告PDF
""")
```

### 3. 智能客服
```python
run_workflow("""
    1. 接收用户问题
    2. 查询FAQ知识库
    3. 如无法回答则搜索文档
    4. 生成回复内容
    5. 记录对话到数据库
""")
```

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## 📄 许可证

MIT License - 免费商用

---

## ⭐ 支持

**如果对你有帮助,欢迎 ⭐ Star 支持!**

---

<div align="center">

**让AI工作流���得���说话一样简单!**

Made with ❤️ by [XiLi](https://github.com/XiLi)

</div>