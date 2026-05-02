# 农产品客服知识库自愈 Agent (MVP)

## 项目结构

```
farm-kb-agent/
├── data/
│   ├── knowledge_base.json    # 知识库（FAQ）
│   └── conversations.json     # 客服对话记录
├── src/
│   ├── kb_manager.py          # 知识库管理
│   ├── dialog_analyzer.py     # 对话分析器
│   ├── self_heal_engine.py    # 自愈引擎
│   └── chat_simulator.py      # 客服对话模拟器（用于生成测试数据）
├── app.py                      # 主程序入口
├── requirements.txt
└── README.md
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行主程序
python app.py
```

## 功能

1. **知识库管理** - 增删改查农产品知识
2. **对话模拟** - 模拟客户咨询，生成对话记录
3. **对话分析** - 识别未解决问题、知识缺口
4. **自愈修复** - 自动生成新知识条目，优化现有内容
