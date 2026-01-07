# 项目说明
根据https://metrodb.org/index/shanghai.html 发布的数据，定时抓取客流量数据，形成 csv文件。
当时准备从上海地铁的微博抓数据，所以 py 名字是 weibo，其实和微博没关系

现在的定时流程：`weibo.py` 抓取数据 → 写入 `shanghai_metro_data.csv`（按日期去重） → 触发 `feishu.py` 把 CSV 内容上传到飞书多维表格（昨日客流量映射到字段「人次」）。

2026-01-06 追加
研究了飞书文档接口，在服务器上安装了飞书文档 sdk，把 csv 文件 内容上传到飞书文档。
增加了 feishu.py


# Ubuntu 云主机部署说明

本目录包含用于在 Ubuntu/Linux 云主机上部署的所有文件。

## 文件清单

- `weibo.py` - 主程序脚本
- `requirements.txt` - Python 依赖包列表
- `install_ubuntu.sh` - 安装脚本（自动设置 cron 定时任务）
- `uninstall_ubuntu.sh` - 卸载脚本
- `README.md` - 本说明文档

## 系统要求

- **Python 3.6+**：大多数 Ubuntu 系统默认已安装
- **pip3**：Python 包管理器（如果没有，安装脚本会尝试自动安装）

## 快速部署步骤

### 1. 检查系统环境（可选）

登录服务器检查 Python3 是否已安装：

```bash
ssh user@your-server
python3 --version
pip3 --version
```

如果未安装 Python3，需要先安装：

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3 python3-pip

# CentOS/RHEL
sudo yum install -y python3 python3-pip
```

### 2. 上传文件到服务器

将整个 `ubuntu_deploy` 目录上传到服务器：

```bash
# 使用 scp
scp -r ubuntu_deploy user@your-server:/path/to/destination/

# 或使用 rsync
rsync -av ubuntu_deploy/ user@your-server:/path/to/destination/ubuntu_deploy/
```

### 3. 登录服务器并安装

```bash
# SSH 登录服务器
ssh user@your-server

# 进入部署目录
cd /path/to/destination/ubuntu_deploy

# 给脚本添加执行权限
chmod +x install_ubuntu.sh uninstall_ubuntu.sh

# 运行安装脚本（会自动安装依赖包）
./install_ubuntu.sh
```

**注意**：`install_ubuntu.sh` 脚本会：
- ✅ 自动检查 Python3 和 pip3
- ✅ 自动安装 Python 依赖包（requests, beautifulsoup4, lxml）
- ✅ 自动设置 cron 定时任务

### 3. 验证安装

```bash
# 查看定时任务
crontab -l

# 手动测试运行一次
python3 weibo.py

# 查看日志
tail -f logs/cron.log
```

## 修改执行时间

编辑 crontab：

```bash
crontab -e
```

找到类似这样的行：
```
0 11 * * * /usr/bin/python3 /path/to/weibo.py >> /path/to/logs/cron.log 2>&1
```

修改时间格式：`分钟 小时 * * *`
- 每天 11:00: `0 11 * * *`
- 每天 09:30: `30 9 * * *`
- 每天 14:15: `15 14 * * *`

保存后，cron 会自动重新加载配置。

## 时区设置

确保服务器时区设置为北京时间：

```bash
# 查看当前时区
timedatectl

# 设置时区为上海（北京时间）
sudo timedatectl set-timezone Asia/Shanghai

# 验证
date
```

## 常用命令

```bash
# 查看所有定时任务
crontab -l

# 编辑定时任务
crontab -e

# 删除所有定时任务（谨慎使用）
crontab -r

# 查看程序日志
tail -f logs/cron.log

# 手动运行程序
python3 weibo.py

# 查看生成的 CSV 文件
cat shanghai_metro_data.csv
```

## 卸载

```bash
./uninstall_ubuntu.sh
```

## 注意事项

1. **Python 环境**：
   - 大多数 Ubuntu 系统默认已安装 Python3
   - 如果没有，需要先安装：`sudo apt-get install python3 python3-pip`
   - 安装脚本会自动安装依赖包，无需手动操作

2. **依赖包安装**：
   - `install_ubuntu.sh` 会自动执行 `pip3 install -r requirements.txt --user`
   - 依赖包会安装到用户目录（`~/.local/lib/python3.x/site-packages`）
   - 如果安装失败，可以手动执行：`pip3 install -r requirements.txt --user`

3. **网络连接**：确保服务器可以访问 `https://metrodb.org`

4. **文件权限**：确保脚本有执行权限（`chmod +x install_ubuntu.sh`）

5. **日志轮转**：日志文件会不断增长，建议定期清理或设置日志轮转

## 日志轮转设置（可选）

创建 `/etc/logrotate.d/weibo-metro`：

```
/path/to/ubuntu_deploy/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

## 故障排查

### 问题：任务没有执行

1. 检查 cron 服务是否运行：
   ```bash
   sudo systemctl status cron
   ```

2. 查看系统日志：
   ```bash
   grep CRON /var/log/syslog
   ```

3. 检查脚本路径是否正确：
   ```bash
   which python3
   ls -l /path/to/weibo.py
   ```

### 问题：找不到模块

确保已安装依赖：
```bash
pip3 install -r requirements.txt --user
```

或者使用虚拟环境：
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

然后在 crontab 中使用虚拟环境的 Python：
```
0 11 * * * /path/to/venv/bin/python /path/to/weibo.py >> /path/to/logs/cron.log 2>&1
```

