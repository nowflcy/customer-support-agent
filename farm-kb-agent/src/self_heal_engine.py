"""
自愈引擎模块
根据对话分析结果自动修复知识库
"""

import os
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class HealSuggestion:
    """修复建议"""
    type: str  # "add", "update", "merge"
    reason: str
    priority: str  # "high", "medium", "low"
    details: Dict
    auto_applicable: bool  # 是否可以自动应用


class SelfHealEngine:
    """知识库自愈引擎"""
    
    def __init__(self, kb_manager, analyzer, use_llm: bool = False):
        self.kb = kb_manager
        self.analyzer = analyzer
        self.use_llm = use_llm and os.getenv("OPENAI_API_KEY")
    
    def analyze_and_suggest(self) -> List[HealSuggestion]:
        """
        分析对话记录，生成修复建议
        """
        suggestions = []
        
        # 1. 分析未解决问题 → 建议新增知识
        gaps = self.analyzer.analyze_unresolved()
        for gap in gaps:
            # 检查是否已有类似知识
            existing = self.kb.search(gap["question"], top_k=1)
            
            if not existing or existing[0]["match_score"] < 3:
                suggestions.append(HealSuggestion(
                    type="add",
                    reason=f"未解决问题: {gap['reason']}",
                    priority="high",
                    details={
                        "question": gap["question"],
                        "conversation_id": gap["conversation_id"],
                        "suggested_category": self._guess_category(gap["question"])
                    },
                    auto_applicable=False  # 需要人工审核
                ))
        
        # 2. 分析低满意度 → 建议优化现有知识
        issues = self.analyzer.analyze_low_satisfaction()
        for issue in issues:
            questions = issue.get("questions", [])
            for q in questions:
                existing = self.kb.search(q, top_k=1)
                if existing:
                    suggestions.append(HealSuggestion(
                        type="update",
                        reason=f"低满意度({issue['satisfaction']}/5): {issue['reason']}",
                        priority="medium",
                        details={
                            "entry_id": existing[0]["id"],
                            "current_question": existing[0]["question"],
                            "customer_question": q,
                            "conversation_id": issue["conversation_id"]
                        },
                        auto_applicable=False
                    ))
        
        # 3. 分析低使用率条目 → 建议优化或删除
        low_hit = self.kb.get_low_hit_entries(threshold=1)
        for entry in low_hit:
            suggestions.append(HealSuggestion(
                type="update",
                reason="知识条目使用率极低，可能需要优化关键词或内容",
                priority="low",
                details={
                    "entry_id": entry["id"],
                    "question": entry["question"],
                    "hit_count": entry.get("hit_count", 0),
                    "suggested_action": "优化关键词或考虑删除"
                },
                auto_applicable=False
            ))
        
        return suggestions
    
    def _guess_category(self, question: str) -> str:
        """
        根据问题猜测分类
        """
        question = question.lower()
        
        keywords_map = {
            "种植技术": ["种", "播", "苗", "栽", "培", "长", "育"],
            "病虫害防治": ["病", "虫", "害", "药", "打药", "发黄", "枯萎", "烂"],
            "土壤肥料": ["土", "肥", "施", "氮", "磷", "钾", "有机", "营养"],
            "采收储存": ["收", "采", "摘", "存", "储", "保鲜", "保存"],
            "品种选择": ["品种", "种什么", "推荐", "适合", "选"],
            "灌溉浇水": ["水", "浇", "灌", "湿", "旱", "涝"],
            "气候环境": ["温度", "光照", "季节", "天气", "冷", "热"]
        }
        
        scores = {}
        for cat, keywords in keywords_map.items():
            score = sum(1 for kw in keywords if kw in question)
            if score > 0:
                scores[cat] = score
        
        if scores:
            return max(scores, key=scores.get)
        return "其他"
    
    def generate_knowledge_entry(self, question: str, conversation_context: List[str] = None) -> Dict:
        """
        基于问题生成知识条目草稿
        """
        # 简单模板生成（实际可用LLM生成更好内容）
        category = self._guess_category(question)
        
        # 提取关键词
        keywords = [w for w in question.replace("？", "").replace("?", "").split() if len(w) >= 2]
        
        # 生成答案模板
        answer_template = f"""关于{question.replace("？", "").replace("?", "")}：

1. 基本情况：[待补充]
2. 关键要点：[待补充]
3. 注意事项：[待补充]
4. 常见问题：[待补充]

（此条目由系统自动生成，需要人工完善）"""
        
        return {
            "category": category,
            "question": question,
            "keywords": keywords[:5],  # 最多5个关键词
            "answer": answer_template,
            "source": "auto_generated",
            "needs_review": True
        }
    
    def auto_heal(self, dry_run: bool = True) -> Dict:
        """
        执行自动修复
        """
        suggestions = self.analyze_and_suggest()
        
        results = {
            "dry_run": dry_run,
            "total_suggestions": len(suggestions),
            "applied": [],
            "pending_review": [],
            "skipped": []
        }
        
        for sug in suggestions:
            if sug.auto_applicable and not dry_run:
                # 执行自动修复
                if sug.type == "add":
                    entry = self.kb.add_entry(
                        category=sug.details["suggested_category"],
                        question=sug.details["question"],
                        answer="[待完善]",
                        keywords=[]
                    )
                    results["applied"].append({
                        "type": "add",
                        "entry_id": entry["id"],
                        "question": entry["question"]
                    })
                
            else:
                # 需要人工审核
                results["pending_review"].append({
                    "type": sug.type,
                    "priority": sug.priority,
                    "reason": sug.reason,
                    "details": sug.details
                })
        
        return results
    
    def print_suggestions(self, suggestions: List[HealSuggestion]):
        """
        打印修复建议
        """
        if not suggestions:
            print("✅ 未发现明显知识缺口")
            return
        
        print(f"\n📊 发现 {len(suggestions)} 条修复建议\n")
        
        # 按优先级分组
        priority_order = {"high": 0, "medium": 1, "low": 2}
        sorted_sug = sorted(suggestions, key=lambda x: priority_order.get(x.priority, 3))
        
        for i, sug in enumerate(sorted_sug, 1):
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(sug.priority, "⚪")
            type_icon = {"add": "➕", "update": "📝", "merge": "🔗"}.get(sug.type, "📋")
            
            print(f"{i}. {priority_icon} {type_icon} [{sug.priority.upper()}] {sug.type}")
            print(f"   原因: {sug.reason}")
            
            if sug.type == "add":
                print(f"   建议新增: 「{sug.details['question']}」")
                print(f"   分类: {sug.details['suggested_category']}")
            elif sug.type == "update":
                print(f"   条目ID: {sug.details.get('entry_id', 'N/A')}")
                print(f"   当前问题: 「{sug.details.get('current_question', 'N/A')}」")
            
            print()
