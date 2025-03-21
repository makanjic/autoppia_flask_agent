from typing import Any, List, Dict
import io
import time
import asyncio
import json
import openai
import tempfile

from loguru import logger
from .config import *
from .prompt import *
from .web_utils import get_html_contents

def _parse_response_json_list(response: str) -> List:
        """Parses a JSON list response from the LLM."""

        resp_fmt = ' { "data": {response} } '.replace("{response}", response)
        logger.debug(f"resp_fmt {resp_fmt}")

        try:
            resp_json = json.loads(resp_fmt)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}")

        logger.debug(f"resp_json {resp_json}")
        return resp_json["data"]




def infer_actions(task_prompt, portal_url, portal_html):
    logger.debug("getting inference for actions");
    logger.debug(f"task_prompt: {task_prompt}")
    logger.debug(f"portal_url: {portal_url}")
    logger.debug(f"portal_html: {portal_html}")

    if portal_html is None or not len(portal_html.strip()):
        logger.debug("refetching the portal page...")
        portal_html = asyncio.run(get_html_contents(portal_url))
        logger.debug(f"portal page size  {len(portal_html)}")
    if portal_html is None or not len(portal_html.strip()):
        logger.debug("failed to fetch the portal page or empty")
        return []

    # Set up OpenAI client
    logger.debug("creating client...")
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    # Create a vector store caled "Web Automation Testbed Store"
    vector_store = client.vector_stores.create(name="Web Automation Testbed Store")
    logger.debug(f"vector_store {vector_store}")

    logger.debug("creating assistant...")
    assistant = client.beta.assistants.create(
        name="The Web Automation Action Generator",
        instructions=SYSTEM_PROMPT,
        model=OPENAI_MODEL,
        tools=[ {"type": "file_search"} ],  # Enables file reading
        tool_resources={
            "file_search": {
                "vector_store_ids": [ vector_store.id ]
            }
        }
    )
    assistant_id = assistant.id
    logger.debug("creating thread...")
    response = client.beta.threads.create(
        tool_resources={
            "file_search": {
                "vector_store_ids": [ vector_store.id ]
            }
        }
    )
    thread_id = response.id

    logger.debug("getting upload pages")
    file_obj = io.BytesIO(portal_html.encode("utf-8"))
    response = client.files.create(file=("page0.html", file_obj), purpose="assistants")
    portal_file_id = response.id
    pages_uploaded = {
        portal_url : {
            "file": "page0.html",
            "html": portal_html,
            "id": portal_file_id
        }
    }

    # Send a message and get a response (while keeping context)
    def _chat_with_assistant(user_message, file_id_list):
        """Sends a message to an assistant and gets a response."""

        attachments = []
        if len(file_id_list) > 0:
            batch = client.vector_stores.file_batches.create_and_poll(
                vector_store_id=vector_store.id,
                file_ids=file_id_list
            )
            for file_id in file_id_list:
                attachments.append({
                    "file_id": file_id, "tools": [{"type": "file_search"}]
                })

        # Add the user's message to the thread
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message,
            attachments=attachments
        )

        # Run the assistant to generate a response
        run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)

        # Wait for the assistant to process the request
        while True:
            run_status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
            if run_status.status == "completed":
                break
            elif run_status.status == "expired":
                return None
            elif run_status.status == "failed":
                return None
            elif run_status.status == "incomplete":
                return None
            elif run_status.status == "cancelled":
                return None
            else:
                time.sleep(1)  # Wait before checking again

        # Get AI's response
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        return messages.data[0].content[0].text.value  # Extract text response

    user_prompt = FIRST_MISSION_PROMPT.format(
                    task_prompt=task_prompt,
                    portal_url=portal_url,
                    file_uploaded="page0.html")
    user_prompt += "\n" + OUTPUT_REQ_PROMPT
    
    logger.debug(f"first prompt: {user_prompt}")
    response = _chat_with_assistant(user_prompt, [ portal_file_id ])
    logger.debug(f"first response: {response}")
    # return []
    url_list = _parse_response_json_list(response)
    url_list = [ url for url in url_list if url not in pages_uploaded ]
    logger.debug(f"first response url: {url_list}")

    total_file_id_list = []
    while len(url_list) > 0:
        file_id_list = []
        mapping_list = []
        for page_url in url_list:
            page_html = asyncio.run(get_html_contents(page_url))
            file_name = "page{index}.html".format(index=len(pages_uploaded))
            logger.debug(f"page_url {page_url}");
            logger.debug(f"file_name {file_name}");
            logger.debug(f"page_size {len(page_html)}");

            file_obj = io.BytesIO(page_html.encode("utf-8"))
            response = client.files.create(file=(file_name, file_obj), purpose="assistants")
            file_id = response.id
            file_id_list.append(file_id)
            total_file_id_list.append(file_id)
            pages_uploaded[page_url] = {
                "file" : file_name,
                "html" : page_html,
                "id" : file_id
            }
            mapping_list.append(page_url + " : " + file_name)

        urls_uploaded = "\n".join(mapping_list)
        logger.debug(f"file_id_list {file_id_list}")
        logger.debug(f"url_uploaded {urls_uploaded}")
        user_prompt = NEXT_MISSION_PROMPT.format(urls_uploaded=urls_uploaded)
        user_prompt += "\n" + OUTPUT_REQ_PROMPT
        logger.debug(f"again prompt: {user_prompt}")
        response = _chat_with_assistant(user_prompt, file_id_list)
        logger.debug(f"again response: {response}")
        url_list = _parse_response_json_list(response)
        url_list = [ url for url in url_list if url not in pages_uploaded ]
        logger.debug(f"again response url: {url_list}")

    user_prompt = LAST_MISSION_PROMPT + "\n" + OUTPUT_REQ_PROMPT
    logger.debug(f"action prompt: {user_prompt}")
    response = _chat_with_assistant(user_prompt, [])
    logger.debug(f"action response: {response}")
    action_list = _parse_response_json_list(response)
    logger.debug(f"action list: {action_list}")

    # List all files in vector store
    files = client.vector_stores.files.list(vector_store.id)
    # Delete each file from vector store
    for file in files.data:
        logger.debug(f"Deleting file {file.id} from vector_store %{vector_store.id}")
        client.vector_stores.files.delete(vector_store_id = vector_store.id, file_id = file.id)
    # Delete vector store
    logger.debug(f"Deleting vector_store %{vector_store.id}")
    client.vector_stores.delete(vector_store.id)
    # Delete files uploaded
    for file_id in total_file_id_list:
        logger.debug(f"Deleting file: {file.id}")
        client.files.delete(file_id)
    logger.debug(f"Deleting assistant {assistant.id}")
    client.beta.assistants.delete(assistant.id)

    #for store in client.vector_stores.list():
    #    try:
    #        client.vector_stores.delete(vector_store_id=store.id)
    #    except:
    #        pass
    #for file in client.files.list():
    #    try:
    #        client.files.delete(file.id)
    #    except:
    #        pass
    #for assistant in client.beta.assistants.list():
    #    try:
    #        client.beta.assistants.delete(assistant.id)
    #    except:
    #        pass

    return action_list
