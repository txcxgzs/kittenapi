#!/bin/bash

#######################################################################
#                     Kitten Cloud API 一键部署脚本
#                     适用于 CentOS 9 / Debian 12 + 宝塔面板
#                     版本: 3.2.2
#                     完全交互式，无默认值
#######################################################################

# 确保 Node.js 路径在 PATH 中
export PATH=/usr/local/nodejs/bin:/usr/local/bin:$PATH
if [ -d "/www/server/nodejs" ]; then
    for dir in /www/server/nodejs/v*/bin; do
        [ -d "$dir" ] && export PATH=$dir:$PATH
    done
fi

# ==================== 颜色定义 ====================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# ==================== 全局变量 ====================
SCRIPT_VERSION="3.2.2"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR=""
LOG_FILE=""
PORT=""
DOMAIN=""
AI_BRIDGE_ENABLED=false
AI_WORK_ID=""
KITTEN_API_URL=""
AI_API_URL=""
AI_API_KEY=""
AI_MODEL=""
AI_VAR_NAME=""
AI_QUESTION_PREFIX=""
AI_ANSWER_PREFIX=""

# ==================== 日志函数 ====================

log() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    if [ -n "$LOG_FILE" ]; then
        echo -e "${timestamp} [${level}] ${message}" >> "$LOG_FILE"
    fi
    
    case $level in
        "INFO")  echo -e "${GREEN}[INFO]${NC} ${message}" ;;
        "WARN")  echo -e "${YELLOW}[WARN]${NC} ${message}" ;;
        "ERROR") echo -e "${RED}[ERROR]${NC} ${message}" ;;
        "STEP")  echo -e "${CYAN}[STEP]${NC} ${message}" ;;
        "OK")    echo -e "${GREEN}[OK]${NC} ${message}" ;;
        "ASK")   echo -e "${YELLOW}${message}${NC}" ;;
        *)       echo -e "${message}" ;;
    esac
}

print_banner() {
    clear
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║           Kitten Cloud API 一键部署脚本 v${SCRIPT_VERSION}            ║"
    echo "║                                                              ║"
    echo "║     编程猫云变量/云列表 API 服务系统 - 自动化部署工具        ║"
    echo "║                                                              ║"
    echo "║     完全交互式配置，无默认值，确保配置正确                   ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
}

print_separator() {
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
}

# ==================== 输入函数 ====================

ask_yes_no() {
    local prompt=$1
    local answer
    
    while true; do
        echo -e "${YELLOW}${prompt} (y/n):${NC} " >&2
        read -p "> " answer
        
        case $answer in
            y|Y) return 0 ;;
            n|N) return 1 ;;
            *) echo -e "${RED}请输入 y 或 n${NC}" ;;
        esac
    done
}

ask_input() {
    local prompt=$1
    local required=${2:-true}
    local answer
    
    while true; do
        echo -e "${YELLOW}${prompt}:${NC} " >&2
        read -p "> " answer
        
        # 清理输入中的特殊字符（反引号、单引号、双引号）
        answer=$(echo "$answer" | sed "s/[\`\']//g" | sed 's/"//g')
        
        if [ -z "$answer" ] && [ "$required" = true ]; then
            echo -e "${RED}此项为必填项，请输入${NC}"
        else
            echo "$answer"
            return 0
        fi
    done
}

ask_number() {
    local prompt=$1
    local default_value=$2
    local answer
    
    while true; do
        if [ -n "$default_value" ]; then
            echo -e "${YELLOW}${prompt} [默认: ${default_value}]:${NC} " >&2
        else
            echo -e "${YELLOW}${prompt}:${NC} " >&2
        fi
        read -p "> " answer
        
        if [ -z "$answer" ] && [ -n "$default_value" ]; then
            echo "$default_value"
            return 0
        fi
        
        if [[ "$answer" =~ ^[0-9]+$ ]] && [ "$answer" -gt 0 ]; then
            echo "$answer"
            return 0
        else
            echo -e "${RED}请输入有效的正整数${NC}"
        fi
    done
}

# ==================== 检测函数 ====================

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log "ERROR" "请使用 root 用户运行此脚本"
        log "INFO" "可以使用: sudo bash $0"
        exit 1
    fi
    log "OK" "Root 权限检测通过"
}

check_os() {
    log "STEP" "检测操作系统..."
    
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
        log "INFO" "操作系统: $PRETTY_NAME"
    else
        log "ERROR" "无法检测操作系统"
        exit 1
    fi
}

check_baota() {
    if [ -d "/www/server/panel" ]; then
        BT_INSTALLED=true
        log "OK" "检测到宝塔面板"
    else
        BT_INSTALLED=false
        log "INFO" "未检测到宝塔面板"
    fi
}

# ==================== 项目检测函数 ====================

find_project_dir() {
    log "STEP" "检测项目目录..."
    
    local script_parent="$(dirname "$SCRIPT_DIR")"
    
    if [ -f "$script_parent/server/package.json" ]; then
        PROJECT_DIR="$script_parent"
        log "OK" "检测到项目目录: $PROJECT_DIR"
        return 0
    fi
    
    log "WARN" "未自动检测到项目目录"
    echo ""
    log "ASK" "请输入项目目录的完整路径"
    log "INFO" "示例: /www/wwwroot/kitten-cloud-api"
    
    while true; do
        PROJECT_DIR=$(ask_input "项目目录路径" true)
        
        if [ -f "$PROJECT_DIR/server/package.json" ]; then
            break
        else
            log "ERROR" "无效的项目目录，请确保目录下存在 server/package.json"
        fi
    done
    
    LOG_FILE="$PROJECT_DIR/deploy.log"
    log "OK" "项目目录确认: $PROJECT_DIR"
}

# ==================== 环境安装函数 ====================

install_dependencies() {
    log "STEP" "安装系统依赖包..."
    
    yum install -y curl wget git vim tar gzip unzip \
        gcc gcc-c++ make automake autoconf libtool \
        openssl-devel bzip2-devel libffi-devel zlib-devel \
        sqlite-devel net-tools > /dev/null 2>&1
    
    log "OK" "系统依赖包安装完成"
}

install_nodejs() {
    log "STEP" "检测 Node.js 环境..."
    
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
        log "INFO" "已安装 Node.js 版本: $(node -v)"
        
        if [ "$NODE_VERSION" -ge 18 ]; then
            log "OK" "Node.js 版本满足要求"
            return 0
        else
            log "WARN" "Node.js 版本过低，需要升级到 18+"
        fi
    fi
    
    log "INFO" "正在安装 Node.js 18..."
    
    # 优先使用宝塔面板已安装的 Node.js
    if [ "$BT_INSTALLED" = true ] && [ -d "/www/server/nodejs" ]; then
        BT_NODE_PATH=$(ls -d /www/server/nodejs/v18*/bin 2>/dev/null | head -1)
        if [ -n "$BT_NODE_PATH" ]; then
            export PATH=$BT_NODE_PATH:$PATH
            log "OK" "使用宝塔 Node.js 环境"
            return 0
        fi
    fi
    
    # 使用国内镜像安装 Node.js（淘宝镜像）
    NODE_VERSION="18.20.2"
    NODE_DIST="node-v${NODE_VERSION}-linux-x64.tar.xz"
    NODE_URL="https://npmmirror.com/mirrors/node/v${NODE_VERSION}/${NODE_DIST}"
    NODE_INSTALL_DIR="/usr/local/nodejs"
    
    log "INFO" "从国内镜像下载 Node.js ${NODE_VERSION}..."
    
    # 创建临时目录
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    # 下载 Node.js
    if curl -fsSL "$NODE_URL" -o "$NODE_DIST"; then
        # 解压并安装
        tar -xf "$NODE_DIST"
        NODE_DIR="node-v${NODE_VERSION}-linux-x64"
        
        # 移动到安装目录
        rm -rf "$NODE_INSTALL_DIR"
        mv "$NODE_DIR" "$NODE_INSTALL_DIR"
        
        # 创建软链接
        ln -sf "$NODE_INSTALL_DIR/bin/node" /usr/local/bin/node
        ln -sf "$NODE_INSTALL_DIR/bin/npm" /usr/local/bin/npm
        ln -sf "$NODE_INSTALL_DIR/bin/npx" /usr/local/bin/npx
        
        # 配置 npm 使用国内镜像
        npm config set registry https://registry.npmmirror.com
        
        log "OK" "Node.js 安装成功: $(node -v)"
    else
        log "ERROR" "Node.js 下载失败，请手动安装"
        log "INFO" "方法1: 在宝塔面板 → 软件商店 → 运行环境 → Node.js 版本管理器 中安装"
        log "INFO" "方法2: 手动下载 https://npmmirror.com/mirrors/node/"
        exit 1
    fi
    
    # 清理临时目录
    cd /
    rm -rf "$TEMP_DIR"
    
    if ! command -v node &> /dev/null; then
        log "ERROR" "Node.js 安装失败"
        exit 1
    fi
}

install_pm2() {
    log "STEP" "检测 PM2..."
    
    # 确保 Node.js bin 目录在 PATH 中
    if [ -d "/usr/local/nodejs/bin" ]; then
        export PATH=/usr/local/nodejs/bin:$PATH
    fi
    
    # 检查宝塔 Node.js 路径
    if [ -d "/www/server/nodejs" ]; then
        BT_NODE_BIN=$(ls -d /www/server/nodejs/v*/bin 2>/dev/null | head -1)
        if [ -n "$BT_NODE_BIN" ]; then
            export PATH=$BT_NODE_BIN:$PATH
        fi
    fi
    
    if command -v pm2 &> /dev/null; then
        log "OK" "PM2 已安装: $(pm2 -v)"
        return 0
    fi
    
    log "INFO" "正在安装 PM2..."
    npm install -g pm2 --registry=https://registry.npmmirror.com
    
    # 再次检查
    if command -v pm2 &> /dev/null; then
        log "OK" "PM2 安装成功: $(pm2 -v)"
    else
        # 尝试从 Node.js 目录直接调用
        if [ -f "/usr/local/nodejs/bin/pm2" ]; then
            log "OK" "PM2 安装成功"
        else
            log "ERROR" "PM2 安装失败"
            log "INFO" "请手动安装: npm install -g pm2"
            exit 1
        fi
    fi
}

install_python() {
    log "STEP" "检测 Python 环境..."
    
    if command -v python3 &> /dev/null; then
        log "OK" "Python 已安装: $(python3 --version)"
        
        if python3 -c "import requests" 2>/dev/null; then
            log "OK" "requests 库已安装"
        else
            log "INFO" "安装 requests 库..."
            pip3 install requests -i https://pypi.tuna.tsinghua.edu.cn/simple > /dev/null 2>&1
        fi
        return 0
    fi
    
    log "INFO" "正在安装 Python 3..."
    yum install -y python3 python3-pip > /dev/null 2>&1
    pip3 install requests -i https://pypi.tuna.tsinghua.edu.cn/simple > /dev/null 2>&1
    
    if command -v python3 &> /dev/null; then
        log "OK" "Python 3 安装成功"
    else
        log "WARN" "Python 3 安装失败，AI桥接功能将不可用"
    fi
}

# ==================== 配置函数 ====================

configure_service() {
    log "STEP" "配置服务参数..."
    
    print_separator
    echo -e "${CYAN}请配置服务参数:${NC}"
    print_separator
    
    # 端口配置
    echo ""
    log "INFO" "服务端口说明: API 服务监听的端口号"
    PORT=$(ask_number "请输入服务端口" 9178)
    log "INFO" "服务端口: $PORT"
    
    # 管理员密码配置
    echo ""
    echo -e "${CYAN}管理后台密码:${NC}"
    echo -e "  ${YELLOW}重要:${NC} 管理后台需要密码才能登录"
    echo ""
    local admin_password=$(ask_input "请输入管理后台密码 (至少6位)" true)
    while [ ${#admin_password} -lt 6 ]; do
        echo -e "${RED}密码至少需要6位${NC}"
        admin_password=$(ask_input "请输入管理后台密码 (至少6位)" true)
    done
    
    # Cookie 配置
    echo ""
    echo -e "${CYAN}获取编程猫 Cookie 方法:${NC}"
    echo -e "  1. 登录 https://shequ.codemao.cn"
    echo -e "  2. 按 F12 打开开发者工具"
    echo -e "  3. Application → Cookies → shequ.codemao.cn"
    echo -e "  4. 复制 ${YELLOW}authorization${NC} 的值"
    echo ""
    
    local auth_value=$(ask_input "请输入编程猫 Cookie (authorization 值)" true)
    
    # API Key 配置
    echo ""
    local enable_api_key
    if ask_yes_no "是否启用 API Key 认证?"; then
        local api_key=$(ask_input "请输入 API Key (至少8位)" true)
        while [ ${#api_key} -lt 8 ]; do
            echo -e "${RED}API Key 至少需要8位${NC}"
            api_key=$(ask_input "请输入 API Key (至少8位)" true)
        done
    else
        api_key=""
    fi
    
    # 日志保留天数
    echo ""
    local log_days=$(ask_number "日志保留天数" 30)
    
    # 写入配置文件
    local env_file="$PROJECT_DIR/server/.env"
    
    if [ -f "$env_file" ]; then
        cp "$env_file" "$env_file.bak.$(date +%Y%m%d%H%M%S)"
        log "INFO" "已备份现有配置文件"
    fi
    
    cat > "$env_file" << EOF
# ==================== Kitten Cloud API 配置文件 ====================
# 生成时间: $(date '+%Y-%m-%d %H:%M:%S')

# 服务配置
PORT=$PORT
HOST=0.0.0.0

# 编程猫身份认证 (必填)
CODEMAO_AUTHORIZATION=$auth_value

# API 密钥 (可选)
API_KEY=$api_key

# 日志保留天数
LOG_RETENTION_DAYS=$log_days

# 数据库路径
DATABASE_PATH=./data/kitten-cloud.db

# 管理员密码 (用于后台登录)
ADMIN_PASSWORD=$admin_password
EOF
    
    chmod 600 "$env_file"
    log "OK" "配置文件已创建: $env_file"
}

configure_ai_bridge() {
    print_separator
    echo -e "${CYAN}AI 桥接程序配置${NC}"
    print_separator
    
    echo -e "${YELLOW}AI 桥接程序功能:${NC}"
    echo -e "  - 轮询云变量，检测玩家问题"
    echo -e "  - 调用 AI API 生成回复"
    echo -e "  - 将回复写入云变量"
    echo ""
    
    if ! ask_yes_no "是否配置并启动 AI 桥接程序?"; then
        log "INFO" "跳过 AI 桥接配置"
        AI_BRIDGE_ENABLED=false
        return 0
    fi
    
    AI_BRIDGE_ENABLED=true
    
    echo ""
    echo -e "${CYAN}请配置 AI 桥接参数:${NC}"
    print_separator
    
    # 作品ID
    echo ""
    log "INFO" "作品ID: 编程猫作品的数字ID"
    AI_WORK_ID=$(ask_number "请输入要连接的作品ID")
    
    # Kitten Cloud API 服务地址
    echo ""
    echo -e "${CYAN}Kitten Cloud API 服务地址说明:${NC}"
    echo -e "  - 本地部署: http://localhost:${PORT}/api"
    echo -e "  - 域名访问: http://你的域名/api"
    echo ""
    KITTEN_API_URL=$(ask_input "请输入 Kitten Cloud API 服务地址" true)
    
    # AI API 配置
    echo ""
    echo -e "${CYAN}AI API 配置说明:${NC}"
    echo -e "  支持 OpenAI 兼容的 API 接口"
    echo -e "  例如: https://api.openai.com/v1/chat/completions"
    echo ""
    AI_API_URL=$(ask_input "请输入 AI API 地址" true)
    AI_API_KEY=$(ask_input "请输入 AI API Key" true)
    AI_MODEL=$(ask_input "请输入 AI 模型名称" true)
    
    # 云变量配置
    echo ""
    echo -e "${CYAN}云变量配置说明:${NC}"
    echo -e "  - 云变量名: 用于 AI 交互的云变量名称"
    echo -e "  - 问题前缀: 玩家发送问题时需要加的前缀"
    echo -e "  - 答案前缀: AI 回复时会加的前缀"
    echo ""
    AI_VAR_NAME=$(ask_input "请输入云变量名" true)
    AI_QUESTION_PREFIX=$(ask_input "请输入问题前缀" true)
    AI_ANSWER_PREFIX=$(ask_input "请输入答案前缀" true)
    
    # 创建配置文件
    local config_dir="$PROJECT_DIR/ai-bridge"
    mkdir -p "$config_dir"
    
    # 创建 Python 配置文件
    cat > "$config_dir/config.py" << EOF
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 桥接程序配置文件
生成时间: $(date '+%Y-%m-%d %H:%M:%S')
"""

CONFIG = {
    "api_base_url": "$KITTEN_API_URL",
    "ai_api_url": "$AI_API_URL",
    "ai_api_key": "$AI_API_KEY",
    "ai_model": "$AI_MODEL",
    "question_prefix": "$AI_QUESTION_PREFIX",
    "answer_prefix": "$AI_ANSWER_PREFIX",
    "variable_name": "$AI_VAR_NAME",
    "request_timeout": 60,
    "max_retries": 5,
    "log_dir": "$config_dir/logs"
}
EOF
    
    # 创建 PM2 配置文件
    cat > "$config_dir/ecosystem.config.js" << EOF
module.exports = {
  apps: [{
    name: 'kitten-ai-bridge',
    script: '$PROJECT_DIR/kitten_ai_bridge.py',
    interpreter: 'python3',
    args: '-w $AI_WORK_ID -c $config_dir/config.py',
    cwd: '$PROJECT_DIR',
    autorestart: true,
    restart_delay: 3000,
    max_restarts: 1000,
    watch: false,
    cron_restart: '*/5 * * * *',
    env: {
      NODE_ENV: 'production'
    },
    error_file: '$config_dir/logs/error.log',
    out_file: '$config_dir/logs/out.log'
  }]
}
EOF
    
    # 创建日志目录
    mkdir -p "$config_dir/logs"
    
    log "OK" "AI 桥接配置完成"
    echo ""
    echo -e "${CYAN}AI 桥接配置摘要:${NC}"
    echo -e "  作品ID:     ${YELLOW}$AI_WORK_ID${NC}"
    echo -e "  API地址:    ${YELLOW}$KITTEN_API_URL${NC}"
    echo -e "  AI API:     ${YELLOW}$AI_API_URL${NC}"
    echo -e "  AI模型:     ${YELLOW}$AI_MODEL${NC}"
    echo -e "  云变量:     ${YELLOW}$AI_VAR_NAME${NC}"
    echo -e "  问题前缀:   ${YELLOW}$AI_QUESTION_PREFIX${NC}"
    echo -e "  答案前缀:   ${YELLOW}$AI_ANSWER_PREFIX${NC}"
    echo -e "  配置文件:   ${YELLOW}$config_dir/config.py${NC}"
}

configure_nginx() {
    if [ "$BT_INSTALLED" != true ]; then
        log "INFO" "未检测到宝塔面板，跳过 Nginx 配置"
        return 0
    fi
    
    print_separator
    echo -e "${CYAN}Nginx 反向代理配置${NC}"
    print_separator
    
    if ! ask_yes_no "是否配置 Nginx 反向代理?"; then
        log "INFO" "跳过 Nginx 配置"
        return 0
    fi
    
    echo ""
    log "INFO" "请输入域名，不要带 http:// 或 https://"
    log "INFO" "示例: kittenapi.example.com"
    DOMAIN=$(ask_input "请输入域名" true)
    
    if [ -z "$DOMAIN" ]; then
        log "WARN" "未输入域名，跳过 Nginx 配置"
        return 0
    fi
    
    local nginx_conf="/www/server/panel/vhost/nginx/$DOMAIN.conf"
    
    # 备份现有配置
    if [ -f "$nginx_conf" ]; then
        cp "$nginx_conf" "$nginx_conf.bak.$(date +%Y%m%d%H%M%S)"
        log "INFO" "已备份现有 Nginx 配置"
    fi
    
    cat > "$nginx_conf" << EOF
# ==================== Kitten Cloud API Nginx 配置 ====================
# 生成时间: $(date '+%Y-%m-%d %H:%M:%S')
# 服务端口: $PORT

server {
    listen 80;
    server_name $DOMAIN;
    
    access_log /www/wwwlogs/$DOMAIN.log;
    error_log /www/wwwlogs/$DOMAIN.error.log;
    
    client_max_body_size 10m;
    
    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location /health {
        proxy_pass http://127.0.0.1:$PORT/health;
        access_log off;
    }
    
    location /api {
        proxy_pass http://127.0.0.1:$PORT/api;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF
    
    if nginx -t 2>/dev/null; then
        nginx -s reload
        log "OK" "Nginx 配置完成: $nginx_conf"
    else
        log "ERROR" "Nginx 配置测试失败"
        return 1
    fi
    
    # 开放防火墙
    if command -v firewall-cmd &> /dev/null; then
        firewall-cmd --permanent --add-service=http > /dev/null 2>&1
        firewall-cmd --permanent --add-service=https > /dev/null 2>&1
        firewall-cmd --reload > /dev/null 2>&1
        log "INFO" "已开放防火墙 HTTP/HTTPS 端口"
    fi
    
    echo ""
    if ask_yes_no "是否配置 SSL 证书?"; then
        log "INFO" "请在宝塔面板中配置 SSL 证书:"
        log "INFO" "网站 → $DOMAIN → SSL → Let's Encrypt → 申请证书"
    fi
}

# ==================== 项目安装函数 ====================

install_project() {
    log "STEP" "安装项目依赖..."
    
    # 先构建 Kitten-Cloud-Function 本地依赖
    if [ -d "$PROJECT_DIR/Kitten-Cloud-Function" ]; then
        log "INFO" "构建本地依赖 Kitten-Cloud-Function..."
        cd "$PROJECT_DIR/Kitten-Cloud-Function"
        
        if [ ! -d "node_modules" ]; then
            npm install --registry=https://registry.npmmirror.com
        fi
        
        if [ ! -d "dist" ]; then
            log "INFO" "编译 Kitten-Cloud-Function..."
            npm run build:package
            log "OK" "Kitten-Cloud-Function 构建完成"
        fi
    fi
    
    cd "$PROJECT_DIR/server"
    
    # 检查是否需要重新安装
    if [ -d "node_modules" ]; then
        if ask_yes_no "检测到已有依赖，是否重新安装?"; then
            rm -rf node_modules package-lock.json
        else
            log "INFO" "跳过依赖安装"
        fi
    fi
    
    if [ ! -d "node_modules" ]; then
        npm config set registry https://registry.npmmirror.com
        log "INFO" "正在安装依赖，请稍候..."
        if npm install; then
            log "OK" "后端依赖安装完成"
        else
            log "ERROR" "后端依赖安装失败"
            exit 1
        fi
    fi
    
    # 编译
    log "STEP" "编译后端项目..."
    if npm run build; then
        log "OK" "后端项目编译完成"
    else
        log "ERROR" "后端项目编译失败"
        exit 1
    fi
    
    # 创建数据目录
    mkdir -p "$PROJECT_DIR/server/data"
    mkdir -p "$PROJECT_DIR/server/logs"
    
    # 前端构建
    if [ -d "$PROJECT_DIR/web" ]; then
        if [ -d "$PROJECT_DIR/web/dist" ]; then
            if ask_yes_no "前端已构建，是否重新构建?"; then
                cd "$PROJECT_DIR/web"
                [ ! -d "node_modules" ] && npm install --registry=https://registry.npmmirror.com
                if npm run build; then
                    log "OK" "前端项目构建完成"
                else
                    log "WARN" "前端项目构建失败"
                fi
            fi
        else
            if ask_yes_no "是否构建前端项目?"; then
                cd "$PROJECT_DIR/web"
                npm install --registry=https://registry.npmmirror.com
                if npm run build; then
                    log "OK" "前端项目构建完成"
                else
                    log "WARN" "前端项目构建失败"
                fi
            fi
        fi
    fi
}

# ==================== 服务启动函数 ====================

start_services() {
    log "STEP" "启动服务..."
    
    # 停止旧服务
    pm2 delete kitten-cloud-api 2>/dev/null
    pm2 delete kitten-ai-bridge 2>/dev/null
    
    # 启动后端
    cd "$PROJECT_DIR/server"
    pm2 start dist/app.js \
        --name "kitten-cloud-api" \
        --cwd "$PROJECT_DIR/server" \
        --time
    
    sleep 3
    
    if pm2 list | grep -q "kitten-cloud-api.*online"; then
        log "OK" "后端服务启动成功"
    else
        log "ERROR" "后端服务启动失败"
        pm2 logs kitten-cloud-api --lines 20
        exit 1
    fi
    
    # 启动 AI 桥接
    if [ "$AI_BRIDGE_ENABLED" = true ]; then
        log "INFO" "启动 AI 桥接服务..."
        pm2 start "$PROJECT_DIR/ai-bridge/ecosystem.config.js"
        sleep 2
        
        if pm2 list | grep -q "kitten-ai-bridge.*online"; then
            log "OK" "AI 桥接服务启动成功"
        else
            log "WARN" "AI 桥接服务启动失败，请检查配置"
            pm2 logs kitten-ai-bridge --lines 10
        fi
    fi
    
    # 保存 PM2 配置
    pm2 save
    pm2 startup | tail -n 1 | bash 2>/dev/null
    
    log "OK" "PM2 配置已保存"
}

# ==================== 验证函数 ====================

verify_deployment() {
    log "STEP" "验证部署..."
    
    sleep 3
    
    # 检查服务状态
    if pm2 list | grep -q "kitten-cloud-api.*online"; then
        log "OK" "后端服务运行正常"
    else
        log "ERROR" "后端服务未运行"
    fi
    
    # 检查端口
    if netstat -tlnp 2>/dev/null | grep -q ":$PORT "; then
        log "OK" "端口 $PORT 监听正常"
    else
        log "WARN" "端口 $PORT 未监听"
    fi
    
    # 健康检查
    local health=$(curl -s "http://localhost:$PORT/health" 2>/dev/null)
    if [ -n "$health" ]; then
        log "OK" "健康检查接口正常"
        echo -e "  ${CYAN}$health${NC}"
    else
        log "WARN" "健康检查接口无响应"
    fi
}

test_connectivity() {
    log "STEP" "连通性测试..."
    
    local test_passed=true
    
    # 1. 本地健康接口
    echo ""
    log "INFO" "1. 测试本地健康接口..."
    local local_health=$(curl -s -w "\n%{http_code}" "http://localhost:$PORT/health" 2>/dev/null)
    local local_status=$(echo "$local_health" | tail -1)
    
    if [ "$local_status" = "200" ]; then
        log "OK" "本地健康接口正常 (HTTP $local_status)"
    else
        log "ERROR" "本地健康接口异常 (HTTP $local_status)"
        test_passed=false
    fi
    
    # 2. API 接口
    echo ""
    log "INFO" "2. 测试 API 接口..."
    local api_test=$(curl -s -w "\n%{http_code}" "http://localhost:$PORT/api/connections" 2>/dev/null)
    local api_status=$(echo "$api_test" | tail -1)
    
    if [ "$api_status" = "200" ]; then
        log "OK" "API 接口正常"
    else
        log "WARN" "API 接口异常 (HTTP $api_status)"
    fi
    
    # 3. 域名访问
    if [ -n "$DOMAIN" ]; then
        echo ""
        log "INFO" "3. 测试域名访问..."
        local domain_health=$(curl -s -w "\n%{http_code}" "http://$DOMAIN/health" 2>/dev/null)
        local domain_status=$(echo "$domain_health" | tail -1)
        
        if [ "$domain_status" = "200" ]; then
            log "OK" "域名访问正常: http://$DOMAIN"
        else
            log "WARN" "域名访问异常 (HTTP $domain_status)"
            log "INFO" "可能需要检查 DNS 解析或防火墙设置"
        fi
    fi
    
    # 4. 编程猫 API
    echo ""
    log "INFO" "4. 测试编程猫 API 连通性..."
    if curl -s --connect-timeout 5 "https://api.codemao.cn" > /dev/null 2>&1; then
        log "OK" "编程猫 API 可访问"
    else
        log "WARN" "无法访问编程猫 API"
    fi
    
    # 5. 用户认证
    echo ""
    log "INFO" "5. 测试用户认证..."
    local user_info=$(curl -s "http://localhost:$PORT/api/user/info" 2>/dev/null)
    
    if echo "$user_info" | grep -q '"success":true'; then
        log "OK" "用户认证成功"
        local user_id=$(echo "$user_info" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
        local user_nick=$(echo "$user_info" | grep -o '"nickname":"[^"]*"' | head -1 | cut -d'"' -f4)
        echo -e "  ${CYAN}用户ID: $user_id, 昵称: $user_nick${NC}"
    else
        log "WARN" "用户认证失败，请检查 Cookie 配置"
    fi
    
    # 6. AI 桥接测试
    if [ "$AI_BRIDGE_ENABLED" = true ]; then
        echo ""
        log "INFO" "6. 测试 AI 桥接服务..."
        if pm2 list | grep -q "kitten-ai-bridge.*online"; then
            log "OK" "AI 桥接服务运行正常"
        else
            log "WARN" "AI 桥接服务未运行"
        fi
    fi
    
    echo ""
    if [ "$test_passed" = true ]; then
        log "OK" "连通性测试完成"
    else
        log "WARN" "部分测试未通过，请检查日志"
    fi
}

# ==================== 完成提示 ====================

print_completion() {
    print_separator
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    部署完成！                                ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    
    local server_ip=$(curl -s --connect-timeout 3 "https://myip.ipip.net/ip" 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    if [ -z "$server_ip" ]; then
        server_ip=$(curl -s --connect-timeout 3 "http://ip.3322.net" 2>/dev/null)
    fi
    if [ -z "$server_ip" ]; then
        server_ip="服务器IP"
    fi
    
    echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}服务信息:${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "  项目目录: ${YELLOW}$PROJECT_DIR${NC}"
    echo -e "  服务端口: ${YELLOW}$PORT${NC}"
    echo ""
    
    echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}访问地址:${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "  本地访问: ${YELLOW}http://localhost:$PORT${NC}"
    echo -e "  IP访问:   ${YELLOW}http://$server_ip:$PORT${NC}"
    
    if [ -n "$DOMAIN" ]; then
        echo -e "  域名访问: ${GREEN}http://$DOMAIN${NC}"
        echo ""
        echo -e "  管理后台: ${GREEN}http://$DOMAIN${NC}"
        echo -e "  API 文档: ${GREEN}http://$DOMAIN/api${NC}"
    else
        echo ""
        echo -e "  管理后台: ${YELLOW}http://$server_ip:$PORT${NC}"
        echo -e "  API 文档: ${YELLOW}http://$server_ip:$PORT/api${NC}"
    fi
    echo ""
    
    if [ "$AI_BRIDGE_ENABLED" = true ]; then
        echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
        echo -e "${CYAN}AI 桥接服务:${NC}"
        echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
        echo -e "  作品ID:   ${YELLOW}$AI_WORK_ID${NC}"
        echo -e "  云变量:   ${YELLOW}$AI_VAR_NAME${NC}"
        echo -e "  AI模型:   ${YELLOW}$AI_MODEL${NC}"
        echo -e "  配置目录: ${YELLOW}$PROJECT_DIR/ai-bridge${NC}"
        echo ""
    fi
    
    echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}常用命令:${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "  查看状态: ${YELLOW}pm2 status${NC}"
    echo -e "  查看日志: ${YELLOW}pm2 logs kitten-cloud-api${NC}"
    echo -e "  重启服务: ${YELLOW}pm2 restart kitten-cloud-api${NC}"
    echo -e "  停止服务: ${YELLOW}pm2 stop kitten-cloud-api${NC}"
    
    if [ "$AI_BRIDGE_ENABLED" = true ]; then
        echo -e "  AI日志:   ${YELLOW}pm2 logs kitten-ai-bridge${NC}"
    fi
    echo ""
    
    echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}配置文件:${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "  环境配置: ${YELLOW}$PROJECT_DIR/server/.env${NC}"
    echo -e "  部署日志: ${YELLOW}$LOG_FILE${NC}"
    
    if [ -n "$DOMAIN" ]; then
        echo -e "  Nginx配置: ${YELLOW}/www/server/panel/vhost/nginx/$DOMAIN.conf${NC}"
    fi
    
    if [ "$AI_BRIDGE_ENABLED" = true ]; then
        echo -e "  AI配置:   ${YELLOW}$PROJECT_DIR/ai-bridge/config.py${NC}"
    fi
    echo ""
    
    print_separator
    echo -e "${GREEN}感谢使用 Kitten Cloud API！${NC}"
    echo ""
}

# ==================== 主函数 ====================

main() {
    print_banner
    
    # 环境检测
    print_separator
    echo -e "${CYAN}[阶段 1/8] 环境检测${NC}"
    print_separator
    check_root
    check_os
    check_baota
    
    # 项目检测
    print_separator
    echo -e "${CYAN}[阶段 2/8] 项目检测${NC}"
    print_separator
    find_project_dir
    
    # 初始化日志
    LOG_FILE="$PROJECT_DIR/deploy.log"
    echo "=== 部署开始: $(date '+%Y-%m-%d %H:%M:%S') ===" > "$LOG_FILE"
    
    # 安装依赖
    print_separator
    echo -e "${CYAN}[阶段 3/8] 安装系统依赖${NC}"
    print_separator
    install_dependencies
    install_nodejs
    install_pm2
    install_python
    
    # 项目安装
    print_separator
    echo -e "${CYAN}[阶段 4/8] 项目安装${NC}"
    print_separator
    install_project
    
    # 配置服务
    print_separator
    echo -e "${CYAN}[阶段 5/8] 配置服务${NC}"
    print_separator
    configure_service
    
    # 配置 AI 桥接
    print_separator
    echo -e "${CYAN}[阶段 6/8] AI 桥接配置${NC}"
    print_separator
    configure_ai_bridge
    
    # 配置 Nginx
    print_separator
    echo -e "${CYAN}[阶段 7/8] 网络配置${NC}"
    print_separator
    configure_nginx
    
    # 启动服务
    print_separator
    echo -e "${CYAN}[阶段 8/8] 启动服务${NC}"
    print_separator
    start_services
    
    # 验证
    print_separator
    echo -e "${CYAN}验证部署${NC}"
    print_separator
    verify_deployment
    
    # 连通性测试
    print_separator
    echo -e "${CYAN}连通性测试${NC}"
    print_separator
    test_connectivity
    
    # 完成
    print_completion
    
    echo "=== 部署完成: $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$LOG_FILE"
}

# ==================== 入口 ====================

case "${1:-}" in
    --help|-h)
        echo "用法: $0 [选项]"
        echo ""
        echo "选项:"
        echo "  --help, -h     显示帮助信息"
        echo "  --version, -v  显示版本信息"
        echo "  --uninstall    卸载服务"
        echo ""
        echo "不带参数运行将执行完整部署流程（完全交互式）"
        ;;
    --version|-v)
        echo "Kitten Cloud API 部署脚本 v${SCRIPT_VERSION}"
        ;;
    --uninstall)
        echo "正在卸载..."
        pm2 delete kitten-cloud-api 2>/dev/null
        pm2 delete kitten-ai-bridge 2>/dev/null
        pm2 save
        echo "卸载完成"
        ;;
    *)
        main
        ;;
esac
