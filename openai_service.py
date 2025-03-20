from typing import Any, List, Dict
import io
import asyncio
import json
import openai
import tempfile

from loguru import logger
from .config import *
from .prompt import *
from .web_utils import get_html_contents

def _parse_json_response(response: str) -> Dict[Any, Any]:
        """Parses a JSON response from the LLM."""
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}")

# Function to create and write to a temporary file
def _create_temp_file(content):
    """Creates a temporary file with the given content and returns its path."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8", suffix=".html")
    temp_file.write(content)
    temp_file.flush()  # Ensure data is written
    return temp_file.name

def get_pages_to_upload(task_prompt, portal_url, portal_html):
    pages_uploaded = []

    logger.debug("getting pages to be uploaded");
    logger.debug(f"task_prompt: {task_prompt}")
    logger.debug(f"portal_url: {portal_url}")
    logger.debug(f"portal_html: {portal_html}")

    if portal_html is None or not len(portal_html.strip()):
        logger.debug("recrawling the portal page...")
        portal_html = asyncio.run(get_html_contents(portal_url))
        logger.debug(f"portal page size  {len(portal_html)}")

    portal_file = _create_temp_file(portal_html)
    pages_uploaded = {
        portal_url : {
            "file": portal_file,
            "html": portal_html,
        }
    }

    while True:
        sync_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        file_id_list = []
        mapping_list = []
        tempfile_list = []

        for k, v in pages_uploaded.items():
            page_url = k
            file_name = v["file"]
            page_contents = v["html"]

            logger.debug(f"page_url {page_url}");
            logger.debug(f"file_name {file_name}");
            logger.debug(f"page_size {len(page_contents)}");

            # file_obj = io.BytesIO(page_contents.encode("utf-8"))
            # response = sync_client.files.create(file=(file_name, file_obj), purpose="assistants")
            # file_id_list.append(response.id)
            with open(file_name, "rb") as file:
                response = sync_client.files.create(file=file, purpose="assistants")
                file_id_list.append(response.id)

            mapping_list.append(page_url + " : " + file_name)

        urls_uploaded = "\n".join(mapping_list)
        
        logger.debug(f"file_id_list {file_id_list}")
        logger.debug(f"url_uploaded {urls_uploaded}")
        prompt = USER_FETCH_URL_PROMPT.format(task_prompt=task_prompt,
                                              urls_uploaded=urls_uploaded)
        logger.debug(f"prompt {prompt}")
        payload = {
            "model": OPENAI_MODEL,
            "messages": [
                # { "role": "system", "content": SYSTEM_FETCH_URL_PROMPT },
                {"role": "system", "content": "You are a helpful AI assistant."},
                { "role": "user", "content": prompt, "file_ids": file_id_list }
            ],
            "temperature": float(OPENAI_TEMPERATURE),
            "max_tokens": int(OPENAI_MAX_TOKENS),
        }

        response = sync_client.chat.completions.create(**payload)

        resp_text = response.choices[0].message.content
        logger.debug(f"url_resp_text {resp_text}")
        resp_fmt = ' { "required": {resp_text} } '.replace("{resp_text}", resp_text)
        logger.debug(f"url_resp_fmt {resp_fmt}")
        resp_json = _parse_json_response(resp_fmt)
        logger.debug(f"url_resp_json {resp_json}")
        url_list = resp_json['required']

        del sync_client

        if not isinstance(url_list, list) or not len(url_list):
            break

        count = 0
        for page_url in url_list:
            if page_url in pages_uploaded:
                continue
            count += 1
            page_html = asyncio.run(get_html_contents(page_url))
            # file_name = "page{index}.html".format(index=len(pages_uploaded))
            file_name = _create_temp_file(page_html)
            pages_uploaded[page_url] = {
                "file" : file_name,
                "html" : page_html
            }
        if count == 0:
            break

    return pages_uploaded



def inference_actions(task_prompt, pages_uploaded):
    """Creates an in-memory file, uploads it, and sends a chat request including the file."""
    logger.debug("getting actions required to perform the task");

    sync_client = openai.OpenAI(api_key=OPENAI_API_KEY)
    file_id_list = []
    mapping_list = []

    for k, v in pages_uploaded.items():
        page_url = k
        file_name = v["file"]
        page_contents = v["html"]

        # file_obj = io.BytesIO(page_contents.encode("utf-8"))
        # response = sync_client.files.create(file=(file_name, file_obj), purpose="assistants")
        # file_id_list.append(response.id)
        with open(file_name, "rb") as file:
            response = sync_client.files.create(file=file, purpose="assistants")
            file_id_list.append(response.id)

        mapping_list.append(page_url + " : " + file_name)

    urls_uploaded = "\n".join(mapping_list)

    prompt = REQUEST_ACTIONS_PROMPT.format(task_prompt=task_prompt,
                                           urls_uploaded=urls_uploaded)
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            { "role": "system", "content": CONVERT_RESPONSE_TO_JSON_PROMPT },
            { "role": "user", "content": prompt, "file_ids": file_id_list }
        ],
        "temperature": float(OPENAI_TEMPERATURE),
        "max_tokens": int(OPENAI_MAX_TOKENS),
    }

    response = sync_client.chat.completions.create(**payload)
    resp_text = response.choices[0].message.content
    resp_fmt = ' { "actions": {resp_text} } '.replace("{resp_text}", resp_text)
    logger.debug(f"action_resp_fmt {resp_fmt}")
    resp_json = _parse_json_response(resp_fmt)
    logger.debug(f"action_resp_json {resp_json}")
    return resp_json["actions"]
