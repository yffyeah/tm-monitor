# 温湿度监控系统 - 阿里云部署指南

## 部署文件清单

需要上传到服务器的文件：
```
tm-monitor/
├── web_app.py              # Flask Web应用
├── dt11_logger.py          # 数据采集脚本（可选，如果传感器也在服务器上）
├── requirements.txt        # Python依赖包
├── start.sh               # 启动脚本
└── templates/
    └── index.html         # 前端页面
```

## 部署步骤

### 1. 上传文件到服务器

使用SCP或FTP工具上传文件到服务器：
```bash
# 使用SCP上传（本地执行）
scp -r tm-monitor/ root@your-server-ip:/root/
```

### 2. 登录服务器并安装依赖

```bash
# SSH登录服务器
ssh root@your-server-ip

# 进入项目目录
cd /root/tm-monitor

# 安装Python依赖
pip3 install -r requirements.txt

# 如果pip3不存在，先安装
# Ubuntu/Debian:
# apt-get update && apt-get install -y python3-pip
# CentOS:
# yum install -y python3-pip
```

### 3. 启动Web应用

#### 方式一：直接启动（测试用）
```bash
python3 web_app.py
```

#### 方式二：使用启动脚本
```bash
chmod +x start.sh
./start.sh
```

#### 方式三：使用nohup后台运行（推荐）
```bash
nohup python3 web_app.py > app.log 2>&1 &
```

#### 方式四：使用systemd服务（生产环境推荐）

创建服务文件 `/etc/systemd/system/tm-monitor.service`:
```ini
[Unit]
Description=Temperature and Humidity Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/tm-monitor
ExecStart=/usr/bin/python3 /root/tm-monitor/web_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
# 重载systemd配置
systemctl daemon-reload

# 启动服务
systemctl start tm-monitor

# 设置开机自启
systemctl enable tm-monitor

# 查看服务状态
systemctl status tm-monitor

# 查看日志
journalctl -u tm-monitor -f
```

### 4. 配置防火墙

开放5002端口：
```bash
# CentOS/RHEL (firewalld)
firewall-cmd --permanent --add-port=5002/tcp
firewall-cmd --reload

# Ubuntu (ufw)
ufw allow 5002/tcp

# 阿里云安全组
# 需要在阿里云控制台 -> ECS实例 -> 安全组 -> 配置规则
# 添加入方向规则：端口5002，授权对象0.0.0.0/0
```

### 5. 访问应用

在浏览器中访问：
```
http://your-server-ip:5002
```

## 可选：使用Nginx反向代理（推荐）

安装Nginx：
```bash
# Ubuntu/Debian
apt-get install -y nginx

# CentOS
yum install -y nginx
```

配置Nginx `/etc/nginx/conf.d/tm-monitor.conf`:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名或IP

    location / {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

重启Nginx：
```bash
# 测试配置
nginx -t

# 重启Nginx
systemctl restart nginx

# 设置开机自启
systemctl enable nginx
```

现在可以通过80端口访问：
```
http://your-server-ip
```

## 可选：配置HTTPS（使用Let's Encrypt）

安装certbot：
```bash
# Ubuntu/Debian
apt-get install -y certbot python3-certbot-nginx

# CentOS
yum install -y certbot python3-certbot-nginx
```

获取证书：
```bash
certbot --nginx -d your-domain.com
```

## 常用命令

```bash
# 查看进程
ps aux | grep web_app.py

# 停止进程
pkill -f web_app.py

# 查看端口占用
netstat -tlnp | grep 5002

# 查看日志
tail -f app.log

# 重启服务（systemd）
systemctl restart tm-monitor
```

## 注意事项

1. **传感器连接**：如果Arduino传感器也连接到服务器，需要配置串口权限
   ```bash
   # 将用户添加到dialout组
   usermod -a -G dialout root
   ```

2. **日志目录**：确保logs目录有写权限
   ```bash
   chmod -R 755 logs/
   ```

3. **Python版本**：确保Python版本≥3.7
   ```bash
   python3 --version
   ```

4. **生产环境**：建议修改web_app.py中的debug模式为False
   ```python
   app.run(debug=False, host='0.0.0.0', port=5002)
   ```

## 故障排查

1. **端口被占用**
   ```bash
   # 查找占用端口的进程
   lsof -i :5002
   # 或
   netstat -tlnp | grep 5002
   ```

2. **权限问题**
   ```bash
   # 检查文件权限
   ls -la

   # 修改权限
   chmod +x start.sh
   ```

3. **依赖问题**
   ```bash
   # 重新安装依赖
   pip3 install -r requirements.txt --force-reinstall
   ```

4. **查看错误日志**
   ```bash
   # systemd服务日志
   journalctl -u tm-monitor -n 50

   # 应用日志
   tail -f app.log
   ```