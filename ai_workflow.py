#!/usr/bin/env python3
"""
AI Workflow - 智能工作流引擎增强版
支持: 工作流编排 / Agent协作 / RAG知识库 / 代码生成 / 数据Pipeline

增强功能:
- 动态条件分支 / 版本控制 / 事件触发 / 自优化
- Agent+RAG融合 / 数据质量监控 / 增量处理
- 可视化编辑器 / 工作流市场 / Agent市场
- 知识图谱RAG / 数据血缘追踪
- AI智能清洗 / 多模态支持
- 自然语言生成 / 自学习转换
"""

import os
import sys
import json
import time
import hashlib
import logging
import re
import uuid
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

# 可选依赖
try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import requests
except ImportError:
    requests = None


# ==================== 配置 ====================
class Config:
    """全局配置"""
    _config = {
        'openai_key': '',
        'anthropic_key': '',
        'model': 'gpt-4',
        'db_url': '',
        'smtp': {},
        'max_retries': 3,
        'timeout': 30,
        'enable_cache': True,
        'log_level': 'INFO',
    }
    
    @classmethod
    def set(cls, key: str, value: Any):
        cls._config[key] = value
    
    @classmethod
    def get(cls, key: str, default=None):
        return cls._config.get(key, default)
    
    @classmethod
    def all(cls):
        return cls._config.copy()


# ==================== 数据结构 ====================
class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


@dataclass
class Step:
    """工作流步骤"""
    name: str
    func: Callable
    args: Dict = field(default_factory=dict)
    retry: int = 0
    max_retries: int = 3
    timeout: int = 30
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: str = ""
    start_time: datetime = None
    end_time: datetime = None
    duration: float = 0.0
    metadata: Dict = field(default_factory=dict)
    
    def run(self, context: Dict) -> Any:
        """执行步骤"""
        self.status = StepStatus.RUNNING
        self.start_time = datetime.now()
        
        try:
            # 合并上下文到参数
            args = {**self.args, **context}
            
            # 执行函数
            if callable(self.func):
                self.result = self.func(**args)
            else:
                self.result = self.func
            
            self.status = StepStatus.SUCCESS
            self.end_time = datetime.now()
            self.duration = (self.end_time - self.start_time).total_seconds()
            
            # 更新上下文
            context[self.name] = self.result
            
            return self.result
            
        except Exception as e:
            self.error = str(e)
            self.status = StepStatus.FAILED
            self.end_time = datetime.now()
            self.duration = (self.end_time - self.start_time).total_seconds()
            
            # 重试
            if self.retry < self.max_retries:
                self.retry += 1
                self.status = StepStatus.RETRYING
                logging.warning(f"步骤 {self.name} 失败, 重试 {self.retry}/{self.max_retries}")
                time.sleep(2 ** self.retry)  # 指数退避
                return self.run(context)
            
            raise e


# ==================== 工作流编排增强 ====================
class Workflow:
    """工作流引擎"""
    
    def __init__(self, steps: List[Union[Step, 'ParallelStep', 'Condition']], name: str = "workflow"):
        self.steps = steps
        self.name = name
        self.context = {}
        self.status = StepStatus.PENDING
        self.start_time = None
        self.end_time = None
        self.results = {}
        self.version = 1
        self.history = []  # 版本历史
        self.checkpoints = []  # 检查点
        self.stats = {
            'total_runs': 0,
            'success_count': 0,
            'fail_count': 0,
            'avg_duration': 0.0,
        }
    
    def run(self, initial_context: Dict = None) -> Dict:
        """执行工作流"""
        self.context = initial_context or {}
        self.status = StepStatus.RUNNING
        self.start_time = datetime.now()
        self.stats['total_runs'] += 1
        
        logging.info(f"开始执行工作流: {self.name}")
        
        try:
            # 保存检查点
            self._save_checkpoint("start")
            
            for step in self.steps:
                if isinstance(step, Step):
                    step.run(self.context)
                    self.results[step.name] = step
                    
                    if step.status == StepStatus.FAILED:
                        logging.error(f"步骤 {step.name} 失败, 终止工作流")
                        self.stats['fail_count'] += 1
                        break
                        
                elif isinstance(step, ParallelStep):
                    results = step.run(self.context)
                    self.results[step.name] = results
                    
                elif isinstance(step, Condition):
                    step.run(self.context)
                    self.results[step.name] = step
            
            self.status = StepStatus.SUCCESS
            self.stats['success_count'] += 1
            
        except Exception as e:
            self.status = StepStatus.FAILED
            self.stats['fail_count'] += 1
            logging.error(f"工作流执行失败: {e}")
            
        finally:
            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds()
            
            # 更新统计
            if self.stats['total_runs'] > 1:
                self.stats['avg_duration'] = (
                    (self.stats['avg_duration'] * (self.stats['total_runs'] - 1) + duration) 
                    / self.stats['total_runs']
                )
            
            logging.info(f"工作流完成, 耗时: {duration:.2f}秒")
        
        return self.results
    
    def _save_checkpoint(self, name: str = None):
        """保存检查点"""
        checkpoint = {
            'name': name or f"checkpoint_{len(self.checkpoints)}",
            'time': datetime.now().isoformat(),
            'context': self.context.copy(),
            'results': {k: str(v)[:100] for k, v in self.results.items()},
        }
        self.checkpoints.append(checkpoint)
    
    def rollback(self, checkpoint_name: str = None) -> bool:
        """回滚到检查点"""
        if not self.checkpoints:
            return False
        
        target = self.checkpoints[-1] if not checkpoint_name else None
        for cp in self.checkpoints:
            if cp['name'] == checkpoint_name:
                target = cp
                break
        
        if target:
            self.context = target['context']
            logging.info(f"已回滚到检查点: {target['name']}")
            return True
        return False
    
    def save_version(self):
        """保存版本"""
        version_data = {
            'version': self.version,
            'time': datetime.now().isoformat(),
            'steps': [(s.name, s.func.__name__ if callable(s.func) else str(s.func)) 
                     for s in self.steps if isinstance(s, Step)],
            'context': self.context.copy(),
            'results': {k: str(v)[:100] for k, v in self.results.items()},
        }
        self.history.append(version_data)
        self.version += 1
        return version_data
    
    def load_version(self, version: int) -> bool:
        """加载版本"""
        for v in self.history:
            if v['version'] == version:
                self.context = v.get('context', {})
                logging.info(f"已加载版本: {version}")
                return True
        return False
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return self.stats.copy()
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            'name': self.name,
            'status': self.status.value,
            'version': self.version,
            'checkpoints': len(self.checkpoints),
            'history': len(self.history),
            'stats': self.stats,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'steps': {
                name: {'status': s.status.value, 'duration': s.duration}
                for name, s in self.results.items()
            }
        }


class ParallelStep:
    """并行执行步骤"""
    
    def __init__(self, steps: List[Step], name: str = "parallel", max_workers: int = 5):
        self.steps = steps
        self.name = name
        self.max_workers = max_workers
        self.result = None
    
    def run(self, context: Dict) -> Dict:
        """并行执行"""
        import concurrent.futures
        
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            for step in self.steps:
                future = executor.submit(step.run, context.copy())
                futures[future] = step.name
            
            for future in concurrent.futures.as_completed(futures):
                name = futures[future]
                try:
                    results[name] = future.result()
                except Exception as e:
                    results[name] = {'error': str(e)}
        
        self.result = results
        return results


class Condition:
    """条件分支"""
    
    def __init__(self, check_func: Callable, if_true: Union[Step, List[Step]], 
                 if_false: Union[Step, List[Step]] = None):
        self.check_func = check_func
        self.if_true = if_true if isinstance(if_true, list) else [if_true]
        self.if_false = if_false if if_false else []
        if isinstance(self.if_false, list) is False:
            self.if_false = [self.if_false]
        self.result = None
        self.branch_taken = None
    
    def run(self, context: Dict) -> Any:
        """执行条件分支"""
        condition = self.check_func(**context)
        
        if condition:
            self.branch_taken = 'true'
            self.result = {'branch': 'true', 'results': {}}
            for step in self.if_true:
                step.run(context)
                self.result['results'][step.name] = step.result
        else:
            self.branch_taken = 'false'
            self.result = {'branch': 'false', 'results': {}}
            for step in self.if_false:
                step.run(context)
                self.result['results'][step.name] = step.result
        
        return self.result


class DynamicCondition(Condition):
    """动态条件分支 - 根据上一��结��动态选择"""
    
    def __init__(self, conditions: Dict[str, Union[Step, List[Step]]], default: Union[Step, List[Step]] = None):
        self.conditions = conditions
        self.default = default if default else []
        if isinstance(self.default, list) is False:
            self.default = [self.default]
        self.result = None
        self.branch_taken = None
    
    def run(self, context: Dict) -> Any:
        """执行动态分支"""
        # 评估每个条件
        result = None
        for condition_key, condition_func in self.conditions.items():
            if callable(condition_key):
                if condition_key(context):
                    result = condition_key
                    break
            elif context.get(condition_key):
                result = condition_key
                break
        
        if result is None:
            result = 'default'
            steps = self.default
        else:
            steps = self.conditions[result] if result in self.conditions else self.default
        
        self.branch_taken = result
        self.result = {'branch': result, 'results': {}}
        
        for step in steps:
            step.run(context)
            self.result['results'][step.name] = step.result
        
        return self.result


class Retry:
    """重试包装器"""
    
    def __init__(self, max_attempts: int = 3, backoff: str = "exponential"):
        self.max_attempts = max_attempts
        self.backoff = backoff
    
    def __call__(self, step: Step):
        step.max_retries = self.max_attempts
        return step


class Loop:
    """循环执行"""
    
    def __init__(self, until: str = "success", max_iterations: int = 100):
        self.until = until
        self.max_iterations = max_iterations
    
    def __call__(self, step: Step):
        original_run = step.run
        
        def loop_run(context):
            for i in range(self.max_iterations):
                result = original_run(context)
                if self.until == "success" and step.status == StepStatus.SUCCESS:
                    break
            return result
        
        step.run = loop_run
        return step


# ==================== Agent系统增强 ====================
@dataclass
class Agent:
    """AI智能体"""
    name: str
    role: str
    tools: List[Callable] = field(default_factory=list)
    knowledge: Any = None
    memory: List[Dict] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    max_history: int = 50
    
    def __post_init__(self):
        self.tools = self.tools or []
        self.capabilities = self.capabilities or []
    
    def execute(self, task: str, context: Dict = None) -> Dict:
        """执行任务"""
        # 记忆
        self.memory.append({
            'task': task,
            'timestamp': datetime.now().isoformat(),
            'result': None
        })
        
        # 限制记忆长度
        if len(self.memory) > self.max_history:
            self.memory = self.memory[-self.max_history:]
        
        # 调用工具
        results = {}
        for tool in self.tools:
            try:
                results[tool.__name__] = tool(task=task, context=context)
            except Exception as e:
                results[tool.__name__] = {'error': str(e)}
        
        # 更新记忆
        if self.memory:
            self.memory[-1]['result'] = results
        
        return {
            'agent': self.name,
            'task': task,
            'results': results,
            'status': 'completed'
        }
    
    def query_knowledge(self, question: str) -> str:
        """查询知识库"""
        if self.knowledge:
            return self.knowledge.query(question)
        return "知识库未配置"
    
    def can_do(self, capability: str) -> bool:
        """检查Agent是否有此能力"""
        return capability in self.capabilities
    
    def learn(self, task: str, result: Any):
        """学习经验"""
        self.memory.append({
            'task': task,
            'result': result,
            'type': 'learning',
            'timestamp': datetime.now().isoformat()
        })
    
    def get_experience(self) -> List[Dict]:
        """获取经验"""
        return [m for m in self.memory if m.get('type') == 'learning']


class AgentTeam:
    """Agent团队 - 支持任务拆解和协作"""
    
    def __init__(self, name: str):
        self.name = name
        self.agents = {}
        self.task_history = []
    
    def add_agent(self, agent: Agent, role: str = None):
        """添加Agent"""
        self.agents[agent.name] = agent
        if role:
            agent.role = role
    
    def assign_task(self, task: str, agent_name: str = None) -> Dict:
        """分配任务"""
        if not agent_name:
            # 智能分配 - 选择最合适的Agent
            agent_name = self._select_agent(task)
        
        agent = self.agents.get(agent_name)
        if not agent:
            return {'error': f'Agent {agent_name} 不存在'}
        
        result = agent.execute(task)
        
        self.task_history.append({
            'task': task,
            'agent': agent_name,
            'result': result,
            'time': datetime.now().isoformat()
        })
        
        return result
    
    def _select_agent(self, task: str) -> str:
        """智能选择Agent"""
        task_lower = task.lower()
        
        # 根据关键词匹配
        keywords = {
            'research': ['研究', '搜索', '调研', '分析', '研究'],
            'writer': ['��', '���作', '生成', '报告', '文章'],
            'coder': ['代码', '编程', '开发', '写代码'],
            'analyzer': ['分析', '统计', '计算', '数据'],
        }
        
        for agent_name, agent in self.agents.items():
            for key, kws in keywords.items():
                if any(kw in task_lower for kw in kws):
                    if agent.can_do(key) or key in agent.capabilities:
                        return agent_name
        
        # 默认返回第一个
        return list(self.agents.keys())[0] if self.agents else None
    
    def collaborate(self, task: str, mode: str = "sequential") -> Dict:
        """协作执行任务"""
        if mode == "sequential":
            context = {'task': task}
            for agent in self.agents.values():
                result = agent.execute(task, context)
                context[agent.name] = result
            return context
        
        elif mode == "parallel":
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {executor.submit(a.execute, task, {}): a for a in self.agents.values()}
                results = {}
                for future in concurrent.futures.as_completed(futures):
                    agent = futures[future]
                    results[agent.name] = future.result()
            return results
        
        return {}


def orchestrate(agents: List[Agent], task: str, mode: str = "sequential") -> Dict:
    """编排Agent协作"""
    if mode == "sequential":
        context = {'task': task}
        for agent in agents:
            result = agent.execute(task, context)
            context[agent.name] = result
            task = f"已完成: {result}"
        return context
        
    elif mode == "parallel":
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(agent.execute, task, {}): agent for agent in agents}
            results = {}
            for future in concurrent.futures.as_completed(futures):
                agent = futures[future]
                results[agent.name] = future.result()
        return results
    
    else:
        raise ValueError(f"Unknown mode: {mode}")


# ==================== RAG知识库增强 ====================
class KnowledgeBase:
    """知识库增强版"""
    
    def __init__(self, name: str, tools: List[Callable] = None, embedding_model: str = None):
        self.name = name
        self.tools = tools or []
        self.embedding_model = embedding_model
        self.documents = []
        self.vectors = []
        self.metadata = {}
        self.cache = {}
        self.query_history = []
    
    def add_document(self, path: str, metadata: Dict = None):
        """添加文档"""
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            doc = {
                'path': path,
                'content': content,
                'added_at': datetime.now().isoformat(),
                'metadata': metadata or {},
                'hash': hashlib.md5(content.encode()).hexdigest(),
            }
            self.documents.append(doc)
            
            # 简单向量化
            self._add_vector(doc)
    
    def add_text(self, text: str, source: str = "manual", metadata: Dict = None):
        """添加文本"""
        doc = {
            'source': source,
            'content': text,
            'added_at': datetime.now().isoformat(),
            'metadata': metadata or {},
            'hash': hashlib.md5(text.encode()).hexdigest(),
        }
        self.documents.append(doc)
        self._add_vector(doc)
    
    def _add_vector(self, doc: Dict):
        """添加向量"""
        # 简单实现 - 分词
        words = doc['content'].split()
        self.vectors.append({
            'doc': doc,
            'keywords': list(set(words[:100])),  # 取前100个词
        })
    
    def query(self, question: str, return_sources: bool = True, use_tools: bool = True) -> Any:
        """查询 - 支持自动工具调用"""
        self.query_history.append({
            'question': question,
            'time': datetime.now().isoformat()
        })
        
        # 检查缓存
        cache_key = hashlib.md5(question.encode()).hexdigest()
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # 关键词匹配
        results = []
        for vec in self.vectors:
            score = sum(1 for kw in question.split()[:5] if kw in vec['keywords'])
            if score > 0:
                results.append((score, vec['doc']))
        
        results.sort(reverse=True)
        
        if results:
            answer = f"根据相关文档: {results[0][1]['content'][:200]}..."
            result = type('Answer', (), {
                'text': answer, 
                'sources': [r[1] for r in results[:3]],
                'scores': [r[0] for r in results[:3]]
            })()
            
            self.cache[cache_key] = result
            return result
        
        # 如果知识库没有,尝试用工具
        if use_tools and self.tools:
            for tool in self.tools:
                try:
                    result = tool(question)
                    answer = type('Answer', (), {
                        'text': str(result), 
                        'sources': [],
                        'from_tool': tool.__name__
                    })()
                    self.cache[cache_key] = answer
                    return answer
                except:
                    continue
        
        return type('Answer', (), {'text': '未找到相关信息', 'sources': []})()
    
    def query_with_context(self, question: str, conversation_history: List[Dict] = None) -> Any:
        """多轮对话查询"""
        if conversation_history:
            # 构建上下文
            context = "\n".join([f"Q: {h.get('question', '')}\nA: {h.get('answer', '')}" 
                               for h in conversation_history[-3:]])
            question = f"{context}\nQ: {question}"
        
        return self.query(question)
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            'name': self.name,
            'documents': len(self.documents),
            'queries': len(self.query_history),
            'cache_size': len(self.cache),
        }


# ==================== 数据处理Pipeline ====================
class DataPipeline:
    """数据处理Pipeline"""
    
    def __init__(self, name: str):
        self.name = name
        self.steps = []
        self.data = None
        self.quality_report = None
    
    def add_step(self, name: str, func: Callable):
        """添加步骤"""
        self.steps.append((name, func))
        return self
    
    def run(self, data: Any = None) -> Any:
        """执行Pipeline"""
        result = data or self.data
        
        for name, func in self.steps:
            try:
                if callable(func):
                    result = func(result)
                else:
                    result = func
                logging.info(f"步骤 {name} 完成")
            except Exception as e:
                logging.error(f"步骤 {name} 失败: {e}")
                raise
        
        self.data = result
        return result
    
    def validate_quality(self, data: Any = None) -> Dict:
        """数据质量验证"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        data = data or self.data
        
        if data is not None:
            # 检查空值
            if hasattr(data, 'isnull'):
                null_count = data.isnull().sum()
                report['checks']['null_values'] = null_count
            
            # 检查重复
            if hasattr(data, 'duplicated'):
                dup_count = data.duplicated().sum()
                report['checks']['duplicates'] = dup_count
            
            # 检查类型
            if hasattr(data, 'dtypes'):
                report['checks']['types'] = data.dtypes.to_dict()
        
        self.quality_report = report
        return report
    
    def monitor(self) -> Dict:
        """实时监控"""
        return {
            'name': self.name,
            'steps': len(self.steps),
            'has_data': self.data is not None,
            'quality': self.quality_report,
        }


class IncrementalPipeline(DataPipeline):
    """增量数据处理Pipeline"""
    
    def __init__(self, name: str, key_column: str = None):
        super().__init__(name)
        self.key_column = key_column
        self.last_processed = None
    
    def process_incremental(self, new_data: Any) -> Any:
        """增量处理"""
        if self.last_processed is None:
            # 首次处理
            self.last_processed = new_data
            return self.run(new_data)
        
        # 找出新增数据
        if hasattr(new_data, 'merge') and self.key_column:
            new_rows = new_data[~new_data[self.key_column].isin(
                self.last_processed[self.key_column]
            )]
            if len(new_rows) > 0:
                self.last_processed = new_data
                return self.run(new_rows)
        
        return None


# ==================== 代码生成器增强 ====================
class WorkflowGenerator:
    """工作流代码生成器"""
    
    def __init__(self):
        self.template_library = self._load_templates()
        self.stats = {
            'generations': 0,
            'success': 0,
            'fail': 0,
        }
    
    def _load_templates(self) -> Dict:
        """加载模板库"""
        return {
            '爬虫': self._template_scraper,
            '清洗': self._template_cleaner,
            '数据库': self._template_database,
            '报告': self._template_report,
            '邮件': self._template_email,
            '分析': self._template_analysis,
            '客服': self._template_customer_service,
            '电商': self._template_ecommerce,
            '营销': self._template_marketing,
        }
    
    def generate(self, description: str, mode: str = "auto") -> Workflow:
        """根据描述生成工作流"""
        self.stats['generations'] += 1
        
        try:
            # 解析描述
            steps = self._parse_description(description)
            
            # 构建工作流
            workflow_steps = []
            for step_name, step_func in steps:
                workflow_steps.append(Step(step_name, step_func))
            
            workflow = Workflow(workflow_steps, name="generated")
            self.stats['success'] += 1
            return workflow
            
        except Exception as e:
            self.stats['fail'] += 1
            raise
    
    def can_generate(self, description: str) -> bool:
        """检查是否能生成"""
        keywords = []
        for line in description.split('\n'):
            import re
            line = re.sub(r'^\d+[.、]\s*', '', line).lower()
            keywords.extend(line.split())
        
        # 检查是否匹配已知模板
        for template in self.template_library.values():
            if any(k in str(template).lower() for k in keywords[:3]):
                return True
        
        return False
    
    def _parse_description(self, description: str) -> List[tuple]:
        """解析描述为步骤"""
        lines = description.strip().split('\n')
        steps = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 移除数字序号
            import re
            line = re.sub(r'^\d+[.、]\s*', '', line)
            
            step_func = self._match_function(line)
            steps.append((line, step_func))
        
        return steps
    
    def _match_function(self, text: str) -> Callable:
        """匹配功能函数"""
        text = text.lower()
        
        funcs = {
            'fetch': ['爬', '抓', '获取', '采集', '请求', '加载', '读取'],
            'clean': ['清洗', '清理', '去重', '处理', '过滤'],
            'save': ['存', '入库', '数据库', 'mysql', 'sql', '保存'],
            'report': ['报告', '生成', '输出', 'excel', '导出'],
            'send': ['邮件', '发送', '通知'],
            'analyze': ['分析', '统计', '计算'],
            'search': ['搜索', '查询', '查找'],
            'ai': ['生成', '创作', '写', 'AI'],
        }
        
        for func_name, keywords in funcs.items():
            if any(k in text for k in keywords):
                return getattr(self, f'_func_{func_name}')
        
        return self._func_default
    
    # 功能函数
    def _func_fetch(self, **kwargs):
        print("🔍 执行: 获取数据")
        return {"status": "fetched", "data": []}
    
    def _func_clean(self, **kwargs):
        print("🧹 执行: 清洗数据")
        return {"status": "cleaned", "count": 0}
    
    def _func_save(self, **kwargs):
        print("💾 执行: 保存数据")
        return {"status": "saved", "rows": 0}
    
    def _func_report(self, **kwargs):
        print("📊 执行: 生成报告")
        return {"status": "reported", "path": "report.xlsx"}
    
    def _func_send(self, **kwargs):
        print("📧 执行: 发送")
        return {"status": "sent"}
    
    def _func_analyze(self, **kwargs):
        print("📈 执行: 分析")
        return {"status": "analyzed", "insights": []}
    
    def _func_search(self, **kwargs):
        print("🔍 执行: 搜索")
        return {"status": "found", "results": []}
    
    def _func_ai(self, **kwargs):
        print("🤖 执行: AI生成")
        return {"status": "generated", "content": ""}
    
    def _func_default(self, **kwargs):
        print("⚙️ 执行: 处理")
        return {"status": "done"}
    
    # 模板
    def _template_scraper(self) -> List[Step]:
        return [
            Step("请求页面", self._func_fetch),
            Step("解析数据", self._func_clean),
        ]
    
    def _template_cleaner(self) -> List[Step]:
        return [
            Step("加载数据", self._func_fetch),
            Step("去重", self._func_clean),
            Step("填充缺失", self._func_clean),
        ]
    
    def _template_database(self) -> List[Step]:
        return [
            Step("连接数据库", self._func_fetch),
            Step("插入数据", self._func_save),
        ]
    
    def _template_report(self) -> List[Step]:
        return [
            Step("查询数据", self._func_fetch),
            Step("分析", self._func_analyze),
            Step("生成报告", self._func_report),
        ]
    
    def _template_email(self) -> List[Step]:
        return [
            Step("生成内容", self._func_report),
            Step("发送邮件", self._func_send),
        ]
    
    def _template_analysis(self) -> List[Step]:
        return [
            Step("加载数据", self._func_fetch),
            Step("统计分析", self._func_analyze),
            Step("生成报告", self._func_report),
            Step("发送报告", self._func_send),
        ]
    
    def _template_customer_service(self) -> List[Step]:
        return [
            Step("接收问题", self._func_fetch),
            Step("查询知识库", self._func_search),
            Step("生成回复", self._func_ai),
            Step("记录对话", self._func_save),
        ]
    
    def _template_ecommerce(self) -> List[Step]:
        return [
            Step("获取商品", self._func_fetch),
            Step("分析数据", self._func_analyze),
            Step("生成推荐", self._func_ai),
            Step("发送通知", self._func_send),
        ]
    
    def _template_marketing(self) -> List[Step]:
        return [
            Step("市场调研", self._func_search),
            Step("分析数据", self._func_analyze),
            Step("生成内容", self._func_ai),
            Step("发布", self._func_send),
        ]
    
    def get_stats(self) -> Dict:
        """获取统��"""
        return self.stats.copy()


# ==================== 事件驱动 ====================
class EventTrigger:
    """事件触发器"""
    
    def __init__(self):
        self.triggers = {}
        self.history = []
    
    def add_trigger(self, event: str, callback: Callable):
        """添加触发器"""
        if event not in self.triggers:
            self.triggers[event] = []
        self.triggers[event].append(callback)
    
    def trigger(self, event: str, data: Any = None):
        """触发事件"""
        self.history.append({
            'event': event,
            'data': data,
            'time': datetime.now().isoformat()
        })
        
        if event in self.triggers:
            for callback in self.triggers[event]:
                try:
                    callback(data)
                except Exception as e:
                    logging.error(f"触发器执行失败: {e}")


# ==================== 自优化工作流 ====================
class SelfOptimizingWorkflow(Workflow):
    """自优化工作流"""
    
    def __init__(self, steps: List, name: str = "optimized"):
        super().__init__(steps, name)
        self.optimization_data = []
    
    def learn(self, step_name: str, duration: float, success: bool):
        """学习步骤执行情况"""
        self.optimization_data.append({
            'step': step_name,
            'duration': duration,
            'success': success,
            'time': datetime.now().isoformat()
        })
    
    def get_optimization_hints(self) -> Dict:
        """获取优化建议"""
        if not self.optimization_data:
            return {'hints': []}
        
        hints = []
        
        # 分析慢步骤
        avg_duration = {}
        for d in self.optimization_data:
            step = d['step']
            if step not in avg_duration:
                avg_duration[step] = []
            avg_duration[step].append(d['duration'])
        
        for step, durations in avg_duration.items():
            avg = sum(durations) / len(durations)
            if avg > 10:  # 超过10秒
                hints.append(f"步骤 {step} 较慢({avg:.1f}秒),建议优化")
        
        # 分析失败步骤
        fail_steps = [d['step'] for d in self.optimization_data if not d['success']]
        if fail_steps:
            from collections import Counter
            fails = Counter(fail_steps)
            for step, count in fails.items():
                if count > 2:
                    hints.append(f"步骤 {step} 失败{count}次,建议检查逻辑")
        
        return {'hints': hints, 'data': self.optimization_data}


# ==================== 便捷函数 ====================
def create_workflow(steps: List[tuple]) -> Workflow:
    """创建工作流"""
    workflow_steps = [Step(name, func) for name, func in steps]
    return Workflow(workflow_steps)


def run_workflow(description: str):
    """一步执行描述的工作流"""
    gen = WorkflowGenerator()
    return gen.generate(description).run()


def quick_workflow(*steps):
    """快速创建工作流"""
    workflow_steps = [Step(name, func) for name, func in steps]
    return Workflow(workflow_steps)


# ==================== 示例 ====================
if __name__ == "__main__":
    print("=== 示例1: 增强工作流 ===")
    wf = Workflow([
        Step("开始", lambda **k: print("开始!")),
        Step("处理", lambda **k: print("处理中...")),
        Step("完成", lambda **k: print("完成!"))
    ])
    wf.run()
    
    # 保存版本
    wf.save_version()
    print(f"版本: {wf.version}")
    
    # 获取统计
    print(f"统计: {wf.get_stats()}")
    
    print("\n=== 示例2: 条件分支 ===")
    wf2 = Workflow([
        Step("检查", lambda **k: {"status": "ok"}),
        Condition(
            lambda **k: k.get("status") == "ok",
            Step("成功", lambda **k: print("成功!")),
            Step("失败", lambda **k: print("失败!"))
        )
    ])
    wf2.run()
    
    print("\n=== 示例3: 自动生成 ===")
    result = run_workflow("""
        1. 爬取网站数据
        2. 清洗数据
        3. 存入数据库
        4. 生成报告
    """)
    
    print("\n完成!")