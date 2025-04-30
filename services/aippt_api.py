import base64
import hashlib
import hmac

import requests
import time
import json

Channel = 'aippt-dify'
Host = 'https://co.aippt.cn'

# 自定义异常类
class AipptApiException(Exception):
    def __init__(self, message, code=None):
        self.message = message
        self.code = code
        super().__init__(message)

    def __str__(self):
        if self.code:
            return f"[Error {self.code}] {self.message}"
        return self.message

# 获取鉴权
def grant_token(api_key:str, secret_key:str):
    url = Host + '/api/grant/token'
    # 获取当前时间的秒级时间戳
    timestamp = int(time.time())

    # 生成签名
    body = f"GET@/api/grant/token/@{timestamp}"
    print("签名body：", body)
    # 使用 HMAC-SHA1 进行加密
    hashed = hmac.new(secret_key.encode(), body.encode(), hashlib.sha1)
    # 将加密结果输出为 Base64 编码
    signature = base64.b64encode(hashed.digest()).decode()

    headers = {
        "x-api-key": api_key,
        "x-timestamp": str(timestamp),
        "x-signature": signature
    }
    params = {
        "channel": Channel,
        "uid": 'dify'
    }

    print("[获取鉴权] Url:", url, " Headers:", headers, " Params:", params)

    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()
    print("Response JSON:", data)

    if 'code' not in data:
        raise Exception('code 不存在')

    if data['code'] != 0:
        raise Exception(data['msg'])

    return data


class AipptApi:
    def __init__(self, api_key:str, token:str):
        self.api_key = api_key
        self.token = token

    # 步骤1.任务创建
    def create_task(self, title, page, group, scene, tone):
        url = Host + '/api/ai/chat/v2/task'
        senior_options = {
            'page': int(page),
            'group': int(group),
            'scene': int(scene),
            'tone': int(tone),
        }

        # if len(files) > 0:
        #     param_type = 17
        # else:
        #     param_type = 1

        params = {
            'type': 1,
            'title': title,
            'senior_options': json.dumps(senior_options, ensure_ascii=False),
        }
        headers = {
            'x-api-key': self.api_key,
            'x-channel': Channel,
            'x-token': self.token,
        }
        print("[步骤1.任务创建] Url:", url, " Headers:", headers, " Params:", params)

        # resp = requests.post(url, headers=headers, data=params, files=files)
        resp = requests.post(url, headers=headers, data=params)
        resp.raise_for_status()
        data = resp.json()
        print("Response JSON:", data)
        if data['code'] != 0:
            raise AipptApiException(data['msg'], data['code'])

        return data

    # 步骤2.生成大纲
    def generate_outline(self, task_id, callback):
        url = Host + '/api/ai/chat/outline'
        params = {
            "task_id": task_id,
        }

        headers = {
            'x-api-key': self.api_key,
            'x-channel': Channel,
            'x-token': self.token,
            'Accept': 'text/event-stream',
            'Content-Type': 'text/event-stream',
        }
        print("[步骤2.生成大纲] Url:", url, " Headers:", headers, " Params:", params)

        response = requests.get(url, headers=headers, params=params, stream=True)
        response.raise_for_status()
        for line in response.iter_lines():
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith("data"):
                line = decoded_line.lstrip("data:")  # 去掉 "data:" 前缀
                if "close" in line:
                    print("close")
                    break

                try:
                    lineJson = json.loads(line)  # 解析 JSON
                    if lineJson.get("code", 0) != 0:
                        raise AipptApiException(lineJson.get("message", ""), lineJson.get("code", 0))

                    content = lineJson.get("content", "")  # 获取 "content" 字段
                    print("content:", content)
                    yield callback(content)
                except json.JSONDecodeError:
                    continue
            else:
                try:
                    decoded_line_json = json.loads(decoded_line)  # 解析 JSON
                    code = decoded_line_json.get("code", "")
                    msg = decoded_line_json.get("msg", "")
                    print("code:", code, "msg:", msg)
                    if code != 0:
                        raise AipptApiException(msg, code)

                except json.JSONDecodeError:
                    continue
                break



    # 步骤2.大纲生成内容 (新)
    def chat_content(self, task_id):
        url = Host + '/api/ai/chat/v2/content'
        params = {
            "task_id": task_id,
        }
        headers = {
            'x-api-key': self.api_key,
            'x-channel': Channel,
            'x-token': self.token,
        }
        print("[步骤2.大纲生成内容 (新)] Url:", url, " Headers:", headers, " Params:", params)

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        print("Response JSON:", data)
        if data['code'] != 0:
            raise AipptApiException(data['msg'], data['code'])

        return data

    # 步骤3.大纲生成内容结果查询 (新)
    def chat_content_check(self, ticket):
        url = Host + '/api/ai/chat/v2/content/check'
        params = {
            "ticket": ticket,
        }
        headers = {
            'x-api-key': self.api_key,
            'x-channel': Channel,
            'x-token': self.token,
        }
        print("[步骤3.大纲生成内容结果查询 (新)] Url:", url, " Headers:", headers, " Params:", params)

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        print("Response JSON:", data)
        if data['code'] != 0:
            raise AipptApiException(data['msg'], data['code'])

        return data

    # 模板套装列表
    def template_component(self, page: int, page_size: int, suit_scene: int, suit_style: int, colour: int):
        url = Host + '/api/template_component/suit/search'
        params = {
            "scene_id": suit_scene,
            "style_id": suit_style,
            "colour_id": colour,
            "page": 1,
            "page_size": 50,
        }
        headers = {
            'x-api-key': self.api_key,
            'x-channel': Channel,
            'x-token': self.token,
        }
        print("[模板套装列表] Url:", url, " Headers:", headers, " Params:", params)

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        print("Response JSON:", data)
        if data['code'] != 0:
            raise AipptApiException(data['msg'], data['code'])

        return data

    # 作品生成
    def design_save(self, task_id, template_id):
        url = Host + '/api/design/v2/save'
        params = {
            "task_id": task_id,
            "template_id": template_id,
            "template_type": 1,
        }
        headers = {
            'x-api-key': self.api_key,
            'x-channel': Channel,
            'x-token': self.token,
        }
        print("[作品生成] Url:", url, " Headers:", headers, " Params:", params)

        response = requests.post(url, headers=headers, data=params)
        response.raise_for_status()
        data = response.json()
        print("Response JSON:", data)
        if data['code'] != 0:
            raise AipptApiException(data['msg'], data['code'])

        return data

    # 作品导出
    def design_export(self, design_id):
        url = Host + '/api/download/export/file'
        params = {
            "id": design_id,
            "format": 'ppt',
            "edit": 'true',
            "files_to_zip": 'true',
        }
        headers = {
            'x-api-key': self.api_key,
            'x-channel': Channel,
            'x-token': self.token,
        }
        print("[作品导出] Url:", url, " Headers:", headers, " Params:", params)

        response = requests.post(url, headers=headers, data=params)
        response.raise_for_status()
        data = response.json()
        print("Response JSON:", data)
        if data['code'] != 0:
            raise AipptApiException(data['msg'], data['code'])

        return data

    # 作品导出结果查询
    def design_export_result(self, task_key):
        url = Host + '/api/download/export/file/result'
        params = {
            "task_key": task_key,
        }
        headers = {
            'x-api-key': self.api_key,
            'x-channel': Channel,
            'x-token': self.token,
        }
        print("[作品导出结果查询] Url:", url, " Headers:", headers, " Params:", params)
        response = requests.post(url, headers=headers, data=params)
        response.raise_for_status()
        data = response.json()
        print("Response JSON:", data)
        if data['code'] == 43103:
            raise AipptApiException(data['msg'], data['code'])
        elif data['code'] != 0:
            raise Exception(data['msg'])

        return data