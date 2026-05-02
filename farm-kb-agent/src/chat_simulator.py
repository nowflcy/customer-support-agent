"""
客服对话模拟器
用于生成测试数据，模拟客户咨询
"""

import random
from datetime import datetime, timedelta
from typing import List, Optional

from .dialog_analyzer import Conversation, DialogTurn


class CustomerSimulator:
    """客户模拟器"""
    
    # 农产品相关问题模板
    QUESTION_TEMPLATES = [
        # 种植技术类
        "{crop}什么时候播种比较好？",
        "{crop}需要什么样的土壤？",
        "{crop}多久浇一次水？",
        "{crop}怎么施肥？",
        "{crop}从种到收要多久？",
        
        # 病虫害类
        "{crop}叶子发黄怎么办？",
        "{crop}长虫了怎么处理？",
        "{crop}得了什么病，怎么治？",
        "{crop}用什么农药比较安全？",
        
        # 采收储存类
        "{crop}什么时候采收？",
        "{crop}怎么保存时间长？",
        "{crop}采摘后怎么处理？",
        
        # 品种选择类
        "{region}适合种什么{crop}品种？",
        "{crop}哪个品种产量高？",
        "新手适合种{crop}吗？",
        
        # 其他
        "{crop}和{crop2}可以一起种吗？",
        "大棚种{crop}要注意什么？",
    ]
    
    CROPS = ["番茄", "黄瓜", "辣椒", "茄子", "西瓜", "草莓", "葡萄", "苹果", 
             "白菜", "萝卜", "土豆", "玉米", "大豆", "水稻", "小麦"]
    
    REGIONS = ["南方", "北方", "东北", "华北", "华南", "西南地区"]
    
    def __init__(self):
        self.crop = random.choice(self.CROPS)
        self.crop2 = random.choice([c for c in self.CROPS if c != self.crop])
        self.region = random.choice(self.REGIONS)
    
    def generate_question(self, has_answer_in_kb: bool = True) -> str:
        """生成客户问题"""
        if has_answer_in_kb:
            # 生成知识库中可能有的问题
            template = random.choice(self.QUESTION_TEMPLATES[:8])
        else:
            # 生成知识库中可能没有的问题（更具体或组合问题）
            template = random.choice(self.QUESTION_TEMPLATES[8:])
        
        return template.format(
            crop=self.crop,
            crop2=self.crop2,
            region=self.region
        )
    
    def generate_followup(self, agent_response: str) -> Optional[str]:
        """根据客服回复生成追问"""
        followups = [
            "具体怎么操作？",
            "有没有更简单的方法？",
            "需要买什么东西？",
            "大概要花多少钱？",
            "多长时间能见效？",
            "好的，谢谢！",
            None  # 不再追问
        ]
        return random.choice(followups)


class AgentSimulator:
    """客服模拟器"""
    
    def __init__(self, kb_manager):
        self.kb = kb_manager
    
    def respond(self, customer_question: str, has_knowledge: bool = True) -> str:
        """
        模拟客服回复
        """
        if has_knowledge:
            # 尝试从知识库找答案
            answer = self.kb.get_answer(customer_question)
            if answer:
                return answer
        
        # 知识库没有，模拟不确定的回答
        uncertain_responses = [
            "这个问题我帮您查一下...",
            "这个情况比较复杂，我需要确认一下再回复您。",
            "您问的这个比较专业，我记录下来让技术同事给您回电可以吗？",
            "抱歉，这个具体的情况我还需要核实，稍后给您答复。",
        ]
        return random.choice(uncertain_responses)


class ConversationSimulator:
    """对话模拟器"""
    
    def __init__(self, kb_manager, store):
        self.customer = CustomerSimulator()
        self.agent = AgentSimulator(kb_manager)
        self.store = store
        self.kb = kb_manager
        self.conv_counter = len(store.get_all())
    
    def simulate_one(self, force_unresolved: bool = False, force_low_satisfaction: bool = False) -> Conversation:
        """
        模拟一次完整对话
        """
        self.conv_counter += 1
        conv_id = f"conv_{self.conv_counter:04d}"
        customer_id = f"user_{random.randint(1000, 9999)}"
        
        now = datetime.now()
        turns = []
        
        # 客户首次提问
        # 30% 概率问知识库没有的问题
        has_kb_answer = random.random() > 0.3 and not force_unresolved
        question = self.customer.generate_question(has_answer_in_kb=has_kb_answer)
        
        turns.append(DialogTurn(
            role="customer",
            content=question,
            timestamp=now.strftime("%Y-%m-%d %H:%M:%S")
        ))
        
        # 客服回复
        response = self.agent.respond(question, has_knowledge=has_kb_answer)
        now += timedelta(minutes=random.randint(1, 5))
        
        turns.append(DialogTurn(
            role="agent",
            content=response,
            timestamp=now.strftime("%Y-%m-%d %H:%M:%S")
        ))
        
        # 50% 概率有追问
        if random.random() > 0.5:
            followup = self.customer.generate_followup(response)
            if followup:
                now += timedelta(minutes=random.randint(1, 3))
                turns.append(DialogTurn(
                    role="customer",
                    content=followup,
                    timestamp=now.strftime("%Y-%m-%d %H:%M:%S")
                ))
                
                # 客服再次回复
                now += timedelta(minutes=random.randint(1, 5))
                turns.append(DialogTurn(
                    role="agent",
                    content="好的，有其他问题随时联系！",
                    timestamp=now.strftime("%Y-%m-%d %H:%M:%S")
                ))
        
        # 判断是否解决
        resolved = has_kb_answer and not force_unresolved
        if force_unresolved:
            resolved = False
        
        # 满意度（未解决的一般满意度低）
        if resolved and not force_low_satisfaction:
            satisfaction = random.choice([4, 4, 5, 5, 5])  # 大部分满意
        elif force_low_satisfaction:
            satisfaction = random.choice([1, 2, 2, 3])
        else:
            satisfaction = random.choice([2, 2, 3, 3, 3])  # 未解决的一般不满意
        
        # 标签
        tags = []
        if not resolved:
            tags.append("未解决")
        if satisfaction and satisfaction <= 2:
            tags.append("低满意度")
        if not has_kb_answer:
            tags.append("知识缺口")
        
        conv = Conversation(
            id=conv_id,
            customer_id=customer_id,
            turns=turns,
            start_time=turns[0].timestamp,
            end_time=turns[-1].timestamp,
            resolved=resolved,
            satisfaction=satisfaction,
            tags=tags
        )
        
        # 保存对话
        self.store.add(conv)
        
        return conv
    
    def simulate_batch(self, count: int = 10) -> List[Conversation]:
        """
        批量模拟对话
        """
        conversations = []
        
        for i in range(count):
            # 随机制造一些特殊场景
            force_unresolved = (i % 5 == 0)  # 20% 未解决
            force_low_sat = (i % 7 == 0)     # ~14% 低满意度
            
            conv = self.simulate_one(
                force_unresolved=force_unresolved,
                force_low_satisfaction=force_low_sat
            )
            conversations.append(conv)
        
        return conversations
    
    def print_conversation(self, conv: Conversation):
        """打印对话内容"""
        status = "✅ 已解决" if conv.resolved else "❌ 未解决"
        sat = f"满意度: {conv.satisfaction}/5" if conv.satisfaction else "无评分"
        
        print(f"\n{'='*60}")
        print(f"对话 {conv.id} | {status} | {sat}")
        print(f"标签: {', '.join(conv.tags) if conv.tags else '无'}")
        print(f"{'='*60}")
        
        for turn in conv.turns:
            role_icon = "👤" if turn.role == "customer" else "🎧"
            print(f"{role_icon} [{turn.role}] {turn.content}")
        
        print(f"{'='*60}\n")
