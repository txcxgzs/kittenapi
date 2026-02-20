# Kitten Cloud API

基于 [Kitten-Cloud-Function](https://github.com/S-LIGHTNING/Kitten-Cloud-Function) 的 HTTP API 服务，提供编程猫云变量/云列表的 RESTful API 接口。

## 功能特性

- HTTP API 接口访问云变量/云列表
- Web 管理后台
- AI 桥接功能（可选）
- 多作品同时连接支持

## 使用方法

将此目录作为 AI 桥接的工作目录，配置文件将自动生成在 `config.py` 中。

## 目录结构

```
ai-bridge/
├── config.py           # 配置文件（自动生成，包含敏感信息）
├── ecosystem.config.js # PM2 配置（自动生成）
├── logs/               # 日志目录
└── prompts/
    └── system_prompt.txt  # 系统提示词（可选）
```
