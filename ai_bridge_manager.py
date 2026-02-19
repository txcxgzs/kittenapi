#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kitten Cloud API - AI 桥接管理工具
功能：管理 AI 桥接服务、修改配置、查看状态、修改提示词

使用方法：
  python3 ai_bridge_manager.py              # 交互菜单
  python3 ai_bridge_manager.py status       # 查看状态
  python3 ai_bridge_manager.py restart      # 重启服务
  python3 ai_bridge_manager.py logs         # 查看日志
"""

import os
import sys
import json
import subprocess
import time
import shutil
from datetime import datetime
from pathlib import Path


def setup_pm2_path():
    """
    设置 PM2 路径
    尝试多种方式找到 PM2 的位置
    """
    possible_paths = [
        '/usr/local/nodejs/bin',
        '/usr/local/bin',
        '/usr/bin',
        os.path.expanduser('~/.npm-global/bin'),
        os.path.expanduser('~/node_modules/.bin'),
        '/root/.npm-global/bin',
    ]
    
    if os.path.exists('/www/server/nodejs'):
        for d in os.listdir('/www/server/nodejs'):
            bin_path = f'/www/server/nodejs/{d}/bin'
            if os.path.exists(bin_path):
                possible_paths.insert(0, bin_path)
    
    for path in possible_paths:
        if os.path.exists(path):
            current_path = os.environ.get('PATH', '')
            if path not in current_path:
                os.environ['PATH'] = path + ':' + current_path
    
    pm2_path = shutil.which('pm2')
    if pm2_path:
        pm2_dir = os.path.dirname(pm2_path)
        current_path = os.environ.get('PATH', '')
        if pm2_dir not in current_path:
            os.environ['PATH'] = pm2_dir + ':' + current_path
    
    return shutil.which('pm2') is not None


PM2_AVAILABLE = setup_pm2_path()

# ==================== 配置路径 ====================
SCRIPT_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = SCRIPT_DIR / "ai-bridge" / "config.py"
PM2_CONFIG_FILE = SCRIPT_DIR / "ai-bridge" / "ecosystem.config.js"
LOGS_DIR = SCRIPT_DIR / "ai-bridge" / "logs"
PROMPT_FILE = SCRIPT_DIR / "ai-bridge" / "system_prompt.txt"

# ==================== 颜色定义 ====================
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
PURPLE = '\033[0;35m'
CYAN = '\033[0;36m'
NC = '\033[0m'

# ==================== 默认提示词 ====================
DEFAULT_PROMPT = """# AI助手提示词

## 重要：输出限制
- **输出长度必须小于200个字符**
- 节省token，回答简洁明了
- 不重复问题，直接给出答案

## 一、基本信息
- 你的身份：AI助手
- 目标用户：编程猫作品玩家

## 二、回复原则

### 1. 回答范围
✅ 可以回答：
- 游戏基础玩法指南
- 常见问题解答
- 友好互动

❌ 拒绝回答：
- 游戏外话题
- 破解/外挂相关
- 其他游戏对比

### 2. 回复风格
- 亲切友好，使用表情
- 简洁明了
- 对新手耐心指导

---

请作为AI助手，为玩家提供友好、准确的帮助！"""

# ==================== 工具函数 ====================

def print_banner():
    """打印横幅"""
    print(f"""
{PURPLE}╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           AI 桥接管理工具 v1.2.0                             ║
║                                                              ║
║     管理 AI 桥接服务、修改配置、查看状态、修改提示词         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝{NC}
""")

def log(level: str, message: str):
    """打印日志"""
    level_colors = {
        "INFO": GREEN,
        "WARN": YELLOW,
        "ERROR": RED,
        "SUCCESS": GREEN,
        "STEP": CYAN
    }
    color = level_colors.get(level, "")
    print(f"{color}[{level}]{NC} {message}")

def run_command(cmd: str, capture: bool = True) -> tuple:
    """
    执行命令
    
    Args:
        cmd: 命令字符串
        capture: 是否捕获输出
        
    Returns:
        (返回码, 输出)
    """
    try:
        if capture:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                env=os.environ
            )
            return result.returncode, result.stdout + result.stderr
        else:
            subprocess.run(cmd, shell=True, timeout=60, env=os.environ)
            return 0, ""
    except subprocess.TimeoutExpired:
        return -1, "命令执行超时"
    except Exception as e:
        return -1, str(e)

def load_config() -> dict:
    """
    加载配置文件
    
    Returns:
        配置字典
    """
    if not CONFIG_FILE.exists():
        return {}
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        local_vars = {}
        exec(content, {}, local_vars)
        
        return local_vars.get('CONFIG', {})
    except Exception as e:
        log("ERROR", f"加载配置失败: {e}")
        return {}

def save_config(config: dict):
    """
    保存配置文件
    
    Args:
        config: 配置字典
    """
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 桥接程序配置文件
更新时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

CONFIG = {{
    "api_base_url": "{config.get('api_base_url', '')}",
    "ai_api_url": "{config.get('ai_api_url', '')}",
    "ai_api_key": "{config.get('ai_api_key', '')}",
    "ai_model": "{config.get('ai_model', '')}",
    "question_prefix": "{config.get('question_prefix', 'QWQ~~~')}",
    "answer_prefix": "{config.get('answer_prefix', 'OKOKOK~~~')}",
    "variable_name": "{config.get('variable_name', 'API')}",
    "system_prompt_file": "{config.get('system_prompt_file', str(PROMPT_FILE))}",
    "request_timeout": {config.get('request_timeout', 60)},
    "max_retries": {config.get('max_retries', 5)},
    "log_dir": "{config.get('log_dir', str(LOGS_DIR))}"
}}
'''
    
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    log("SUCCESS", "配置已保存")

def load_prompt() -> str:
    """
    加载提示词
    
    Returns:
        提示词内容
    """
    if PROMPT_FILE.exists():
        try:
            with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            pass
    return DEFAULT_PROMPT

def save_prompt(prompt: str):
    """
    保存提示词
    
    Args:
        prompt: 提示词内容
    """
    PROMPT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(PROMPT_FILE, 'w', encoding='utf-8') as f:
        f.write(prompt)
    
    # 更新配置文件中的提示词文件路径
    config = load_config()
    config['system_prompt_file'] = str(PROMPT_FILE)
    save_config(config)
    
    log("SUCCESS", "提示词已保存")

def get_pm2_status() -> dict:
    """
    获取 PM2 服务状态
    
    Returns:
        状态字典
    """
    if not PM2_AVAILABLE:
        pm2_path = shutil.which('pm2')
        if not pm2_path:
            return {"error": "PM2 未找到，请确保已安装 PM2 并在 PATH 中。尝试运行: npm install -g pm2"}
    
    returncode, output = run_command("pm2 jlist")
    
    if returncode != 0:
        error_msg = output[:200] if output else '未知错误'
        if "command not found" in error_msg or "not found" in error_msg.lower():
            return {"error": "PM2 命令未找到，请检查 PATH 环境变量"}
        return {"error": f"PM2 命令执行失败: {error_msg}"}
    
    try:
        processes = json.loads(output)
        for proc in processes:
            if proc.get('name') == 'kitten-ai-bridge':
                return {
                    "name": proc.get('name'),
                    "status": proc.get('pm2_env', {}).get('status'),
                    "pid": proc.get('pid'),
                    "uptime": proc.get('pm2_env', {}).get('pm_uptime'),
                    "restarts": proc.get('pm2_env', {}).get('restart_time'),
                    "cpu": proc.get('monit', {}).get('cpu'),
                    "memory": proc.get('monit', {}).get('memory'),
                    "online": proc.get('pm2_env', {}).get('status') == 'online'
                }
        return {"status": "not_found", "online": False}
    except json.JSONDecodeError:
        return {"error": "PM2 输出解析失败"}
    except Exception as e:
        return {"error": str(e)}

def get_work_id() -> str:
    """从 PM2 配置获取作品ID"""
    if PM2_CONFIG_FILE.exists():
        with open(PM2_CONFIG_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            if '-w ' in content:
                start = content.find('-w ') + 3
                end = content.find(' ', start)
                if end == -1:
                    end = content.find("'", start)
                if end == -1:
                    end = content.find('"', start)
                if end > start:
                    return content[start:end].strip()
    return "未知"

def update_pm2_config(work_id: str):
    """
    更新 PM2 配置
    
    Args:
        work_id: 作品ID
    """
    PM2_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    content = f'''module.exports = {{
  apps: [{{
    name: 'kitten-ai-bridge',
    script: '{SCRIPT_DIR}/kitten_ai_bridge.py',
    interpreter: 'python3',
    args: '-w {work_id} -c {CONFIG_FILE}',
    cwd: '{SCRIPT_DIR}',
    autorestart: true,
    restart_delay: 3000,
    max_restarts: 1000,
    watch: false,
    cron_restart: '*/5 * * * *',
    env: {{
      NODE_ENV: 'production'
    }},
    error_file: '{LOGS_DIR}/error.log',
    out_file: '{LOGS_DIR}/out.log'
  }}]
}}
'''
    
    with open(PM2_CONFIG_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

# ==================== 功能函数 ====================

def show_status():
    """显示服务状态"""
    print(f"\n{CYAN}════════════════════════════════════════════════════════════════{NC}")
    print(f"{CYAN}AI 桥接服务状态{NC}")
    print(f"{CYAN}════════════════════════════════════════════════════════════════{NC}\n")
    
    # PM2 状态
    pm2_status = get_pm2_status()
    
    if pm2_status.get('error'):
        log("ERROR", pm2_status['error'])
        log("INFO", "请确保 PM2 已安装并在 PATH 中")
        pm2_path = shutil.which('pm2')
        if pm2_path:
            log("INFO", f"PM2 路径: {pm2_path}")
        else:
            log("INFO", f"当前 PATH: {os.environ.get('PATH', '未设置')}")
            print(f"\n尝试执行: export PATH=/usr/local/nodejs/bin:$PATH")
        return
    
    if pm2_status.get('status') == 'not_found':
        log("WARN", "AI 桥接服务未运行")
        return
    
    status_color = GREEN if pm2_status.get('online') else RED
    print(f"  服务状态: {status_color}{pm2_status.get('status', '未知')}{NC}")
    print(f"  进程 PID: {YELLOW}{pm2_status.get('pid', '无')}{NC}")
    
    # 计算运行时间
    uptime = pm2_status.get('uptime')
    if uptime:
        uptime_seconds = (time.time() * 1000 - uptime) / 1000
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        print(f"  运行时间: {YELLOW}{hours}小时{minutes}分钟{NC}")
    
    print(f"  重启次数: {YELLOW}{pm2_status.get('restarts', 0)}{NC}")
    print(f"  CPU 使用: {YELLOW}{pm2_status.get('cpu', 0)}%{NC}")
    
    memory = pm2_status.get('memory', 0)
    if memory:
        print(f"  内存使用: {YELLOW}{memory / 1024 / 1024:.1f} MB{NC}")
    
    # 配置信息
    config = load_config()
    work_id = get_work_id()
    
    print(f"\n{CYAN}════════════════════════════════════════════════════════════════{NC}")
    print(f"{CYAN}当前配置{NC}")
    print(f"{CYAN}════════════════════════════════════════════════════════════════{NC}\n")
    
    print(f"  作品ID:     {YELLOW}{work_id}{NC}")
    print(f"  API地址:    {YELLOW}{config.get('api_base_url', '未配置')}{NC}")
    print(f"  AI API:     {YELLOW}{config.get('ai_api_url', '未配置')}{NC}")
    print(f"  AI模型:     {YELLOW}{config.get('ai_model', '未配置')}{NC}")
    print(f"  云变量名:   {YELLOW}{config.get('variable_name', '未配置')}{NC}")
    print(f"  问题前缀:   {YELLOW}{config.get('question_prefix', '未配置')}{NC}")
    print(f"  答案前缀:   {YELLOW}{config.get('answer_prefix', '未配置')}{NC}")
    print(f"  提示词文件: {YELLOW}{config.get('system_prompt_file', PROMPT_FILE)}{NC}")
    print()

def show_logs(lines: int = 50):
    """
    显示日志
    
    Args:
        lines: 显示行数
    """
    print(f"\n{CYAN}════════════════════════════════════════════════════════════════{NC}")
    print(f"{CYAN}AI 桥接日志 (最近 {lines} 行){NC}")
    print(f"{CYAN}════════════════════════════════════════════════════════════════{NC}\n")
    
    # 使用 PM2 查看日志
    run_command(f"pm2 logs kitten-ai-bridge --lines {lines} --nostream", capture=False)

def restart_service():
    """重启服务"""
    log("STEP", "正在重启 AI 桥接服务...")
    
    returncode, output = run_command("pm2 restart kitten-ai-bridge")
    
    if returncode == 0:
        log("SUCCESS", "AI 桥接服务已重启")
        time.sleep(2)
        show_status()
    else:
        log("ERROR", f"重启失败: {output}")

def start_service():
    """启动服务"""
    log("STEP", "正在启动 AI 桥接服务...")
    
    # 先检查是否已运行
    pm2_status = get_pm2_status()
    if pm2_status.get('online'):
        log("WARN", "服务已在运行中")
        return
    
    # 使用 PM2 配置启动
    returncode, output = run_command(f"pm2 start {PM2_CONFIG_FILE}")
    
    if returncode == 0:
        log("SUCCESS", "AI 桥接服务已启动")
        run_command("pm2 save")
        time.sleep(2)
        show_status()
    else:
        log("ERROR", f"启动失败: {output}")

def stop_service():
    """停止服务"""
    log("STEP", "正在停止 AI 桥接服务...")
    
    returncode, output = run_command("pm2 stop kitten-ai-bridge")
    
    if returncode == 0:
        log("SUCCESS", "AI 桥接服务已停止")
    else:
        log("ERROR", f"停止失败: {output}")

def edit_work_id():
    """修改作品ID"""
    config = load_config()
    current_id = get_work_id()
    
    print(f"\n{CYAN}当前作品ID: {YELLOW}{current_id}{NC}\n")
    
    new_id = input("请输入新的作品ID: ").strip()
    
    if not new_id:
        log("WARN", "未输入作品ID，取消修改")
        return
    
    if not new_id.isdigit():
        log("ERROR", "作品ID必须是数字")
        return
    
    # 更新 PM2 配置
    update_pm2_config(new_id)
    
    log("SUCCESS", f"作品ID已更新为: {new_id}")
    
    # 询问是否重启
    if input("\n是否立即重启服务? (y/n): ").strip().lower() == 'y':
        restart_service()

def edit_ai_config():
    """修改 AI 配置"""
    config = load_config()
    
    print(f"\n{CYAN}════════════════════════════════════════════════════════════════{NC}")
    print(f"{CYAN}修改 AI 配置{NC}")
    print(f"{CYAN}════════════════════════════════════════════════════════════════{NC}\n")
    
    # AI API 地址
    print(f"当前 AI API 地址: {YELLOW}{config.get('ai_api_url', '未配置')}{NC}")
    new_ai_url = input("请输入新的 AI API 地址 (回车保持不变): ").strip()
    if new_ai_url:
        config['ai_api_url'] = new_ai_url
    
    # AI API Key
    print(f"\n当前 AI API Key: {YELLOW}{'*' * 10}{config.get('ai_api_key', '')[-4:] if config.get('ai_api_key') else '未配置'}{NC}")
    new_ai_key = input("请输入新的 AI API Key (回车保持不变): ").strip()
    if new_ai_key:
        config['ai_api_key'] = new_ai_key
    
    # AI 模型
    print(f"\n当前 AI 模型: {YELLOW}{config.get('ai_model', '未配置')}{NC}")
    new_model = input("请输入新的 AI 模型名称 (回车保持不变): ").strip()
    if new_model:
        config['ai_model'] = new_model
    
    # 保存配置
    save_config(config)
    
    # 询问是否重启
    if input("\n是否立即重启服务? (y/n): ").strip().lower() == 'y':
        restart_service()

def edit_variable_config():
    """修改云变量配置"""
    config = load_config()
    
    print(f"\n{CYAN}════════════════════════════════════════════════════════════════{NC}")
    print(f"{CYAN}修改云变量配置{NC}")
    print(f"{CYAN}════════════════════════════════════════════════════════════════{NC}\n")
    
    # 云变量名
    print(f"当前云变量名: {YELLOW}{config.get('variable_name', '未配置')}{NC}")
    new_var_name = input("请输入新的云变量名 (回车保持不变): ").strip()
    if new_var_name:
        config['variable_name'] = new_var_name
    
    # 问题前缀
    print(f"\n当前问题前缀: {YELLOW}{config.get('question_prefix', '未配置')}{NC}")
    new_q_prefix = input("请输入新的问题前缀 (回车保持不变): ").strip()
    if new_q_prefix:
        config['question_prefix'] = new_q_prefix
    
    # 答案前缀
    print(f"\n当前答案前缀: {YELLOW}{config.get('answer_prefix', '未配置')}{NC}")
    new_a_prefix = input("请输入新的答案前缀 (回车保持不变): ").strip()
    if new_a_prefix:
        config['answer_prefix'] = new_a_prefix
    
    # 保存配置
    save_config(config)
    
    # 询问是否重启
    if input("\n是否立即重启服务? (y/n): ").strip().lower() == 'y':
        restart_service()

def edit_prompt():
    """修改 AI 提示词"""
    current_prompt = load_prompt()
    
    print(f"\n{CYAN}════════════════════════════════════════════════════════════════{NC}")
    print(f"{CYAN}修改 AI 提示词{NC}")
    print(f"{CYAN}════════════════════════════════════════════════════════════════{NC}\n")
    
    print(f"当前提示词 ({len(current_prompt)} 字符):")
    print(f"{YELLOW}{'-' * 50}{NC}")
    # 显示前 500 字符
    if len(current_prompt) > 500:
        print(current_prompt[:500] + "\n... (已截断)")
    else:
        print(current_prompt)
    print(f"{YELLOW}{'-' * 50}{NC}\n")
    
    print("选择操作:")
    print(f"  {CYAN}1.{NC} 查看完整提示词")
    print(f"  {CYAN}2.{NC} 编辑提示词 (使用 nano 编辑器)")
    print(f"  {CYAN}3.{NC} 重置为默认提示词")
    print(f"  {CYAN}0.{NC} 返回")
    
    choice = input("\n请选择: ").strip()
    
    if choice == '1':
        # 查看完整提示词
        print(f"\n{CYAN}完整提示词:{NC}")
        print(f"{YELLOW}{'-' * 50}{NC}")
        print(current_prompt)
        print(f"{YELLOW}{'-' * 50}{NC}")
        input("\n按回车继续...")
    
    elif choice == '2':
        # 使用 nano 编辑
        print(f"\n{CYAN}正在打开编辑器...{NC}")
        print(f"提示: 编辑完成后按 Ctrl+X 保存退出\n")
        time.sleep(1)
        
        # 保存当前提示词到临时文件
        temp_file = SCRIPT_DIR / "ai-bridge" / "temp_prompt.txt"
        temp_file.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(current_prompt)
        
        # 使用 nano 编辑
        os.system(f"nano {temp_file}")
        
        # 读取编辑后的内容
        if temp_file.exists():
            with open(temp_file, 'r', encoding='utf-8') as f:
                new_prompt = f.read()
            
            if new_prompt.strip() and new_prompt != current_prompt:
                save_prompt(new_prompt)
                log("SUCCESS", "提示词已更新")
                
                if input("\n是否立即重启服务? (y/n): ").strip().lower() == 'y':
                    restart_service()
            else:
                log("INFO", "提示词未更改")
            
            # 删除临时文件
            temp_file.unlink()
    
    elif choice == '3':
        # 重置为默认
        if input("确定要重置为默认提示词吗? (y/n): ").strip().lower() == 'y':
            save_prompt(DEFAULT_PROMPT)
            log("SUCCESS", "已重置为默认提示词")
            
            if input("\n是否立即重启服务? (y/n): ").strip().lower() == 'y':
                restart_service()

def show_stats():
    """显示统计数据"""
    print(f"\n{CYAN}════════════════════════════════════════════════════════════════{NC}")
    print(f"{CYAN}AI 桥接统计数据{NC}")
    print(f"{CYAN}════════════════════════════════════════════════════════════════{NC}\n")
    
    # 查找最新的统计文件
    stats_files = list(LOGS_DIR.glob("stats_*.json")) if LOGS_DIR.exists() else []
    
    if not stats_files:
        log("WARN", "暂无统计数据")
        return
    
    latest_stats = max(stats_files, key=lambda f: f.stat().st_mtime)
    
    try:
        with open(latest_stats, 'r', encoding='utf-8') as f:
            stats = json.load(f)
        
        print(f"  统计日期:   {YELLOW}{stats.get('date', '未知')}{NC}")
        print(f"  运行时长:   {YELLOW}{stats.get('uptime_seconds', 0) // 3600}小时{(stats.get('uptime_seconds', 0) % 3600) // 60}分钟{NC}")
        print(f"  轮询次数:   {YELLOW}{stats.get('total_polls', 0)}{NC}")
        print(f"  收到问题:   {YELLOW}{stats.get('total_questions', 0)}{NC}")
        print(f"  成功答复:   {GREEN}{stats.get('successful_answers', 0)}{NC}")
        print(f"  失败答复:   {RED}{stats.get('failed_answers', 0)}{NC}")
        
        total = stats.get('total_questions', 0)
        success = stats.get('successful_answers', 0)
        rate = (success / total * 100) if total > 0 else 0
        print(f"  成功率:     {YELLOW}{rate:.1f}%{NC}")
        print(f"  错误次数:   {RED}{stats.get('total_errors', 0)}{NC}")
        print()
    except Exception as e:
        log("ERROR", f"读取统计数据失败: {e}")

def show_help():
    """显示帮助"""
    print(f"""
{CYAN}使用方法:{NC}
  python3 ai_bridge_manager.py              # 交互菜单
  python3 ai_bridge_manager.py status       # 查看状态
  python3 ai_bridge_manager.py restart      # 重启服务
  python3 ai_bridge_manager.py start        # 启动服务
  python3 ai_bridge_manager.py stop         # 停止服务
  python3 ai_bridge_manager.py logs         # 查看日志
  python3 ai_bridge_manager.py stats        # 查看统计
  python3 ai_bridge_manager.py prompt       # 修改提示词

{CYAN}PM2 自动重启说明:{NC}
  - 每 5 分钟自动重启一次 (cron_restart)
  - 崩溃后自动重启 (autorestart)
  - 最大重启次数: 1000 次

{CYAN}提示词文件位置:{NC}
  {PROMPT_FILE}
""")

# ==================== 主菜单 ====================

def show_menu():
    """显示主菜单"""
    while True:
        print(f"\n{PURPLE}════════════════════════════════════════════════════════════════{NC}")
        print(f"{PURPLE}AI 桥接管理菜单{NC}")
        print(f"{PURPLE}════════════════════════════════════════════════════════════════{NC}\n")
        
        print(f"  {CYAN}1.{NC} 查看服务状态")
        print(f"  {CYAN}2.{NC} 重启服务")
        print(f"  {CYAN}3.{NC} 启动服务")
        print(f"  {CYAN}4.{NC} 停止服务")
        print(f"  {CYAN}5.{NC} 查看日志")
        print(f"  {CYAN}6.{NC} 查看统计")
        print(f"  {CYAN}7.{NC} 修改作品ID")
        print(f"  {CYAN}8.{NC} 修改 AI 配置")
        print(f"  {CYAN}9.{NC} 修改云变量配置")
        print(f"  {CYAN}10.{NC} 修改 AI 提示词")
        print(f"  {CYAN}0.{NC} 退出")
        print()
        
        choice = input("请选择操作: ").strip()
        
        if choice == '1':
            show_status()
        elif choice == '2':
            restart_service()
        elif choice == '3':
            start_service()
        elif choice == '4':
            stop_service()
        elif choice == '5':
            show_logs()
        elif choice == '6':
            show_stats()
        elif choice == '7':
            edit_work_id()
        elif choice == '8':
            edit_ai_config()
        elif choice == '9':
            edit_variable_config()
        elif choice == '10':
            edit_prompt()
        elif choice == '0':
            print(f"\n{GREEN}再见！{NC}\n")
            break
        else:
            log("WARN", "无效选择，请重新输入")

# ==================== 主函数 ====================

def main():
    """主函数"""
    print_banner()
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'status':
            show_status()
        elif command == 'restart':
            restart_service()
        elif command == 'start':
            start_service()
        elif command == 'stop':
            stop_service()
        elif command == 'logs':
            show_logs()
        elif command == 'stats':
            show_stats()
        elif command == 'prompt':
            edit_prompt()
        elif command in ['help', '-h', '--help']:
            show_help()
        else:
            log("ERROR", f"未知命令: {command}")
            show_help()
    else:
        show_menu()

if __name__ == "__main__":
    main()
