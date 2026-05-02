#!/usr/bin/env python3
"""
农产品客服知识库自愈 Agent - 主程序
MVP 版本
"""

import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.kb_manager import KnowledgeBaseManager
from src.dialog_analyzer import ConversationStore, DialogAnalyzer
from src.self_heal_engine import SelfHealEngine
from src.chat_simulator import ConversationSimulator


def print_header():
    """打印标题"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║     🌾 农产品客服知识库自愈 Agent (MVP) 🌾                    ║
║                                                              ║
║   功能: 知识库管理 | 对话模拟 | 智能分析 | 自动修复建议      ║
╚══════════════════════════════════════════════════════════════╝
    """)


def show_menu():
    """显示菜单"""
    print("\n📋 功能菜单:")
    print("-" * 50)
    print("  1. 📚 查看知识库统计")
    print("  2. 🔍 搜索知识库")
    print("  3. ➕ 添加新知识")
    print("  4. 🎭 模拟客服对话")
    print("  5. 📊 生成分析报告")
    print("  6. 🔧 运行自愈诊断")
    print("  7. 💾 查看对话记录")
    print("  0. 🚪 退出")
    print("-" * 50)


def cmd_kb_stats(kb: KnowledgeBaseManager):
    """知识库统计"""
    stats = kb.get_stats()
    print("\n📚 知识库统计:")
    print(f"  总条目数: {stats['total_entries']}")
    print(f"  分类数: {stats['categories']}")
    print(f"  总查询次数: {stats['total_hits']}")
    print("\n  分类分布:")
    for cat, count in stats['category_distribution'].items():
        print(f"    • {cat}: {count} 条")


def cmd_search(kb: KnowledgeBaseManager):
    """搜索知识库"""
    query = input("\n🔍 请输入搜索关键词: ").strip()
    if not query:
        print("❌ 关键词不能为空")
        return
    
    results = kb.search(query, top_k=3)
    
    if not results:
        print("❌ 未找到相关知识")
        return
    
    print(f"\n📋 找到 {len(results)} 条相关结果:")
    for i, r in enumerate(results, 1):
        print(f"\n{i}. [{r['category']}] {r['question']}")
        print(f"   匹配度: {r['match_score']}")
        print(f"   答案: {r['answer'][:100]}...")


def cmd_add_knowledge(kb: KnowledgeBaseManager):
    """添加新知识"""
    print("\n➕ 添加新知识条目:")
    
    categories = kb.data.get("categories", [])
    print(f"\n现有分类: {', '.join(categories)}")
    
    category = input("分类 (可输入新分类): ").strip()
    question = input("问题: ").strip()
    answer = input("答案: ").strip()
    keywords = input("关键词 (用空格分隔): ").strip().split()
    
    if not all([category, question, answer]):
        print("❌ 分类、问题、答案不能为空")
        return
    
    entry = kb.add_entry(category, question, answer, keywords)
    print(f"\n✅ 已添加新知识条目: {entry['id']}")
    print(f"   问题: {entry['question']}")


def cmd_simulate(kb: KnowledgeBaseManager, store: ConversationSimulator):
    """模拟对话"""
    print("\n🎭 客服对话模拟:")
    print("  1. 模拟单次对话")
    print("  2. 批量模拟 (10次)")
    
    choice = input("\n请选择: ").strip()
    
    simulator = ConversationSimulator(kb, store)
        
    def cmd_simulate_local(kb_manager, conv_store):
        """模拟对话 - 使用正确的路径"""
        print("\n🎭 客服对话模拟:")
        print("  1. 模拟单次对话")
        print("  2. 批量模拟 (10次)")
        
        choice = input("\n请选择: ").strip()
        
        if choice == "1":
            print("\n正在模拟单次对话...")
            conv = simulator.simulate_one()
            simulator.print_conversation(conv)
            
        elif choice == "2":
            print("\n正在批量模拟10次对话...")
            convs = simulator.simulate_batch(count=10)
            for conv in convs:
                simulator.print_conversation(conv)
            print(f"\n✅ 已生成 {len(convs)} 条对话记录")
        else:
            print("❌ 无效选择")
    
    if choice == "1":
        print("\n正在模拟单次对话...")
        conv = simulator.simulate_one()
        simulator.print_conversation(conv)
        
    elif choice == "2":
        print("\n正在批量模拟10次对话...")
        convs = simulator.simulate_batch(count=10)
        for conv in convs:
            simulator.print_conversation(conv)
        print(f"\n✅ 已生成 {len(convs)} 条对话记录")
    else:
        print("❌ 无效选择")


def cmd_analyze(analyzer: DialogAnalyzer, store: ConversationStore):
    """生成分析报告"""
    total = len(store.get_all())
    
    if total == 0:
        print("\n⚠️ 暂无对话记录，请先模拟一些对话")
        return
    
    print(f"\n📊 正在分析 {total} 条对话记录...")
    report = analyzer.generate_report()
    
    print("\n" + "="*60)
    print("📈 对话分析报告")
    print("="*60)
    
    print(f"\n📌 总体情况:")
    print(f"  总对话数: {report['total_conversations']}")
    print(f"  已解决: {report['resolved']}")
    print(f"  未解决: {report['unresolved']}")
    print(f"  解决率: {report['resolution_rate']}")
    print(f"  平均满意度: {report['avg_satisfaction']}")
    
    if report['knowledge_gaps']:
        print(f"\n🔴 知识缺口 ({len(report['knowledge_gaps'])} 个):")
        for gap in report['knowledge_gaps'][:5]:  # 只显示前5个
            print(f"  • {gap['question']}")
    
    if report['quality_issues']:
        print(f"\n🟡 质量问题 ({len(report['quality_issues'])} 个):")
        for issue in report['quality_issues'][:3]:
            print(f"  • 满意度 {issue['satisfaction']}/5 - {issue['questions'][0] if issue['questions'] else 'N/A'}")
    
    if report['frequent_topics']:
        print(f"\n📌 高频话题:")
        for topic in report['frequent_topics'][:5]:
            print(f"  • {topic['term']}: {topic['count']} 次")


def cmd_heal(kb: KnowledgeBaseManager, analyzer: DialogAnalyzer):
    """运行自愈诊断"""
    print("\n🔧 启动自愈诊断引擎...")
    
    engine = SelfHealEngine(kb, analyzer, use_llm=False)
    
    # 分析并生成建议
    suggestions = engine.analyze_and_suggest()
    engine.print_suggestions(suggestions)
    
    if not suggestions:
        return
    
    # 询问是否生成草稿
    print("\n是否生成知识条目草稿？")
    choice = input("输入编号生成对应草稿 (或按Enter跳过): ").strip()
    
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(suggestions):
            sug = suggestions[idx]
            if sug.type == "add":
                draft = engine.generate_knowledge_entry(sug.details["question"])
                print("\n📝 生成的知识条目草稿:")
                print(f"分类: {draft['category']}")
                print(f"问题: {draft['question']}")
                print(f"关键词: {', '.join(draft['keywords'])}")
                print(f"答案:\n{draft['answer']}")
                
                save = input("\n是否添加到知识库？(y/n): ").strip().lower()
                if save == 'y':
                    entry = kb.add_entry(
                        category=draft['category'],
                        question=draft['question'],
                        answer=draft['answer'],
                        keywords=draft['keywords']
                    )
                    print(f"✅ 已添加: {entry['id']}")


def cmd_view_conversations(store: ConversationStore):
    """查看对话记录"""
    convs = store.get_recent(limit=5)
    
    if not convs:
        print("\n⚠️ 暂无对话记录")
        return
    
    print(f"\n💾 最近 {len(convs)} 条对话记录:")
    
    from src.chat_simulator import ConversationSimulator
    simulator = ConversationSimulator(None, store)
    
    for conv in convs:
        simulator.print_conversation(conv)


def main():
    """主函数"""
    print_header()
    
    # 初始化组件
    base_dir = os.path.dirname(os.path.abspath(__file__))
    kb = KnowledgeBaseManager(os.path.join(base_dir, "data/knowledge_base.json"))
    store = ConversationStore(os.path.join(base_dir, "data/conversations.json"))
    analyzer = DialogAnalyzer(store)
    
    print("✅ 系统初始化完成")
    print(f"   知识库: {len(kb.list_all())} 条")
    print(f"   对话记录: {len(store.get_all())} 条")
    
    while True:
        show_menu()
        choice = input("请选择功能: ").strip()
        
        if choice == "1":
            cmd_kb_stats(kb)
        elif choice == "2":
            cmd_search(kb)
        elif choice == "3":
            cmd_add_knowledge(kb)
        elif choice == "4":
            cmd_simulate_local(kb, store)
        elif choice == "5":
            cmd_analyze(analyzer, store)
        elif choice == "6":
            cmd_heal(kb, analyzer)
        elif choice == "7":
            cmd_view_conversations(store)
        elif choice == "0":
            print("\n👋 再见！")
            break
        else:
            print("\n❌ 无效选择，请重新输入")


if __name__ == "__main__":
    main()
