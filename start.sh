#!/bin/bash

# 安装依赖
pip3 install -r requirements.txt

# 创建日志目录
mkdir -p logs

# 启动Web应用
python3 web_app.py