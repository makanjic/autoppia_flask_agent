#!/usr/bin/env python3

import sys
import os
import time
import asyncio
import json

from typing import Any, List, Dict
from distutils.util import strtobool
from loguru import logger
from browser_use import Agent, Controller
from browser_use.agent.views import AgentState
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig


import httpx
import gc

import pymongo

from config import DEMO_WEBS_STARTING_PORT
from config import LLM_PROVIDER, BROWSER_HEADLESS, MONGO_DB_URL, MONGO_DB_NAME
if LLM_PROVIDER == "gemini":
    from llm_gemini import llm
elif LLM_PROVIDER == "openai":
    from llm_openai import llm
elif LLM_PROVIDER == "perplexity":
    from llm_perplexity import llm
else:
    llm = None

from actions.base import \
        SelectorType, Selector
from actions.actions import \
        ClickAction, DoubleClickAction, NavigateAction, \
        TypeAction, SelectAction, HoverAction, WaitAction, \
        ScrollAction, SubmitAction, DragAndDropAction, \
        ScreenshotAction, SendKeysIWAAction, GetDropDownOptionsAction, \
        SelectDropDownOptionAction, UndefinedAction, IdleAction

from urllib.parse import urljoin
import aiohttp


def _convert_selector(element):
    s_type = None
    s_attr = None
    s_val = None

    result = None

    if element.attributes:
        attributes = element.attributes
    else:
        attributes = {}

    if 'id' in attributes and attributes['id']:
        s_type = SelectorType.ATTRIBUTE_VALUE_SELECTOR
        s_attr = 'id'
        s_val = attributes['id']
    elif 'name' in attributes and attributes['name']:
        s_type = SelectorType.ATTRIBUTE_VALUE_SELECTOR
        s_attr = 'name'
        s_val = attributes['name']
    elif element.xpath:
        s_type = SelectorType.XPATH_SELECTOR
        s_val = element.xpath
    elif 'class' in attributes and attributes['class']:
        s_type = SelectorType.ATTRIBUTE_VALUE_SELECTOR
        s_attr = 'class'
        s_val = attributes['class']

    if s_type:
        result = Selector(type=s_type, attribute=s_attr, value=s_val)

    return result


def _convert_actions(model_actions: List) -> List:
    result_action_list = []

    for model_action in model_actions:
        action_keys = list(model_action.keys())
        if not action_keys:
            continue
        action_name = action_keys[0]
        if not action_name:
            continue
        action = model_action[action_name]
        element = model_action['interacted_element']

        selector = None
        if element is not None:
            selector = _convert_selector(element)

        result_action = None
        match action_name:
            case 'search_google':
                pass
            case 'go_to_url':
                if 'url' in action and action['url']:
                    url=action['url']
                else:
                    url = None
                result_action = NavigateAction(url=url, go_back=False, go_forward=False)
            case 'go_back':
                result_action = NavigateAction(url=None, go_back=True, go_forward=False)
            case 'wait':
                if 'seconds' in action and action['seconds']:
                    seconds = float(action['seconds'])
                else:
                    seconds = 0
                result_action = WaitAction(time_seconds=seconds)
            case 'click_element':
                result_action = ClickAction(selector=selector)
            case 'input_text':
                if 'text' in action and action['text']:
                    text = action['text']
                else:
                    text = None
                result_action = TypeAction(selector=selector, text=text)
            case 'save_pdf':
                pass
            case 'switch_tab':
                pass
            case 'open_tab':
                pass
            case 'extract_content':
                pass
            case 'scroll_down':
                if 'amount' in action and action['amount']:
                    value = float(action['amount'])
                else:
                    value = None
                result_action = ScrollAction(up=False, down=True, value=value)
            case 'scroll_up':
                if 'amount' in action and action['amount']:
                    value = float(action['amount'])
                else:
                    value = None
                result_action = ScrollAction(up=True, down=False, value=value)
            case 'send_keys':
                if 'keys' in action:
                    keys = action['keys']
                else:
                    keys = None
                result_action = SendKeysIWAAction(keys=keys)
            case 'scroll_to_text':
                if 'text' in action and action['text']:
                    text = action['text']
                else:
                    text = None
                result_action = ScrollAction(up=False, down=False, value=text)
            case 'get_dropdown_options':
                result_action = GetDropDownOptionsAction(selector=selector)
            case 'select_dropdown_option':
                if 'text' in action and action['text']:
                    text = action['text']
                else:
                    text = None 
                result_action = SelectDropDownOptionAction(selector=selector, text=text)

        if result_action:
            result_action_list.append(result_action)

    return result_action_list


# XXX: it will be replaced of agent.close()
async def _agent_cleanup_httpx_clients(agent):
    """Cleanup all httpx clients"""

    # Force garbage collection to make sure all clients are in memory
    gc.collect()
    
    # Get all httpx clients
    clients = [obj for obj in gc.get_objects() if isinstance(obj, httpx.AsyncClient)]
    
    # Close all clients
    for client in clients:
        if not client.is_closed:
            try:
                await client.aclose()
            except Exception as e:
                logger.debug(f"Error closing httpx client: {e}")

async def _agent_close(agent: Agent):
    """Close all resources"""
    try:
        # First close browser resources
        # if agent.browser_context and not agent.injected_browser_context:
        if True:
            logger.debug("Closing browser_context...")
            await agent.browser_context.close()
        # if agent.browser and not agent.injected_browser:
        if True:
            logger.debug("Closing browser...")
            await agent.browser.close()
        
        # Then cleanup httpx clients
        logger.debug("Cleaning up the httpx clients...")
        # await agent.cleanup_httpx_clients()
        await _agent_cleanup_httpx_clients(agent)
        
        # Force garbage collection
        logger.debug("Forcing garbage collection...")
        gc.collect()
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


async def reset_site_database(site_url: str) -> bool:
    """
    Resets the entire database (requires admin/superuser permissions).
    """
    
    logger.info("Resetting Project Environment & Database.")
    endpoint = urljoin(site_url, "management_admin/reset_db/")
    try:
        session = aiohttp.ClientSession()
        async with session.post(endpoint, timeout=30) as response:
            response.raise_for_status()

            try:
                response_json = await response.json()
                status = response_json.get("status")
                message = response_json.get("message", "")

                if status == "success":
                    logger.info(f"Database reset initiated: {message}. Lasted: {time.time() - start_time}")
                    return True
                else:
                    logger.warning(f"Database reset failed: {message} Lasted: {time.time() - start_time}")
                    return False

            except Exception:
                # If we can't parse JSON, check status code
                if response.status in (200, 202):
                    logger.info("Database reset initiated successfully.")
                    return True
                else:
                    logger.warning(f"Database reset completed with unexpected status: {response.status}")
                    return False

    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        return False
    finally:
        if session:
            await session.close()


async def llm_get_actions(task: Dict) -> List:
    logger.debug("getting inference for actions");
    logger.debug(f"task: {task}")

    myclient = pymongo.MongoClient(MONGO_DB_URL)
    mydb = myclient[MONGO_DB_NAME]
    mycol = mydb["task_solutions"]

    task_prompt = task.get("prompt", None)
    page_url = task.get("url", None)
    task_spec = task.get("specifications", None)
    relevant_data = task.get("relevant_data", None)

    db_accessible = True
    try:
        x = mycol.find({"prompt" : task_prompt,
                        "url" : page_url,
                        "specifications" : task_spec,
                        "relevant_data" : relevant_data})
        x = list(x)
        if len(x) > 0:
            logger.debug(f"found in db - count is {len(x)}")
            logger.debug(f"x is {x}")
            maxlen = 0
            used_actions = None
            for doc in x:
                try:
                    actions = doc.get('actions', [])
                    is_done = bool(doc.get('is_done', False))               
                    if actions and is_done and maxlen < len(actions):
                        maxlen = max(maxlen, len(actions))
                        used_actions = actions
                except Exception as e:
                    logger.debug(f"Error processing document {doc}: {e}")
                    pass
            if used_actions is not None:
                logger.debug(f"used_actions {used_actions}")
                actions = used_actions
            else:
                actions = []
            if len(actions) > 2:
                logger.debug(f"using the search result from db")
                return actions
            else:
                logger.debug("ignore the search result from db")
        else:
            logger.debug("no found in db")
    except Exception as e:
        db_accessible = False
        logger.debug(f"failed to access db: {e}")

    browser = Browser(config=BrowserConfig(
            headless=BROWSER_HEADLESS,
            disable_security=True
        )
    )
    browser_context = BrowserContext(
            browser=browser,
            config=BrowserContextConfig(
                highlight_elements=False,
            )
    )

    agent_state = AgentState()
    controller = Controller(exclude_actions=[
                            'search_google',
                            'save_pdf',
                            'open_tab',
                            'extract_content'
                            ])

    message_context = f"""
The url of site is {page_url}.
The first action must be navigating to this url.
"""

    is_web_real = bool(task.get("is_web_real", False))
    if not is_web_real:
        message_context += """
Try a action only once. - DO NOT retry a action more since it fails.
"""

    logger.debug(f"task is {task_prompt}")
    agent = Agent(
        browser=browser,
        controller=controller,
        browser_context=browser_context,
        injected_agent_state=agent_state,
        task=task_prompt,
        message_context=message_context,
        llm=llm,
        max_failures=1
    )

    model_actions = []
    try:
        history = await agent.run()
    finally:
        # await browser.close()
        await _agent_close(agent)

    # if history.is_done():
    if True:
        model_actions = history.model_actions()
        logger.debug(f"model_actions {model_actions}")

    actions = []
    if model_actions:
        action_objects = _convert_actions(model_actions)
        logger.debug(f"action_objects {action_objects}")
        actions = [action.model_dump() for action in action_objects]
        logger.debug(f"actions {actions}")
        if db_accessible:
            logger.debug("trying to insert into db...")
            try:
                mycol.update_one(
                    {
                        "prompt": task_prompt,
                        "url": page_url,
                        "specifications": task_spec,
                        "relevant_data" : relevant_data,
                        "actions": actions,
                        "is_done": history.is_done(),
                    },
                    {
                        "$set": {
                            "prompt": task_prompt,
                            "url": page_url,
                            "specifications": task_spec,
                            "relevant_data" : relevant_data,
                            "actions": actions,
                            "is_done": history.is_done(),
                        }
                    },
                    upsert=True
                )
            except Exception as e:
                logger.debug(f"failed to insert db: {e}")

    return actions


if __name__ == "__main__":
    async def main():
        if len(sys.argv) > 1:
            f_in = open(sys.argv[1], "r")
            s_input = f_in.read()
            f_in.close()
        else:
            s_input = sys.stdin.read()

        if len(sys.argv) > 2:
            f_out = open(sys.argv[2], "w")
        else:
            f_out = sys.stdout

        logger.debug(f"input: {s_input}")
        task = json.loads(s_input)

        site_url = task.get("url", None)
        if site_url is not None:
            reset_success = await reset_site_database(site_url)
            if reset_success:
                logger.debug("Database reset successfully.")
            else:
                logger.debug("Database reset failed or not required.")

        actions = await llm_get_actions(task)
        f_out.write(json.dumps(actions))

    asyncio.run(main())
