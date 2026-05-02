"""
知识库管理模块
负责知识库的增删改查
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional


class KnowledgeBaseManager:
    """知识库管理器"""
    
    def __init__(self, kb_path: str = "data/knowledge_base.json"):
        self.kb_path = kb_path
        self.data = self._load()
    
    def _load(self) -> Dict:
        """加载知识库"""
        if os.path.exists(self.kb_path):
            with open(self.kb_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"categories": [], "entries": []}
    
    def _save(self):
        """保存知识库"""
        os.makedirs(os.path.dirname(self.kb_path), exist_ok=True)
        with open(self.kb_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        搜索知识库
        简单实现：基于关键词匹配
        """
        query_words = set(query.lower().split())
        results = []
        
        for entry in self.data["entries"]:
            # 计算匹配分数
            score = 0
            
            # 问题匹配
            question_words = set(entry["question"].lower().split())
            score += len(query_words & question_words) * 2
            
            # 关键词匹配
            for kw in entry.get("keywords", []):
                if any(qw in kw.lower() or kw.lower() in qw for qw in query_words):
                    score += 3
            
            # 答案匹配
            answer_words = set(entry["answer"].lower().split())
            score += len(query_words & answer_words)
            
            if score > 0:
                results.append({
                    **entry,
                    "match_score": score
                })
        
        # 按匹配分数排序
        results.sort(key=lambda x: x["match_score"], reverse=True)
        
        # 更新命中次数
        for r in results[:top_k]:
            entry = next((e for e in self.data["entries"] if e["id"] == r["id"]), None)
            if entry:
                entry["hit_count"] = entry.get("hit_count", 0) + 1
        self._save()
        
        return results[:top_k]
    
    def get_answer(self, query: str) -> Optional[str]:
        """获取最佳答案"""
        results = self.search(query, top_k=1)
        if results and results[0]["match_score"] >= 3:
            return results[0]["answer"]
        return None
    
    def add_entry(self, category: str, question: str, answer: str, keywords: List[str] = None) -> Dict:
        """添加新知识条目"""
        entry_id = f"kb_{len(self.data['entries']) + 1:03d}"
        now = datetime.now().strftime("%Y-%m-%d")
        
        entry = {
            "id": entry_id,
            "category": category,
            "question": question,
            "keywords": keywords or [],
            "answer": answer,
            "created_at": now,
            "updated_at": now,
            "hit_count": 0
        }
        
        self.data["entries"].append(entry)
        
        # 自动添加新分类
        if category not in self.data["categories"]:
            self.data["categories"].append(category)
        
        self._save()
        return entry
    
    def update_entry(self, entry_id: str, **kwargs) -> Optional[Dict]:
        """更新知识条目"""
        entry = next((e for e in self.data["entries"] if e["id"] == entry_id), None)
        if not entry:
            return None
        
        for key, value in kwargs.items():
            if key in ["category", "question", "answer", "keywords"]:
                entry[key] = value
        
        entry["updated_at"] = datetime.now().strftime("%Y-%m-%d")
        self._save()
        return entry
    
    def delete_entry(self, entry_id: str) -> bool:
        """删除知识条目"""
        original_len = len(self.data["entries"])
        self.data["entries"] = [e for e in self.data["entries"] if e["id"] != entry_id]
        
        if len(self.data["entries"]) < original_len:
            self._save()
            return True
        return False
    
    def get_stats(self) -> Dict:
        """获取知识库统计"""
        entries = self.data["entries"]
        return {
            "total_entries": len(entries),
            "categories": len(self.data["categories"]),
            "total_hits": sum(e.get("hit_count", 0) for e in entries),
            "category_distribution": {
                cat: len([e for e in entries if e["category"] == cat])
                for cat in self.data["categories"]
            }
        }
    
    def get_low_hit_entries(self, threshold: int = 1) -> List[Dict]:
        """获取低使用率条目（可能需要优化）"""
        return [e for e in self.data["entries"] if e.get("hit_count", 0) < threshold]
    
    def list_all(self) -> List[Dict]:
        """列出所有条目"""
        return self.data["entries"]
