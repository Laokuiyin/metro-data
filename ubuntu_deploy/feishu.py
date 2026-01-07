import csv
import json
import time
from pathlib import Path

import requests
import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *


CSV_PATH = Path(__file__).parent / "shanghai_metro_data.csv"
APP_TOKEN = "U7Oibq2HIaoOVdsBeqccFp6gnAg"
TABLE_ID = "tblocD8QRdUqUi9Z"
APP_ID = "cli_a9d63838bbf81bd1"
APP_SECRET = "ldl7dRCzgYHVNZKzVlJFthhlBqlQF8C7"

# 缓存 token
_token_cache = {
    "token": None,
    "expires_at": 0
}


def get_tenant_access_token():
    """获取 tenant_access_token，支持缓存和自动刷新."""
    current_time = time.time()
    if _token_cache["token"] and current_time < _token_cache["expires_at"] - 60:  # 提前1分钟刷新
        return _token_cache["token"]
    
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    data = {
        "app_id": APP_ID,
        "app_secret": APP_SECRET
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        if result.get("code") == 0:
            token = result["tenant_access_token"]
            expires_in = result.get("expire", 7200)  # 默认2小时
            _token_cache["token"] = token
            _token_cache["expires_at"] = current_time + expires_in
            return token
        else:
            error_msg = f"获取 tenant_access_token 失败: code={result.get('code')}, msg={result.get('msg')}"
            print(error_msg)
            raise Exception(error_msg)
    else:
        error_msg = f"HTTP 错误: {response.status_code}, {response.text}"
        print(error_msg)
        raise Exception(error_msg)


def load_rows(csv_path: Path = CSV_PATH):
    """读取本地 CSV，返回包含字段映射的列表."""
    rows = []
    # 使用 utf-8-sig 编码以正确处理 BOM
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 跳过空行
            if not any(row.values()):
                continue
            date = row.get("日期", "").strip()
            lines = row.get("地铁运营路线数", "").strip()
            flow = row.get("昨日客流量", "").strip()
            # 确保所有字段都有值
            if date and lines and flow:
                rows.append(
                    {
                        "日期": date,
                        "地铁运营路线数": lines,
                        # 映射昨日客流量 -> 人次，并转换为整数
                        "人次": int(float(flow)),
                    }
                )
    return rows


def push_row(fields, client, token):
    """将单条数据写入飞书多维表格."""
    option = lark.RequestOption.builder().tenant_access_token(token).build()
    request = (
        CreateAppTableRecordRequest.builder()
        .app_token(APP_TOKEN)
        .table_id(TABLE_ID)
        .request_body(AppTableRecord.builder().fields(fields).build())
        .build()
    )
    response: CreateAppTableRecordResponse = client.bitable.v1.app_table_record.create(
        request, option
    )
    if not response.success():
        error_msg = f"上传失败: code={response.code}, msg={response.msg}, log_id={response.get_log_id()}"
        try:
            error_detail = json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)
            error_msg += f"\n详情: {error_detail}"
        except:
            pass
        lark.logger.error(error_msg)
        print(f"❌ {error_msg}")
        return False
    else:
        lark.logger.info(lark.JSON.marshal(response.data, indent=4))
        print(f"✅ 成功上传: {fields.get('日期', 'N/A')}")
        return True


def get_existing_dates(client, token):
    """获取表格中已存在的日期列表."""
    option = lark.RequestOption.builder().tenant_access_token(token).build()
    request = (
        ListAppTableRecordRequest.builder()
        .app_token(APP_TOKEN)
        .table_id(TABLE_ID)
        .build()
    )
    response = client.bitable.v1.app_table_record.list(request, option)
    if response.success():
        existing_dates = set()
        for record in response.data.items:
            date = record.fields.get("日期")
            if date:
                existing_dates.add(date)
        return existing_dates
    else:
        lark.logger.error(f"查询现有记录失败: {response.msg}")
        return set()


def push_rows(rows, client, token):
    """将多条数据写入飞书多维表格."""
    success_count = 0
    for fields in rows:
        if push_row(fields, client, token):
            success_count += 1
    return success_count


def upload_single_record(date, lines, flow):
    """上传单条记录到飞书多维表格."""
    client = (
        lark.Client.builder()
        .enable_set_token(True)
        .log_level(lark.LogLevel.DEBUG)
        .build()
    )
    token = get_tenant_access_token()
    fields = {
        "日期": date,
        "地铁运营路线数": lines,
        "人次": flow,
    }
    return push_row(fields, client, token)


def upload_csv(csv_path: Path = CSV_PATH, only_latest=False):
    """上传 CSV 数据到飞书多维表格.
    
    Args:
        csv_path: CSV 文件路径
        only_latest: 如果为 True，只上传最后一条记录（最新的）
    """
    client = (
        lark.Client.builder()
        .enable_set_token(True)
        .log_level(lark.LogLevel.DEBUG)
        .build()
    )
    token = get_tenant_access_token()
    rows = load_rows(csv_path)
    if not rows:
        lark.logger.warning(f"未在 {csv_path} 中找到数据")
        print(f"⚠️  未在 {csv_path} 中找到数据")
        return 0
    
    # 获取现有日期，避免重复上传
    existing_dates = get_existing_dates(client, token)
    rows = [row for row in rows if row["日期"] not in existing_dates]
    if not rows:
        print("ℹ️  所有数据已存在，无需上传")
        return 0
    
    if only_latest:
        # 只上传最后一条记录
        rows = [rows[-1]]
        print(f"📤 上传最新记录: {rows[0].get('日期', 'N/A')}")
    
    return push_rows(rows, client, token)


if __name__ == "__main__":
    upload_csv()