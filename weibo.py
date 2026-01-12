import csv
import os
import re
from datetime import datetime, timedelta

import requests

from feishu import upload_csv

def scrape_shanghai_metro():
    url = "https://metrodb.org/index/shanghai.html"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8' # 强制使用utf-8防止乱码
        
        if response.status_code != 200:
            print("网页请求失败")
            return None

        # 数据是通过JavaScript动态加载的，需要从JavaScript代码中提取
        html_text = response.text
        
        # --- 1. 提取日期 ---
        # 从 JavaScript 代码中提取：$("#new_date").html("2026-01-03");
        # 注意：页面上的日期是「统计日期」，对应的客流为「昨日客流量」，
        #      因此保存到 CSV 时需要将日期往前推一天。
        date_text = "未找到"
        csv_date = "未找到"

        # 查找包含 new_date 和日期格式的行
        match = re.search(r'new_date.*?html.*?(\d{4}-\d{2}-\d{2})', html_text)
        if match:
            date_text = match.group(1)
        else:
            # 备用方法：查找标题中的日期
            match = re.search(r'上海地铁统计数据[（(](\d{4}-\d{2}-\d{2})[）)]', html_text)
            if match:
                date_text = match.group(1)

        # 计算 CSV 中使用的日期（统计日期往前推一天）
        try:
            if date_text != "未找到":
                dt = datetime.strptime(date_text, "%Y-%m-%d")
                csv_date = (dt - timedelta(days=1)).strftime("%Y-%m-%d")
        except Exception:
            # 日期解析失败则保持 "未找到"
            pass

        # --- 2. 提取运营线路数 (20) ---
        # 从 JavaScript 代码中提取：rollNum("line_open", 0, 20);
        lines_count = "未找到"
        match = re.search(r'rollNum\(["\']line_open["\'],\s*\d+,\s*(\d+)', html_text)
        if match:
            lines_count = match.group(1)

        # --- 3. 提取昨日客流量 (718.00) ---
        # 从 JavaScript 代码中提取：rollNum("flow_last", 0, 718.00, 2);
        flow_count = "未找到"
        match = re.search(r'rollNum\(["\']flow_last["\'],\s*\d+,\s*(\d+\.?\d*)', html_text)
        if match:
            flow_count = match.group(1)

        # --- 打印结果 ---
        print("-" * 30)
        print(f"统计日期: {date_text}")
        if csv_date != "未找到":
            print(f"写入CSV日期: {csv_date}（统计日期前一天）")
        print(f"运营线路: {lines_count}")
        print(f"昨日客流: {flow_count} (万)")
        print("-" * 30)
        
        # 返回提取的数据
        return {
            # 写入 CSV 使用「昨日」这一天的日期
            '日期': csv_date if csv_date != "未找到" else date_text,
            '地铁运营路线数': lines_count,
            '昨日客流量': flow_count
        }

    except Exception as e:
        print(f"抓取发生错误: {e}")
        return None

def save_to_csv(data, filename='shanghai_metro_data.csv'):
    """将数据保存到 CSV 文件，返回是否写入成功"""
    if data is None:
        print("没有数据可保存")
        return False
    
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(current_dir, filename)
    
    # 检查文件是否存在，决定是追加还是新建
    file_exists = os.path.exists(filepath)

    # 1. 按日期去重：如果当日数据已存在，则不再写入
    existing_dates = set()
    if file_exists:
        try:
            with open(filepath, 'r', encoding='utf-8-sig', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if '日期' in row and row['日期']:
                        existing_dates.add(row['日期'])
        except Exception as e:
            # 读取失败不影响后续写入，只是无法去重
            print(f"读取已有 CSV 时发生错误，跳过去重逻辑: {e}")

    target_date = data.get('日期')
    if target_date in existing_dates:
        print(f"日期 {target_date} 的数据已存在，跳过写入。")
        return False
    
    try:
        with open(filepath, 'a', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['日期', '地铁运营路线数', '昨日客流量']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # 如果文件不存在，写入表头
            if not file_exists:
                writer.writeheader()
            
            # 写入数据
            writer.writerow(data)
            print(f"\n数据已保存到: {filepath}")
            return True
            
    except Exception as e:
        print(f"保存 CSV 文件时发生错误: {e}")
    return False

if __name__ == "__main__":
    data = scrape_shanghai_metro()
    if data:
        saved = save_to_csv(data)
        if saved:
            print("开始上传飞书多维表格...")
            # 差异上传：上传CSV中有但飞书中没有的记录
            success_count = upload_csv()
            if success_count > 0:
                print(f"✅ 已上传 {success_count} 条新记录到飞书多维表格")
            else:
                print("ℹ️  无新记录需要上传")
        else:
            print("未新增数据，不触发飞书上传。")

