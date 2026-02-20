# Kitten Cloud API - AI 桥接目录

基于 [Kitten-Cloud-Function](https://github.com/S-LIGHTNING/Kitten-Cloud-Function) 的 HTTP API 服务，提供编程猫云变量/云列表的 RESTful API 接口。

## 功能特性

- HTTP API 接口访问云变量/云列表
- Web 管理后台
- AI 桥接功能（可选）
- 多作品同时连接支持

## 使用方法

将此目录作为 AI 桥接的工作目录，配置文件将自动生成。

## 目录结构（多作品隔离）

```
ai-bridge/
├── config_{作品ID}.py           # 各作品的配置文件（自动生成，包含敏感信息）
├── system_prompt_{作品ID}.txt   # 各作品的系统提示词（可选）
├── ecosystem_{作品ID}.config.js # 各作品的 PM2 配置（自动生成）
├── logs/
│   ├── error_{作品ID}.log       # 各作品的 PM2 错误日志
│   ├── out_{作品ID}.log         # 各作品的 PM2 输出日志
│   ├── ai_bridge_{作品ID}_{日期}.log  # 各作品的桥接日志
│   └── stats_{作品ID}_{日期}.json     # 各作品的统计数据
└── prompts/
    └── system_prompt.txt.example  # 系统提示词示例
```

## 多作品支持

每个作品都有独立的配置文件和日志文件，通过作品ID进行隔离：

- 配置文件：`config_123456.py`
- 提示词文件：`system_prompt_123456.txt`
- PM2 实例名：`ai-bridge-123456`
- 日志文件：`ai_bridge_123456_2025-02-20.log`
