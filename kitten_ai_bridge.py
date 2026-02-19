#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kitten Cloud API - AI 桥接程序
功能：轮询云变量，调用AI API，实现编程猫作品与AI的交互
支持：日志记录、统计功能、断电恢复查看、配置文件读取

使用方法：
  python3 kitten_ai_bridge.py                              # 交互模式
  python3 kitten_ai_bridge.py -w 123456                    # 指定作品ID
  python3 kitten_ai_bridge.py -w 123456 -u http://xxx/api  # 指定API地址
  python3 kitten_ai_bridge.py -c ./ai-bridge/config.py     # 使用配置文件
"""

import requests
import time
import sys
import json
import os
import argparse
from datetime import datetime, timedelta

# ==================== 默认配置 ====================
# 注意：这些是默认值，实际配置应通过配置文件或命令行参数传入
DEFAULT_CONFIG = {
    "api_base_url": "",
    "ai_api_url": "",
    "ai_api_key": "",
    "ai_model": "gpt-3.5-turbo",
    "question_prefix": "QWQ~~~",
    "answer_prefix": "OKOKOK~~~",
    "variable_name": "API",
    "system_prompt_file": "",
    "request_timeout": 60,
    "max_retries": 5,
    "log_dir": "."
}

# 运行时配置（从配置文件或命令行参数加载）
CONFIG = DEFAULT_CONFIG.copy()

# 记录上次处理的值，避免重复处理
last_processed_value = None

# 统计数据
stats = {
    "start_time": None,
    "end_time": None,
    "total_polls": 0,
    "total_questions": 0,
    "successful_answers": 0,
    "failed_answers": 0,
    "total_errors": 0,
    "online_periods": []
}

# 默认系统提示词（当文件不存在时使用）
DEFAULT_SYSTEM_PROMPT = """# AI助手提示词

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


def load_system_prompt() -> str:
    """
    加载系统提示词
    优先从配置文件指定的路径读取，如果不存在则使用默认提示词
    
    Returns:
        系统提示词内容
    """
    prompt_file = CONFIG.get("system_prompt_file", "")
    
    if prompt_file and os.path.exists(prompt_file):
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    return content
        except Exception as e:
            print(f"读取提示词文件失败: {e}")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_prompt_path = os.path.join(script_dir, "ai-bridge", "system_prompt.txt")
    
    if os.path.exists(default_prompt_path):
        try:
            with open(default_prompt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    return content
        except Exception as e:
            print(f"读取默认提示词文件失败: {e}")
    
    return DEFAULT_SYSTEM_PROMPT


def load_config_from_file(config_path: str) -> bool:
    """
    从配置文件加载配置
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        是否加载成功
    """
    global CONFIG
    
    if not os.path.exists(config_path):
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        safe_globals = {
            '__builtins__': {
                'True': True,
                'False': False,
                'None': None,
            }
        }
        safe_locals = {}
        exec(content, safe_globals, safe_locals)
        
        if 'CONFIG' in safe_locals:
            file_config = safe_locals['CONFIG']
            for key in DEFAULT_CONFIG:
                if key in file_config and file_config[key]:
                    CONFIG[key] = file_config[key]
            return True
        
        return False
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return False


def get_poll_interval() -> int:
    """
    根据当前时间获取轮询间隔
    白天(6:00-18:00): 3秒
    晚上(18:00-23:00): 5秒
    凌晨(23:00-6:00): 10秒
    """
    hour = datetime.now().hour
    if 6 <= hour < 18:
        return 3
    elif 18 <= hour < 23:
        return 5
    else:
        return 10


def ensure_log_dir():
    """确保日志目录存在"""
    log_dir = CONFIG.get("log_dir", ".")
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)


def get_log_file_path():
    """获取当日日志文件路径"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(CONFIG["log_dir"], f"ai_bridge_{date_str}.log")


def get_stats_file_path():
    """获取统计文件路径"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(CONFIG["log_dir"], f"stats_{date_str}.json")


def write_log(message: str, log_type: str = "INFO"):
    """
    写入日志文件
    
    Args:
        message: 日志消息
        log_type: 日志类型
    """
    ensure_log_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{log_type}] {message}\n"
    
    try:
        with open(get_log_file_path(), "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception as e:
        print(f"写入日志失败: {e}")


def write_call_record(question: str, answer: str, success: bool, duration: float):
    """
    写入调用记录
    
    Args:
        question: 问题
        answer: 答复
        success: 是否成功
        duration: 耗时（秒）
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "成功" if success else "失败"
    
    record = f"""
{'='*60}
时间: {timestamp}
状态: {status}
耗时: {duration:.2f}秒
问题: {question}
答复: {answer}
{'='*60}
"""
    
    try:
        with open(get_log_file_path(), "a", encoding="utf-8") as f:
            f.write(record)
    except Exception as e:
        print(f"写入调用记录失败: {e}")


def save_stats():
    """保存统计数据到文件"""
    ensure_log_dir()
    
    stats_data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "start_time": stats["start_time"].strftime("%Y-%m-%d %H:%M:%S") if stats["start_time"] else None,
        "end_time": stats["end_time"].strftime("%Y-%m-%d %H:%M:%S") if stats["end_time"] else None,
        "total_polls": stats["total_polls"],
        "total_questions": stats["total_questions"],
        "successful_answers": stats["successful_answers"],
        "failed_answers": stats["failed_answers"],
        "total_errors": stats["total_errors"],
        "uptime_seconds": calculate_uptime(),
        "online_periods": [
            {
                "start": p[0].strftime("%Y-%m-%d %H:%M:%S") if isinstance(p[0], datetime) else p[0],
                "end": p[1].strftime("%Y-%m-%d %H:%M:%S") if isinstance(p[1], datetime) else p[1]
            }
            for p in stats["online_periods"]
        ]
    }
    
    try:
        with open(get_stats_file_path(), "w", encoding="utf-8") as f:
            json.dump(stats_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存统计失败: {e}")


def calculate_uptime() -> int:
    """计算运行时长（秒）"""
    if stats["start_time"] and stats["end_time"]:
        return int((stats["end_time"] - stats["start_time"]).total_seconds())
    elif stats["start_time"]:
        return int((datetime.now() - stats["start_time"]).total_seconds())
    return 0


def format_uptime(seconds: int) -> str:
    """格式化运行时长"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours}小时{minutes}分钟{secs}秒"


def print_banner():
    """打印程序横幅"""
    print("=" * 60)
    print("  Kitten Cloud API - AI 桥接程序")
    print("  版本: 2.1.0 (支持提示词文件读取)")
    print("=" * 60)
    print()


def log(level: str, message: str):
    """
    打印带时间戳的日志并写入文件
    
    Args:
        level: 日志级别 (INFO, SUCCESS, ERROR, WARNING)
        message: 日志消息
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    level_colors = {
        "INFO": "\033[94m",
        "SUCCESS": "\033[92m",
        "ERROR": "\033[91m",
        "WARNING": "\033[93m",
        "DEBUG": "\033[90m",
        "STATS": "\033[95m"
    }
    reset_color = "\033[0m"
    color = level_colors.get(level, "")
    print(f"[{timestamp}] {color}[{level}]{reset_color} {message}")
    
    write_log(message, level)


def print_stats():
    """打印当前统计信息"""
    uptime = calculate_uptime()
    success_rate = (stats["successful_answers"] / stats["total_questions"] * 100) if stats["total_questions"] > 0 else 0
    
    print()
    log("STATS", "=" * 50)
    log("STATS", "当前运行统计:")
    log("STATS", f"  运行时长: {format_uptime(uptime)}")
    log("STATS", f"  轮询次数: {stats['total_polls']}")
    log("STATS", f"  收到问题: {stats['total_questions']}")
    log("STATS", f"  成功答复: {stats['successful_answers']}")
    log("STATS", f"  失败答复: {stats['failed_answers']}")
    log("STATS", f"  成功率: {success_rate:.1f}%")
    log("STATS", f"  错误次数: {stats['total_errors']}")
    log("STATS", "=" * 50)
    print()


def print_config():
    """打印当前配置"""
    log("INFO", "=" * 50)
    log("INFO", "当前配置:")
    log("INFO", f"  API服务地址: {CONFIG['api_base_url']}")
    log("INFO", f"  AI API地址: {CONFIG['ai_api_url']}")
    log("INFO", f"  AI模型: {CONFIG['ai_model']}")
    log("INFO", f"  云变量名: {CONFIG['variable_name']}")
    log("INFO", f"  问题前缀: {CONFIG['question_prefix']}")
    log("INFO", f"  答案前缀: {CONFIG['answer_prefix']}")
    log("INFO", f"  提示词文件: {CONFIG.get('system_prompt_file', '使用默认')}")
    log("INFO", f"  日志目录: {CONFIG['log_dir']}")
    log("INFO", "=" * 50)


def connect_to_work(api_base_url: str, work_id: int) -> dict:
    """
    连接到编程猫作品
    
    Args:
        api_base_url: API基础地址
        work_id: 作品ID
        
    Returns:
        连接信息字典
    """
    url = f"{api_base_url}/connection/connect"
    payload = {"workId": work_id}
    
    try:
        response = requests.post(url, json=payload, timeout=CONFIG["request_timeout"])
        data = response.json()
        
        if data.get("success"):
            return {
                "success": True,
                "data": data.get("data", {}),
                "message": data.get("message", "连接成功")
            }
        else:
            return {
                "success": False,
                "error": data.get("error", "UNKNOWN_ERROR"),
                "message": data.get("message", "连接失败")
            }
    except requests.exceptions.Timeout:
        return {"success": False, "error": "TIMEOUT", "message": "请求超时"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "CONNECTION_ERROR", "message": "无法连接到API服务"}
    except Exception as e:
        return {"success": False, "error": "EXCEPTION", "message": str(e)}


def get_variable(api_base_url: str, work_id: int, var_name: str) -> dict:
    """
    获取云变量的值（带重试机制）
    
    Args:
        api_base_url: API基础地址
        work_id: 作品ID
        var_name: 变量名
        
    Returns:
        包含变量值的字典
    """
    url = f"{api_base_url}/var/get"
    payload = {"workId": work_id, "name": var_name}
    
    for attempt in range(CONFIG["max_retries"]):
        try:
            response = requests.post(url, json=payload, timeout=CONFIG["request_timeout"])
            data = response.json()
            
            if data.get("success"):
                var_data = data.get("data", {})
                return {
                    "success": True,
                    "value": var_data.get("value"),
                    "type": var_data.get("type"),
                    "name": var_data.get("name")
                }
            else:
                return {
                    "success": False,
                    "error": data.get("error", "UNKNOWN_ERROR"),
                    "message": data.get("message", "获取变量失败")
                }
        except requests.exceptions.Timeout:
            if attempt < CONFIG["max_retries"] - 1:
                time.sleep(2)
                continue
            return {"success": False, "error": "TIMEOUT", "message": "请求超时"}
        except requests.exceptions.ConnectionError:
            if attempt < CONFIG["max_retries"] - 1:
                time.sleep(2)
                continue
            return {"success": False, "error": "CONNECTION_ERROR", "message": "无法连接到API服务"}
        except Exception as e:
            if attempt < CONFIG["max_retries"] - 1:
                time.sleep(2)
                continue
            return {"success": False, "error": "EXCEPTION", "message": str(e)}
    
    return {"success": False, "error": "MAX_RETRIES", "message": "超过最大重试次数"}


def set_variable(api_base_url: str, work_id: int, var_name: str, value: str, var_type: str = "public") -> dict:
    """
    设置云变量的值（带重试机制）
    
    Args:
        api_base_url: API基础地址
        work_id: 作品ID
        var_name: 变量名
        value: 要设置的值
        var_type: 变量类型 (public/private)
        
    Returns:
        操作结果字典
    """
    url = f"{api_base_url}/var/set"
    payload = {
        "workId": work_id,
        "name": var_name,
        "value": value,
        "type": var_type
    }
    
    for attempt in range(CONFIG["max_retries"]):
        try:
            response = requests.post(url, json=payload, timeout=CONFIG["request_timeout"])
            data = response.json()
            
            if data.get("success"):
                return {
                    "success": True,
                    "message": data.get("message", "设置成功")
                }
            else:
                return {
                    "success": False,
                    "error": data.get("error", "UNKNOWN_ERROR"),
                    "message": data.get("message", "设置变量失败")
                }
        except requests.exceptions.Timeout:
            if attempt < CONFIG["max_retries"] - 1:
                time.sleep(2)
                continue
            return {"success": False, "error": "TIMEOUT", "message": "请求超时"}
        except requests.exceptions.ConnectionError:
            if attempt < CONFIG["max_retries"] - 1:
                time.sleep(2)
                continue
            return {"success": False, "error": "CONNECTION_ERROR", "message": "无法连接到API服务"}
        except Exception as e:
            if attempt < CONFIG["max_retries"] - 1:
                time.sleep(2)
                continue
            return {"success": False, "error": "EXCEPTION", "message": str(e)}
    
    return {"success": False, "error": "MAX_RETRIES", "message": "超过最大重试次数"}


def call_ai_api(question: str) -> dict:
    """
    调用AI API获取答复
    
    Args:
        question: 用户问题
        
    Returns:
        包含AI答复的字典
    """
    system_prompt = load_system_prompt()
    
    headers = {
        "Authorization": f"Bearer {CONFIG['ai_api_key']}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": CONFIG["ai_model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    for attempt in range(CONFIG["max_retries"]):
        try:
            response = requests.post(
                CONFIG["ai_api_url"],
                headers=headers,
                json=payload,
                timeout=CONFIG["request_timeout"]
            )
            
            if response.status_code == 200:
                data = response.json()
                choices = data.get("choices", [])
                if choices:
                    answer = choices[0].get("message", {}).get("content", "")
                    return {
                        "success": True,
                        "answer": answer,
                        "model": data.get("model", CONFIG["ai_model"])
                    }
                else:
                    return {"success": False, "error": "EMPTY_RESPONSE", "message": "AI返回空响应"}
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                return {
                    "success": False,
                    "error": f"HTTP_{response.status_code}",
                    "message": error_data.get("error", {}).get("message", f"HTTP错误: {response.status_code}")
                }
                
        except requests.exceptions.Timeout:
            if attempt < CONFIG["max_retries"] - 1:
                log("WARNING", f"AI API请求超时，重试中... ({attempt + 1}/{CONFIG['max_retries']})")
                time.sleep(2)
                continue
            return {"success": False, "error": "TIMEOUT", "message": "AI API请求超时"}
            
        except requests.exceptions.ConnectionError:
            if attempt < CONFIG["max_retries"] - 1:
                log("WARNING", f"无法连接AI API，重试中... ({attempt + 1}/{CONFIG['max_retries']})")
                time.sleep(2)
                continue
            return {"success": False, "error": "CONNECTION_ERROR", "message": "无法连接到AI API"}
            
        except Exception as e:
            return {"success": False, "error": "EXCEPTION", "message": str(e)}
    
    return {"success": False, "error": "MAX_RETRIES", "message": "超过最大重试次数"}


def parse_question(value: str) -> tuple:
    """
    解析云变量值，提取问题
    
    Args:
        value: 云变量的值
        
    Returns:
        (是否为新问题, 问题内容)
    """
    global last_processed_value
    
    prefix = CONFIG["question_prefix"]
    
    if not value or not isinstance(value, str):
        return False, None
    
    if not value.startswith(prefix):
        return False, None
    
    if value == last_processed_value:
        return False, None
    
    question = value[len(prefix):].strip()
    return True, question


def validate_config() -> bool:
    """
    验证配置是否完整
    
    Returns:
        配置是否有效
    """
    required_fields = ["api_base_url", "ai_api_url", "ai_api_key", "ai_model", "variable_name"]
    missing = []
    
    for field in required_fields:
        if not CONFIG.get(field):
            missing.append(field)
    
    if missing:
        log("ERROR", f"缺少必要配置项: {', '.join(missing)}")
        return False
    
    return True


def main():
    """主函数"""
    global last_processed_value, CONFIG
    
    parser = argparse.ArgumentParser(
        description='Kitten Cloud API - AI 桥接程序',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s -w 123456                                    # 使用默认配置
  %(prog)s -w 123456 -u http://localhost:9178/api       # 指定API地址
  %(prog)s -c ./ai-bridge/config.py                     # 使用配置文件
  %(prog)s -w 123456 --ai-url https://api.xxx.com/v1/chat/completions --ai-key sk-xxx --ai-model gpt-4
        """
    )
    
    # 基本参数
    parser.add_argument('-w', '--work-id', type=int, help='作品ID（必填）')
    parser.add_argument('-u', '--api-url', type=str, help='API服务地址（如: http://localhost:9178/api）')
    parser.add_argument('-c', '--config', type=str, help='配置文件路径（如: ./ai-bridge/config.py）')
    
    # AI API 参数
    parser.add_argument('--ai-url', type=str, help='AI API地址（如: https://api.openai.com/v1/chat/completions）')
    parser.add_argument('--ai-key', type=str, help='AI API Key')
    parser.add_argument('--ai-model', type=str, help='AI模型名称（如: gpt-3.5-turbo）')
    
    # 云变量参数
    parser.add_argument('--var-name', type=str, help='云变量名（默认: API）')
    parser.add_argument('--question-prefix', type=str, help='问题前缀（默认: QWQ~~~）')
    parser.add_argument('--answer-prefix', type=str, help='答案前缀（默认: OKOKOK~~~）')
    
    # 其他参数
    parser.add_argument('--log-dir', type=str, help='日志目录')
    parser.add_argument('--prompt-file', type=str, help='系统提示词文件路径')
    parser.add_argument('-d', '--daemon', action='store_true', help='后台运行模式（无交互输入）')
    parser.add_argument('--show-config', action='store_true', help='显示当前配置后退出')
    
    args = parser.parse_args()
    
    print_banner()
    
    # 1. 先加载配置文件（如果指定）
    if args.config:
        if load_config_from_file(args.config):
            log("SUCCESS", f"已加载配置文件: {args.config}")
        else:
            log("WARNING", f"无法加载配置文件: {args.config}")
    
    # 2. 命令行参数覆盖配置文件
    if args.api_url:
        CONFIG["api_base_url"] = args.api_url
    if args.ai_url:
        CONFIG["ai_api_url"] = args.ai_url
    if args.ai_key:
        CONFIG["ai_api_key"] = args.ai_key
    if args.ai_model:
        CONFIG["ai_model"] = args.ai_model
    if args.var_name:
        CONFIG["variable_name"] = args.var_name
    if args.question_prefix:
        CONFIG["question_prefix"] = args.question_prefix
    if args.answer_prefix:
        CONFIG["answer_prefix"] = args.answer_prefix
    if args.log_dir:
        CONFIG["log_dir"] = args.log_dir
    if args.prompt_file:
        CONFIG["system_prompt_file"] = args.prompt_file
    
    # 3. 显示配置模式
    if args.show_config:
        print_config()
        sys.exit(0)
    
    # 4. 交互模式获取缺失参数
    work_id = args.work_id
    
    if work_id:
        log("INFO", f"作品ID: {work_id}")
    elif args.daemon or not sys.stdin.isatty():
        log("ERROR", "后台运行模式必须指定作品ID: python3 kitten_ai_bridge.py -w 123456")
        sys.exit(1)
    else:
        try:
            work_id_input = input("请输入作品ID: ").strip()
            try:
                work_id = int(work_id_input)
            except ValueError:
                log("ERROR", "作品ID必须是数字")
                sys.exit(1)
        except (EOFError, OSError):
            log("ERROR", "无法读取输入，请使用命令行参数: python3 kitten_ai_bridge.py -w 123456")
            sys.exit(1)
    
    if work_id <= 0:
        log("ERROR", "作品ID必须是正整数")
        sys.exit(1)
    
    # 5. 交互模式获取其他缺失配置
    if not args.daemon and sys.stdin.isatty():
        if not CONFIG.get("api_base_url"):
            api_input = input("请输入API服务地址: ").strip()
            if api_input:
                CONFIG["api_base_url"] = api_input
        
        if not CONFIG.get("ai_api_url"):
            ai_url_input = input("请输入AI API地址: ").strip()
            if ai_url_input:
                CONFIG["ai_api_url"] = ai_url_input
        
        if not CONFIG.get("ai_api_key"):
            ai_key_input = input("请输入AI API Key: ").strip()
            if ai_key_input:
                CONFIG["ai_api_key"] = ai_key_input
        
        if not CONFIG.get("ai_model"):
            model_input = input("请输入AI模型名称 (默认: gpt-3.5-turbo): ").strip()
            if model_input:
                CONFIG["ai_model"] = model_input
            else:
                CONFIG["ai_model"] = "gpt-3.5-turbo"
    
    # 6. 验证配置
    if not validate_config():
        log("ERROR", "配置不完整，请检查必要参数")
        print()
        print("使用方法:")
        print("  方式1: 使用配置文件")
        print("    python3 kitten_ai_bridge.py -w 123456 -c ./ai-bridge/config.py")
        print()
        print("  方式2: 使用命令行参数")
        print("    python3 kitten_ai_bridge.py -w 123456 -u http://localhost:9178/api \\")
        print("      --ai-url https://api.openai.com/v1/chat/completions \\")
        print("      --ai-key sk-xxx --ai-model gpt-3.5-turbo")
        sys.exit(1)
    
    # 7. 显示当前配置
    print()
    print_config()
    print()
    
    # 8. 连接作品
    log("INFO", f"正在连接作品 {work_id}...")
    
    connect_result = connect_to_work(CONFIG["api_base_url"], work_id)
    if not connect_result["success"]:
        log("ERROR", f"连接失败: {connect_result.get('message', '未知错误')}")
        sys.exit(1)
    
    conn_data = connect_result.get("data", {})
    online_users = conn_data.get("onlineUsers", "未知")
    log("SUCCESS", f"连接成功！在线人数: {online_users}")
    print()
    
    stats["start_time"] = datetime.now()
    stats["online_periods"].append([datetime.now(), None])
    
    write_log(f"程序启动 - 作品ID: {work_id}", "SYSTEM")
    write_log(f"连接成功 - 在线人数: {online_users}", "SYSTEM")
    
    log("INFO", f"开始轮询云变量 '{CONFIG['variable_name']}'...")
    log("INFO", "轮询间隔: 白天3秒 / 晚上5秒 / 凌晨10秒")
    log("INFO", "按 Ctrl+C 退出程序")
    log("INFO", f"日志文件: {get_log_file_path()}")
    log("INFO", f"统计文件: {get_stats_file_path()}")
    print()
    
    poll_count = 0
    last_stats_print = datetime.now()
    consecutive_errors = 0
    max_consecutive_errors = 3
    reconnect_fail_count = 0
    max_reconnect_fails = 3
    
    try:
        while True:
            poll_count += 1
            stats["total_polls"] = poll_count
            
            var_result = get_variable(CONFIG["api_base_url"], work_id, CONFIG["variable_name"])
            
            if not var_result["success"]:
                consecutive_errors += 1
                log("ERROR", f"获取变量失败: {var_result.get('message', '未知错误')} (连续失败: {consecutive_errors}/{max_consecutive_errors})")
                stats["total_errors"] += 1
                
                if consecutive_errors >= max_consecutive_errors:
                    log("WARNING", "连续失败次数过多，尝试重新连接作品...")
                    reconnect_result = connect_to_work(CONFIG["api_base_url"], work_id)
                    if reconnect_result["success"]:
                        conn_data = reconnect_result.get("data", {})
                        online_users = conn_data.get("onlineUsers", "未知")
                        log("SUCCESS", f"重新连接成功！在线人数: {online_users}")
                        write_log(f"自动重连成功 - 在线人数: {online_users}", "SYSTEM")
                        consecutive_errors = 0
                        reconnect_fail_count = 0
                    else:
                        reconnect_fail_count += 1
                        log("ERROR", f"重新连接失败: {reconnect_result.get('message', '未知错误')} (重连失败: {reconnect_fail_count}/{max_reconnect_fails})")
                        write_log(f"自动重连失败: {reconnect_result.get('message', '未知错误')}", "SYSTEM")
                        
                        if reconnect_fail_count >= max_reconnect_fails:
                            log("ERROR", f"连续重连失败{max_reconnect_fails}次，程序将退出并由PM2自动重启...")
                            write_log(f"连续重连失败{max_reconnect_fails}次，程序退出等待PM2重启", "SYSTEM")
                            save_stats()
                            sys.exit(1)
                
                time.sleep(get_poll_interval())
                continue
            
            consecutive_errors = 0
            reconnect_fail_count = 0
            
            current_value = var_result.get("value")
            var_type = var_result.get("type", "public")
            
            if current_value is not None:
                log("DEBUG", f"[轮询#{poll_count}] 当前值: {current_value}")
            
            is_new_question, question = parse_question(str(current_value) if current_value else "")
            
            if not is_new_question:
                if (datetime.now() - last_stats_print).total_seconds() >= 300:
                    print_stats()
                    save_stats()
                    last_stats_print = datetime.now()
                time.sleep(get_poll_interval())
                continue
            
            log("INFO", f"[轮询#{poll_count}] 检测到新问题，停止轮询计时，开始处理...")
            log("INFO", f"原始值: {current_value}")
            log("INFO", f"提取问题: {question}")
            
            stats["total_questions"] += 1
            
            call_start_time = time.time()
            
            log("INFO", "正在调用AI API...")
            ai_result = call_ai_api(question)
            
            call_duration = time.time() - call_start_time
            
            if not ai_result["success"]:
                error_msg = ai_result.get("message", "未知错误")
                log("ERROR", f"AI API调用失败: {error_msg}")
                answer = f"[AI调用失败: {error_msg}]"
                stats["failed_answers"] += 1
                write_call_record(question, answer, False, call_duration)
            else:
                answer = ai_result["answer"]
                log("SUCCESS", f"AI答复: {answer}")
                stats["successful_answers"] += 1
                write_call_record(question, answer, True, call_duration)
            
            response_value = f"{CONFIG['answer_prefix']}{answer}"
            
            log("INFO", f"正在设置变量值为: {response_value[:50]}{'...' if len(response_value) > 50 else ''}")
            
            set_result = set_variable(CONFIG["api_base_url"], work_id, CONFIG["variable_name"], response_value, var_type)
            
            if set_result["success"]:
                log("SUCCESS", "变量设置成功")
                last_processed_value = current_value
            else:
                log("ERROR", f"变量设置失败: {set_result.get('message', '未知错误')}")
                stats["total_errors"] += 1
            
            log("INFO", "回复完成，立即重新开始轮询...")
            print()
            
            save_stats()
            
    except KeyboardInterrupt:
        print()
        log("INFO", "收到退出信号，正在退出...")
    except Exception as e:
        log("ERROR", f"发生未预期的错误: {str(e)}")
        stats["total_errors"] += 1
    finally:
        stats["end_time"] = datetime.now()
        if stats["online_periods"] and stats["online_periods"][-1][1] is None:
            stats["online_periods"][-1][1] = datetime.now()
        
        save_stats()
        print_stats()
        
        write_log(f"程序终止 - 运行时长: {format_uptime(calculate_uptime())}", "SYSTEM")
        
        log("INFO", "程序已退出")
        print()
        print("=" * 60)


if __name__ == "__main__":
    main()
