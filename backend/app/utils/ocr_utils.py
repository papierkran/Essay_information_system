import os
import json
import time
import hashlib
import base64
import re
import logging
from typing import Optional
import httpx

import requests
from openai import OpenAI

logger = logging.getLogger(__name__)


# ========== OCR (讯飞) ==========

def _get_xfyun_header(config: dict) -> dict:
    api_key = config.get("api_key", "")
    appid = config.get("appid", "")
    language = config.get("language", "cn|en")
    location = config.get("location", "false")
    cur_time = str(int(time.time()))
    param = json.dumps({"language": language, "location": location})
    param_base64 = base64.b64encode(param.encode("utf-8")).decode("utf-8")
    checksum_str = api_key + cur_time + param_base64
    checksum = hashlib.md5(checksum_str.encode("utf-8")).hexdigest()
    return {
        "X-CurTime": cur_time,
        "X-Param": param_base64,
        "X-Appid": appid,
        "X-CheckSum": checksum,
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    }


def ocr_image(image_path: str, config: dict, timeout: int = 30) -> list[str]:
    url = config.get("url", "")
    if not url:
        raise RuntimeError("OCR URL 未配置")

    with open(image_path, "rb") as f:
        img_data = f.read()

    data = {"image": base64.b64encode(img_data).decode("utf-8")}
    headers = _get_xfyun_header(config)

    max_retries = 3
    last_error = None
    for attempt in range(max_retries):
        try:
            resp = requests.post(url, headers=headers, data=data, timeout=timeout)
            resp.raise_for_status()
            result = resp.json()
            break
        except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ReadTimeout, requests.exceptions.Timeout) as e:
            last_error = e
            logger.warning(f"OCR 请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            continue
    else:
        raise RuntimeError(f"OCR 请求失败，已重试 {max_retries} 次: {last_error}")

    if result.get("code") != "0":
        raise RuntimeError(f"OCR 失败: {result.get('desc', '未知错误')}")

    lines = []
    for block in result.get("data", {}).get("block", []):
        if block.get("type") != "text":
            continue
        for line in block.get("line", []):
            text = "".join(w.get("content", "") for w in line.get("word", []))
            if text.strip():
                lines.append(text)

    paragraphs = []
    buffer = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if len(line) <= 4:
            buffer += line
            continue
        buffer += line
        if buffer[-1] in "。！？…" and len(buffer) >= 30:
            paragraphs.append(buffer)
            buffer = ""
    if buffer:
        paragraphs.append(buffer)

    return paragraphs


def ocr_essay_images(essay_dir: str, ocr_config: dict) -> str:
    if not os.path.isdir(essay_dir):
        raise RuntimeError(f"目录不存在: {essay_dir}")

    all_paragraphs = []
    for fname in sorted(os.listdir(essay_dir)):
        if not fname.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
            continue
        img_path = os.path.join(essay_dir, fname)
        if os.path.isdir(img_path):
            continue
        logger.info(f"OCR 识别: {fname}")
        paragraphs = ocr_image(img_path, ocr_config)
        all_paragraphs.extend(paragraphs)

    if not all_paragraphs:
        raise RuntimeError("目录中没有可识别的图片")

    return "\n".join(all_paragraphs)


DEFAULT_EDITOR_PROMPT = (
    "下面是一篇中文文章，请你【对文章进行改写】。\n"
    "要求：\n"
    "1. 可以改变原意，但要保持文章主题不变\n"
    "2. 可以润色文风\n"
    "3. 可以增删内容，但要保持文章结构合理\n"
    "4. 保持原有段落结构\n"
    "5. 只输出修改后的完整文章正文\n"
    "6. 格式应该是  标题  （\\n）下一行  ——xx(替换为姓名)  然后文章内容\n"
    "标题不要出现 题目： 标题：等字样\n\n"
    "{text}"
)


def _create_llm_client(llm_config: dict):
    base_url = (llm_config.get("base_url") or "").strip() or "https://api.deepseek.com/v1"
    api_key = (llm_config.get("api_key") or "").strip()
    model = (llm_config.get("model") or "").strip() or "deepseek-chat"
    provider_name = llm_config.get("provider", "deepseek")

    if not api_key:
        raise RuntimeError(f"LLM API Key 未配置 (provider: {provider_name})")

    proxy_env_vars = ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]
    saved_proxy = {}
    for var in proxy_env_vars:
        if var in os.environ:
            saved_proxy[var] = os.environ.pop(var)

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
    finally:
        os.environ.update(saved_proxy)

    return client, model


def _build_prompt(prompt_template: str, text: str) -> str:
    if "{text}" in prompt_template:
        return prompt_template.replace("{text}", text)
    return prompt_template + "\n\n" + text


# ========== AI 错别字修正 (OpenAI-compatible) ==========

DEFAULT_TYPO_FIX_PROMPT = (
    "下面是一篇中文文章，请你完成以下任务：\n"
    "1. 【只修改错别字和明显的识别错误】\n"
    "2. 【从文章中识别并提取元数据信息】\n\n"
    "要求：\n"
    "1. 不改变原意\n"
    "2. 不润色文风\n"
    "3. 不增删内容\n"
    "4. 保持原有段落结构\n\n"
    "请严格按照以下JSON格式输出（不要输出其他内容）：\n"
    "```json\n"
    "{{\n"
    '  "作文标题": "从文章中识别的标题，去掉题目、标题等前缀",\n'
    '  "作者": "从文章中识别的作者姓名，去掉——前缀",\n'
    '  "原文字数": "文章原始字数（包含标点，不含空格）",\n'
    '  "年级": "从文章中识别的年级，如：三年级、四年级等，如无法识别则填未知",\n'
    '  "线上或线下": "从文章中识别的线上或线下，如无法识别则填未知",\n'
    '  "修改后内容": "作文标题（换行）——作者姓名（换行）修正错别字后的完整文章内容"\n'
    "}}\n"
    "```\n\n"
    "注意：\n"
    "- 字数用代码统计（非估算），包含标点符号，不包含空格\n"
    "- 如果无法识别某个字段，请填写未知\n"
    "- 标题不要出现 题目： 标题：等字样\n"
    "- 修改后内容的第一行是作文标题，第二行是——作者姓名，然后是文章正文\n\n"
    "文章内容如下：\n"
    "{text}"
)


def ai_correct_text(text: str, llm_config: dict, prompt_template: str = None) -> dict:
    client, model = _create_llm_client(llm_config)
    if not prompt_template:
        prompt_template = llm_config.get("prompt") or DEFAULT_TYPO_FIX_PROMPT
    prompt = _build_prompt(prompt_template, text)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "你是一名严谨的中文校对助手"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        stream=False,
    )

    result_text = response.choices[0].message.content.strip()

    try:
        json_match = re.search(r"```json\s*(.*?)\s*```", result_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = result_text
        result_data = json.loads(json_str)
        required_fields = ["作文标题", "作者", "原文字数", "年级", "线上或线下", "修改后内容"]
        for field in required_fields:
            if field not in result_data:
                result_data[field] = "未知"
        return result_data
    except json.JSONDecodeError:
        logger.warning("解析 LLM 返回的 JSON 失败，使用原始文本")
        return {
            "作文标题": "未知",
            "作者": "未知",
            "原文字数": str(len([c for c in text if not c.isspace()])),
            "年级": "未知",
            "线上或线下": "未知",
            "修改后内容": result_text,
        }


def count_cjk_chars(text: str) -> int:
    count = 0
    for char in text:
        if '\u4e00' <= char <= '\u9fff' or '\u3400' <= char <= '\u4dbf':
            count += 1
    return count


def ai_rewrite_text(text: str, llm_config: dict, prompt_template: str = None, count_min: int = None, count_max: int = None) -> str:
    client, model = _create_llm_client(llm_config)
    if not prompt_template:
        prompt_template = DEFAULT_EDITOR_PROMPT

    max_attempts = 3
    last_result = None

    for attempt in range(1, max_attempts + 1):
        prompt = _build_prompt(prompt_template, text)

        if attempt > 1 and count_min is not None and count_max is not None:
            hint = (
                f"\n\n注意：你上次返回的内容字数不符合要求（{last_count}字），"
                f"请确保中文字数在 {count_min}-{count_max} 之间，重新修改。"
            )
            prompt += hint

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一名优秀的中文写作编辑助手"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            stream=False,
        )

        result_text = response.choices[0].message.content.strip()
        last_result = result_text

        if count_min is not None and count_max is not None:
            last_count = count_cjk_chars(result_text)
            if last_count < count_min or last_count > count_max:
                if attempt >= max_attempts:
                    raise RuntimeError(
                        f"AI 改写后字数 {last_count} 不在 {count_min}-{count_max} 范围内，"
                        f"已重试 {max_attempts} 次仍不符合要求"
                    )
                continue

        return result_text

    return last_result
