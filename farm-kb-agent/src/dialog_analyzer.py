"""
对话分析模块
分析客服对话，识别问题和知识缺口
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class DialogTurn:
    """对话轮次"""
    role: str  # "customer" 或 "agent"
    content: str
    timestamp: str


@dataclass
class Conversation:
    """对话记录"""
    id: str
    customer_id: str
    turns: List[DialogTurn]
    start_time: str
    end_time: Optional[str] = None
    resolved: bool = False
    satisfaction: Optional[int] = None  # 1-5 评分
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "turns": [{"role": t.role, "content": t.content, "timestamp": t.timestamp} for t in self.turns],
            "start_time": self.start_time,
            "end_time": self.end_time,
            "resolved": self.resolved,
            "satisfaction": self.satisfaction,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Conversation":
        turns = [DialogTurn(t["role"], t["content"], t["timestamp"]) for t in data["turns"]]
        return cls(
            id=data["id"],
            customer_id=data["customer_id"],
            turns=turns,
            start_time=data["start_time"],
            end_time=data.get("end_time"),
            resolved=data.get("resolved", False),
            satisfaction=data.get("satisfaction"),
            tags=data.get("tags", [])
        )
    
    def get_customer_questions(self) -> List[str]:
        """获取客户所有问题"""
        return [t.content for t in self.turns if t.role == "customer"]
    
    def get_agent_responses(self) -> List[str]:
        """获取客服所有回复"""
        return [t.content for t in self.turns if t.role == "agent"]


class ConversationStore:
    """对话存储"""
    
    def __init__(self, path: str = "data/conversations.json"):
        self.path = path
        self.conversations = self._load()
    
    def _load(self) -> List[Conversation]:
        """加载对话记录"""
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [Conversation.from_dict(c) for c in data.get("conversations", [])]
        return []
    
    def _save(self):
        """保存对话记录"""
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump({
                "conversations": [c.to_dict() for c in self.conversations]
            }, f, ensure_ascii=False, indent=2)
    
    def add(self, conversation: Conversation):
        """添加对话"""
        self.conversations.append(conversation)
        self._save()
    
    def get_unresolved(self) -> List[Conversation]:
        """获取未解决的对话"""
        return [c for c in self.conversations if not c.resolved]
    
    def get_recent(self, limit: int = 10) -> List[Conversation]:
        """获取最近对话"""
        sorted_conv = sorted(self.conversations, key=lambda x: x.start_time, reverse=True)
        return sorted_conv[:limit]
    
    def get_all(self) -> List[Conversation]:
        """获取所有对话"""
        return self.conversations


class DialogAnalyzer:
    """对话分析器"""
    
    def __init__(self, store: ConversationStore):
        self.store = store
    
    def analyze_unresolved(self) -> List[Dict]:
        """
        分析未解决的对话
        返回知识缺口建议
        """
        unresolved = self.store.get_unresolved()
        gaps = []
        
        for conv in unresolved:
            questions = conv.get_customer_questions()
            for q in questions:
                gaps.append({
                    "conversation_id": conv.id,
                    "question": q,
                    "reason": "对话未解决，可能知识库缺少相关内容",
                    "suggested_action": "补充知识条目"
                })
        
        return gaps
    
    def analyze_low_satisfaction(self, threshold: int = 3) -> List[Dict]:
        """
        分析低满意度对话
        """
        low_sat = [c for c in self.store.get_all() 
                   if c.satisfaction and c.satisfaction <= threshold]
        
        issues = []
        for conv in low_sat:
            questions = conv.get_customer_questions()
            responses = conv.get_agent_responses()
            
            issues.append({
                "conversation_id": conv.id,
                "satisfaction": conv.satisfaction,
                "questions": questions,
                "responses": responses,
                "reason": f"满意度评分 {conv.satisfaction}/5，可能需要优化回答质量",
                "suggested_action": "优化现有知识条目或改进回答方式"
            })
        
        return issues
    
    def extract_frequent_questions(self, min_freq: int = 2) -> List[Dict]:
        """
        提取高频问题（简单版本：基于关键词统计）
        """
        from collections import Counter
        
        all_questions = []
        for conv in self.store.get_all():
            all_questions.extend(conv.get_customer_questions())
        
        # 简单分词统计（实际可用更好的NLP）
        word_freq = Counter()
        for q in all_questions:
            words = q.replace("？", "").replace("?", "").replace("怎么", "").replace("什么", "").split()
            for w in words:
                if len(w) >= 2:  # 只统计2字以上的词
                    word_freq[w] += 1
        
        frequent = [
            {"term": term, "count": count, "suggested_action": "确保有完善的知识条目"}
            for term, count in word_freq.most_common(10)
            if count >= min_freq
        ]
        
        return frequent
    
    def generate_report(self) -> Dict:
        """
        生成分析报告
        """
        all_conv = self.store.get_all()
        
        total = len(all_conv)
        resolved = len([c for c in all_conv if c.resolved])
        unresolved = total - resolved
        
        # 平均满意度
        satisfactions = [c.satisfaction for c in all_conv if c.satisfaction]
        avg_satisfaction = sum(satisfactions) / len(satisfactions) if satisfactions else 0
        
        return {
            "total_conversations": total,
            "resolved": resolved,
            "unresolved": unresolved,
            "resolution_rate": f"{resolved/total*100:.1f}%" if total > 0 else "0%",
            "avg_satisfaction": f"{avg_satisfaction:.1f}/5" if satisfactions else "N/A",
            "knowledge_gaps": self.analyze_unresolved(),
            "quality_issues": self.analyze_low_satisfaction(),
            "frequent_topics": self.extract_frequent_questions()
        }
