#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kitten Cloud API - AI 桥接管理工具
功能：管理 AI 桥接服务、多作品管理、修改配置、查看状态、修改提示词

使用方法：
  python3 ai_bridge_manager.py              # 交互菜单
  python3 ai_bridge_manager.py status       # 查看所有实例状态
  python3 ai_bridge_manager.py add          # 添加作品
  python3 ai_bridge_manager.py logs         # 查看日志
  python3 ai_bridge_manager.py clear-logs   # 清除日志
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

SCRIPT_DIR = Path(__file__).parent.resolve()
CONFIG_DIR = SCRIPT_DIR / "ai-bridge"
LOGS_DIR = CONFIG_DIR / "logs"
PROMPT_FILE = CONFIG_DIR / "system_prompt.txt"

RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
PURPLE = '\033[0;35m'
CYAN = '\033[0;36m'
NC = '\033[0m'

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
可以回答：
- 游戏基础玩法指南
- 常见问题解答
- 友好互动

拒绝回答：
- 游戏外话题
- 破解/外挂相关
- 其他游戏对比

### 2. 回复风格
- 亲切友好，使用表情
- 简洁明了
- 对新手耐心指导

请作为AI助手，为玩家提供友好、准确的帮助！"""


def print_banner():
    print(f"""
{PURPLE}╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           AI 桥接管理工具 v2.0.0                             ║
║                                                              ║
║     多作品管理 | 配置管理 | 日志管理 | 提示词管理            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝{NC}
""")


def log(level: str, message: str):
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


def get_all_ai_bridges() -> list:
    """
    获取所有 AI 桥接实例
    
    Returns:
        实例列表
    """
    if not PM2_AVAILABLE:
        return []
    
    returncode, output = run_command("pm2 jlist")
    
    if returncode != 0:
        return []
    
    try:
        processes = json.loads(output)
        bridges = []
        for proc in processes:
            name = proc.get('name', '')
            if name.startswith('ai-bridge-') or name == 'kitten-ai-bridge':
                work_id = name.replace('ai-bridge-', '').replace('kitten-ai-bridge', 'default')
                bridges.append({
                    'name': name,
                    'work_id': work_id if work_id else 'default',
                    'status': proc.get('pm2_env', {}).get('status'),
                    'pid': proc.get('pid'),
                    'uptime': proc.get('pm2_env', {}).get('pm_uptime'),
                    'restarts': proc.get('pm2_env', {}).get('restart_time'),
                    'cpu': proc.get('monit', {}).get('cpu'),
                    'memory': proc.get('monit', {}).get('memory'),
                    'online': proc.get('pm2_env', {}).get('status') == 'online'
                })
        return bridges
    except:
        return []


def get_config_path(work_id: str) -> Path:
    """获取指定作品的配置文件路径"""
    if work_id == 'default':
        return CONFIG_DIR / "config.py"
    return CONFIG_DIR / f"config_{work_id}.py"


def get_prompt_path(work_id: str) -> Path:
    """获取指定作品的提示词文件路径"""
    if work_id == 'default':
        return CONFIG_DIR / "system_prompt.txt"
    return CONFIG_DIR / f"system_prompt_{work_id}.txt"


def load_config(work_id: str = 'default') -> dict:
    config_file = get_config_path(work_id)
    
    if not config_file.exists():
        return {}
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        local_vars = {}
        exec(content, {}, local_vars)
        
        return local_vars.get('CONFIG', {})
    except Exception as e:
        log("ERROR", f"加载配置失败: {e}")
        return {}


def save_config(config: dict, work_id: str = 'default'):
    config_file = get_config_path(work_id)
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    prompt_file = get_prompt_path(work_id)
    
    content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 桥接程序配置文件
作品ID: {work_id}
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
    "system_prompt_file": "{config.get('system_prompt_file', str(prompt_file))}",
    "request_timeout": {config.get('request_timeout', 60)},
    "max_retries": {config.get('max_retries', 5)},
    "log_dir": "{config.get('log_dir', str(LOGS_DIR))}"
}}
'''
    
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    log("SUCCESS", f"配置已保存 (作品: {work_id})")


def load_prompt(work_id: str = 'default') -> str:
    prompt_file = get_prompt_path(work_id)
    
    if prompt_file.exists():
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            pass
    return DEFAULT_PROMPT


def save_prompt(prompt: str, work_id: str = 'default'):
    prompt_file = get_prompt_path(work_id)
    prompt_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(prompt)
    
    config = load_config(work_id)
    config['system_prompt_file'] = str(prompt_file)
    save_config(config, work_id)
    
    log("SUCCESS", f"提示词已保存 (作品: {work_id})")


def show_all_status():
    """显示所有实例状态"""
    print(f"\n{CYAN}════════════════════════════════════════════════════════════════{NC}")
    print(f"{CYAN}所有 AI 桥接实例{NC}")
    print(f"{CYAN}════════════════════════════════════════════════════════════════{NC}\n")
    
    bridges = get_all_ai_bridges()
    
    if not bridges:
        log("WARN", "暂无运行中的 AI 桥接实例")
        log("INFO", "使用 '添加作品' 功能创建新实例")
        return
    
    print(f"{'实例名称':<25} {'作品ID':<12} {'状态':<10} {'PID':<8} {'CPU':<8} {'内存':<10}")
    print("-" * 80)
    
    for bridge in bridges:
        status_color = GREEN if bridge['online'] else RED
        status = bridge.get('status', '未知')
        pid = bridge.get('pid', '-') or '-'
        cpu = f"{bridge.get('cpu', 0)}%" if bridge.get('cpu') else "-"
        memory = bridge.get('memory', 0)
        mem_str = f"{memory / 1024 / 1024:.1f}MB" if memory else "-"
        
        print(f"{bridge['name']:<25} {bridge['work_id']:<12} {status_color}{status:<10}{NC} {str(pid):<8} {cpu:<8} {mem_str:<10}")
    
    print()


def show_instance_status(work_id: str):
    """显示指定实例详细状态"""
    bridges = get_all_ai_bridges()
    bridge = None
    
    for b in bridges:
        if b['work_id'] == work_id or b['name'] == work_id:
            bridge = b
            break
    
    if not bridge:
        log("ERROR", f"未找到实例: {work_id}")
        return
    
    print(f"\n{CYAN}════════════════════════════════════════════════════════════════{NC}")
    print(f"{CYAN}实例详情: {bridge['name']}{NC}")
    print(f"{CYAN}════════════════════════════════════════════════════════════════{NC}\n")
    
    status_color = GREEN if bridge['online'] else RED
    print(f"  实例名称:   {YELLOW}{bridge['name']}{NC}")
    print(f"  作品ID:     {YELLOW}{bridge['work_id']}{NC}")
    print(f"  服务状态:   {status_color}{bridge.get('status', '未知')}{NC}")
    print(f"  进程 PID:   {YELLOW}{bridge.get('pid', '无') or '无'}{NC}")
    
    uptime = bridge.get('uptime')
    if uptime:
        uptime_seconds = (time.time() * 1000 - uptime) / 1000
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        print(f"  运行时间:   {YELLOW}{hours}小时{minutes}分钟{NC}")
    
    print(f"  重启次数:   {YELLOW}{bridge.get('restarts', 0)}{NC}")
    print(f"  CPU 使用:   {YELLOW}{bridge.get('cpu', 0)}%{NC}")
    
    memory = bridge.get('memory', 0)
    if memory:
        print(f"  内存使用:   {YELLOW}{memory / 1024 / 1024:.1f} MB{NC}")
    
    config = load_config(bridge['work_id'])
    
    print(f"\n{CYAN}配置信息:{NC}")
    print(f"  API地址:    {YELLOW}{config.get('api_base_url', '未配置')}{NC}")
    print(f"  AI API:     {YELLOW}{config.get('ai_api_url', '未配置')}{NC}")
    print(f"  AI模型:     {YELLOW}{config.get('ai_model', '未配置')}{NC}")
    print(f"  云变量名:   {YELLOW}{config.get('variable_name', '未配置')}{NC}")
    print()


def add_work():
    """添加新作品"""
    print(f"\n{CYAN}════════════════════════════════════════════════════════════════{NC}")
    print(f"{CYAN}添加新作品{NC}")
    print(f"{CYAN}════════════════════════════════════════════════════════════════{NC}\n")
    
    work_id = input("请输入作品ID: ").strip()
    
    if not work_id:
        log("WARN", "未输入作品ID，取消操作")
        return
    
    if not work_id.isdigit():
        log("ERROR", "作品ID必须是数字")
        return
    
    instance_name = f"ai-bridge-{work_id}"
    
    bridges = get_all_ai_bridges()
    for b in bridges:
        if b['work_id'] == work_id:
            log("WARN", f"作品 {work_id} 已存在")
            return
    
    config_file = get_config_path(work_id)
    
    if not config_file.exists():
        print(f"\n{CYAN}配置作品 {work_id} 的参数:{NC}\n")
        
        config = {}
        
        api_base_url = input("API服务地址 (默认 http://localhost:9178): ").strip()
        config['api_base_url'] = api_base_url if api_base_url else "http://localhost:9178"
        
        ai_api_url = input("AI API 地址: ").strip()
        if not ai_api_url:
            log("ERROR", "AI API 地址不能为空")
            return
        config['ai_api_url'] = ai_api_url
        
        ai_api_key = input("AI API Key: ").strip()
        if not ai_api_key:
            log("ERROR", "AI API Key 不能为空")
            return
        config['ai_api_key'] = ai_api_key
        
        ai_model = input("AI 模型名称 (默认 gpt-3.5-turbo): ").strip()
        config['ai_model'] = ai_model if ai_model else "gpt-3.5-turbo"
        
        variable_name = input("云变量名 (默认 API): ").strip()
        config['variable_name'] = variable_name if variable_name else "API"
        
        question_prefix = input("问题前缀 (默认 QWQ~~~): ").strip()
        config['question_prefix'] = question_prefix if question_prefix else "QWQ~~~"
        
        answer_prefix = input("答案前缀 (默认 OKOKOK~~~): ").strip()
        config['answer_prefix'] = answer_prefix if answer_prefix else "OKOKOK~~~"
        
        config['request_timeout'] = 60
        config['max_retries'] = 5
        config['log_dir'] = str(LOGS_DIR)
        
        prompt_file = get_prompt_path(work_id)
        config['system_prompt_file'] = str(prompt_file)
        
        save_config(config, work_id)
        
        use_default_prompt = input("\n使用默认提示词? (y/n, 默认y): ").strip().lower()
        if use_default_prompt != 'n':
            save_prompt(DEFAULT_PROMPT, work_id)
        else:
            print(f"\n请编辑提示词文件: {prompt_file}")
    
    log("STEP", f"正在启动实例 {instance_name}...")
    
    cmd = f'pm2 start {SCRIPT_DIR}/kitten_ai_bridge.py --name "{instance_name}" --interpreter python3 -- -w {work_id} -c {config_file}'
    
    returncode, output = run_command(cmd)
    
    if returncode == 0:
        run_command("pm2 save")
        log("SUCCESS", f"作品 {work_id} 已添加并启动")
        show_all_status()
    else:
        log("ERROR", f"启动失败: {output}")


def remove_work(work_id: str = None):
    """移除作品"""
    if not work_id:
        show_all_status()
        work_id = input("\n请输入要移除的作品ID: ").strip()
    
    if not work_id:
        log("WARN", "未输入作品ID，取消操作")
        return
    
    instance_name = f"ai-bridge-{work_id}"
    
    confirm = input(f"确定要移除作品 {work_id} 吗? (y/n): ").strip().lower()
    if confirm != 'y':
        log("INFO", "取消操作")
        return
    
    log("STEP", f"正在停止并删除实例 {instance_name}...")
    
    run_command(f"pm2 stop {instance_name}")
    run_command(f"pm2 delete {instance_name}")
    run_command("pm2 save")
    
    log("SUCCESS", f"作品 {work_id} 已移除")
    
    delete_config = input("是否同时删除配置文件? (y/n): ").strip().lower()
    if delete_config == 'y':
        config_file = get_config_path(work_id)
        prompt_file = get_prompt_path(work_id)
        
        if config_file.exists():
            config_file.unlink()
        if prompt_file.exists():
            prompt_file.unlink()
        
        log("SUCCESS", "配置文件已删除")


def show_logs(work_id: str = None, lines: int = 50):
    """显示日志"""
    if work_id:
        instance_name = f"ai-bridge-{work_id}"
    else:
        show_all_status()
        work_id = input("\n请输入作品ID (回车查看所有日志): ").strip()
        if work_id:
            instance_name = f"ai-bridge-{work_id}"
        else:
            instance_name = "ai-bridge-"
    
    print(f"\n{CYAN}════════════════════════════════════════════════════════════════{NC}")
    print(f"{CYAN}日志 (最近 {lines} 行){NC}")
    print(f"{CYAN}════════════════════════════════════════════════════════════════{NC}\n")
    
    run_command(f"pm2 logs {instance_name} --lines {lines} --nostream", capture=False)


def clear_logs():
    """清除所有日志"""
    print(f"\n{CYAN}════════════════════════════════════════════════════════════════{NC}")
    print(f"{CYAN}清除日志{NC}")
    print(f"{CYAN}════════════════════════════════════════════════════════════════{NC}\n")
    
    confirm = input("确定要清除所有 AI 桥接日志吗? (y/n): ").strip().lower()
    if confirm != 'y':
        log("INFO", "取消操作")
        return
    
    log("STEP", "正在清除日志...")
    
    run_command("pm2 flush")
    
    if LOGS_DIR.exists():
        for log_file in LOGS_DIR.glob("*.log"):
            log_file.unlink()
        for log_file in LOGS_DIR.glob("*.json"):
            log_file.unlink()
    
    log("SUCCESS", "日志已清除")


def restart_instance(work_id: str = None):
    """重启实例"""
    if not work_id:
        show_all_status()
        work_id = input("\n请输入要重启的作品ID: ").strip()
    
    if not work_id:
        log("WARN", "未输入作品ID，取消操作")
        return
    
    instance_name = f"ai-bridge-{work_id}"
    
    log("STEP", f"正在重启实例 {instance_name}...")
    
    returncode, output = run_command(f"pm2 restart {instance_name}")
    
    if returncode == 0:
        log("SUCCESS", f"实例 {instance_name} 已重启")
        time.sleep(2)
        show_instance_status(work_id)
    else:
        log("ERROR", f"重启失败: {output}")


def stop_instance(work_id: str = None):
    """停止实例"""
    if not work_id:
        show_all_status()
        work_id = input("\n请输入要停止的作品ID: ").strip()
    
    if not work_id:
        log("WARN", "未输入作品ID，取消操作")
        return
    
    instance_name = f"ai-bridge-{work_id}"
    
    log("STEP", f"正在停止实例 {instance_name}...")
    
    returncode, output = run_command(f"pm2 stop {instance_name}")
    
    if returncode == 0:
        log("SUCCESS", f"实例 {instance_name} 已停止")
    else:
        log("ERROR", f"停止失败: {output}")


def edit_config(work_id: str = None):
    """编辑配置"""
    if not work_id:
        show_all_status()
        work_id = input("\n请输入作品ID: ").strip()
    
    if not work_id:
        log("WARN", "未输入作品ID，取消操作")
        return
    
    config = load_config(work_id)
    
    print(f"\n{CYAN}════════════════════════════════════════════════════════════════{NC}")
    print(f"{CYAN}编辑配置 (作品: {work_id}){NC}")
    print(f"{CYAN}════════════════════════════════════════════════════════════════{NC}\n")
    
    print(f"当前 API 服务地址: {YELLOW}{config.get('api_base_url', '未配置')}{NC}")
    new_val = input("新的 API 服务地址 (回车保持不变): ").strip()
    if new_val:
        config['api_base_url'] = new_val
    
    print(f"\n当前 AI API 地址: {YELLOW}{config.get('ai_api_url', '未配置')}{NC}")
    new_val = input("新的 AI API 地址 (回车保持不变): ").strip()
    if new_val:
        config['ai_api_url'] = new_val
    
    print(f"\n当前 AI API Key: {YELLOW}{'*' * 10}{config.get('ai_api_key', '')[-4:] if config.get('ai_api_key') else '未配置'}{NC}")
    new_val = input("新的 AI API Key (回车保持不变): ").strip()
    if new_val:
        config['ai_api_key'] = new_val
    
    print(f"\n当前 AI 模型: {YELLOW}{config.get('ai_model', '未配置')}{NC}")
    new_val = input("新的 AI 模型 (回车保持不变): ").strip()
    if new_val:
        config['ai_model'] = new_val
    
    print(f"\n当前云变量名: {YELLOW}{config.get('variable_name', '未配置')}{NC}")
    new_val = input("新的云变量名 (回车保持不变): ").strip()
    if new_val:
        config['variable_name'] = new_val
    
    print(f"\n当前问题前缀: {YELLOW}{config.get('question_prefix', '未配置')}{NC}")
    new_val = input("新的问题前缀 (回车保持不变): ").strip()
    if new_val:
        config['question_prefix'] = new_val
    
    print(f"\n当前答案前缀: {YELLOW}{config.get('answer_prefix', '未配置')}{NC}")
    new_val = input("新的答案前缀 (回车保持不变): ").strip()
    if new_val:
        config['answer_prefix'] = new_val
    
    save_config(config, work_id)
    
    restart = input("\n是否立即重启实例? (y/n): ").strip().lower()
    if restart == 'y':
        restart_instance(work_id)


def edit_prompt(work_id: str = None):
    """编辑提示词"""
    if not work_id:
        show_all_status()
        work_id = input("\n请输入作品ID: ").strip()
    
    if not work_id:
        log("WARN", "未输入作品ID，取消操作")
        return
    
    current_prompt = load_prompt(work_id)
    
    print(f"\n{CYAN}════════════════════════════════════════════════════════════════{NC}")
    print(f"{CYAN}编辑提示词 (作品: {work_id}){NC}")
    print(f"{CYAN}════════════════════════════════════════════════════════════════{NC}\n")
    
    print(f"当前提示词 ({len(current_prompt)} 字符):")
    print(f"{YELLOW}{'-' * 50}{NC}")
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
        print(f"\n{CYAN}完整提示词:{NC}")
        print(f"{YELLOW}{'-' * 50}{NC}")
        print(current_prompt)
        print(f"{YELLOW}{'-' * 50}{NC}")
        input("\n按回车继续...")
    
    elif choice == '2':
        print(f"\n{CYAN}正在打开编辑器...{NC}")
        print(f"提示: 编辑完成后按 Ctrl+X 保存退出\n")
        time.sleep(1)
        
        prompt_file = get_prompt_path(work_id)
        prompt_file.parent.mkdir(parents=True, exist_ok=True)
        
        temp_file = CONFIG_DIR / f"temp_prompt_{work_id}.txt"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(current_prompt)
        
        os.system(f"nano {temp_file}")
        
        if temp_file.exists():
            with open(temp_file, 'r', encoding='utf-8') as f:
                new_prompt = f.read()
            
            if new_prompt.strip() and new_prompt != current_prompt:
                save_prompt(new_prompt, work_id)
                
                restart = input("\n是否立即重启实例? (y/n): ").strip().lower()
                if restart == 'y':
                    restart_instance(work_id)
            else:
                log("INFO", "提示词未更改")
            
            temp_file.unlink()
    
    elif choice == '3':
        confirm = input("确定要重置为默认提示词吗? (y/n): ").strip().lower()
        if confirm == 'y':
            save_prompt(DEFAULT_PROMPT, work_id)
            log("SUCCESS", "已重置为默认提示词")
            
            restart = input("\n是否立即重启实例? (y/n): ").strip().lower()
            if restart == 'y':
                restart_instance(work_id)


def show_help():
    """显示帮助"""
    print(f"""
{CYAN}使用方法:{NC}
  python3 ai_bridge_manager.py              # 交互菜单
  python3 ai_bridge_manager.py status       # 查看所有实例状态
  python3 ai_bridge_manager.py add          # 添加作品
  python3 ai_bridge_manager.py remove       # 移除作品
  python3 ai_bridge_manager.py restart      # 重启实例
  python3 ai_bridge_manager.py stop         # 停止实例
  python3 ai_bridge_manager.py logs         # 查看日志
  python3 ai_bridge_manager.py clear-logs   # 清除日志
  python3 ai_bridge_manager.py config       # 编辑配置
  python3 ai_bridge_manager.py prompt       # 编辑提示词

{CYAN}多作品管理:{NC}
  每个作品独立运行一个 PM2 实例
  实例命名格式: ai-bridge-{作品ID}
  配置文件: ai-bridge/config_{作品ID}.py
  提示词: ai-bridge/system_prompt_{作品ID}.txt

{CYAN}配置文件目录:{NC}
  {CONFIG_DIR}
""")


def show_menu():
    """显示主菜单"""
    while True:
        print(f"\n{PURPLE}════════════════════════════════════════════════════════════════{NC}")
        print(f"{PURPLE}AI 桥接管理菜单{NC}")
        print(f"{PURPLE}════════════════════════════════════════════════════════════════{NC}\n")
        
        print(f"  {CYAN}1.{NC} 查看所有实例状态")
        print(f"  {CYAN}2.{NC} 添加作品")
        print(f"  {CYAN}3.{NC} 移除作品")
        print(f"  {CYAN}4.{NC} 重启实例")
        print(f"  {CYAN}5.{NC} 停止实例")
        print(f"  {CYAN}6.{NC} 查看日志")
        print(f"  {CYAN}7.{NC} 清除日志")
        print(f"  {CYAN}8.{NC} 编辑配置")
        print(f"  {CYAN}9.{NC} 编辑提示词")
        print(f"  {CYAN}0.{NC} 退出")
        print()
        
        choice = input("请选择操作: ").strip()
        
        if choice == '1':
            show_all_status()
        elif choice == '2':
            add_work()
        elif choice == '3':
            remove_work()
        elif choice == '4':
            restart_instance()
        elif choice == '5':
            stop_instance()
        elif choice == '6':
            show_logs()
        elif choice == '7':
            clear_logs()
        elif choice == '8':
            edit_config()
        elif choice == '9':
            edit_prompt()
        elif choice == '0':
            print(f"\n{GREEN}再见！{NC}\n")
            break
        else:
            log("WARN", "无效选择，请重新输入")


def main():
    print_banner()
    
    if not PM2_AVAILABLE:
        log("ERROR", "PM2 未找到，请确保已安装 PM2")
        log("INFO", "运行: npm install -g pm2")
        return
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'status':
            show_all_status()
        elif command == 'add':
            add_work()
        elif command == 'remove':
            remove_work(sys.argv[2] if len(sys.argv) > 2 else None)
        elif command == 'restart':
            restart_instance(sys.argv[2] if len(sys.argv) > 2 else None)
        elif command == 'stop':
            stop_instance(sys.argv[2] if len(sys.argv) > 2 else None)
        elif command == 'logs':
            show_logs(sys.argv[2] if len(sys.argv) > 2 else None)
        elif command == 'clear-logs':
            clear_logs()
        elif command == 'config':
            edit_config(sys.argv[2] if len(sys.argv) > 2 else None)
        elif command == 'prompt':
            edit_prompt(sys.argv[2] if len(sys.argv) > 2 else None)
        elif command in ['help', '-h', '--help']:
            show_help()
        else:
            log("ERROR", f"未知命令: {command}")
            show_help()
    else:
        show_menu()


if __name__ == "__main__":
    main()
