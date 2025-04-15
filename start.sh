#!/bin/sh

# 颜色定义
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[0;33m'
plain='\033[0m'

# 日志函数
log() {
    printf "${yellow}%s${plain}\n" "$*"
}

success() {
    printf "${green}%s${plain}\n" "$*"
}

error() {
    printf "${red}%s${plain}\n" "$*" >&2
}

# 启动所有服务
start_services() {
    python /app/app.py &
    # 等待所有后台任务完成
    wait
}

# 主函数
main() {
    # 启动所有服务
    start_services
}

# 执行主函数
main
