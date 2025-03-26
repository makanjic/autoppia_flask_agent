#!/usr/bin/env python3

import sys
import os
import asyncio
import json

from typing import Any, List, Dict
from distutils.util import strtobool
from loguru import logger
from browser_use import Agent, Browser, BrowserConfig, Controller

import httpx
import gc

import pymongo

from config import LLM_PROVIDER, BROWSER_HEADLESS, MONGO_DB_URL, MONGO_DB_NAME
if LLM_PROVIDER == "gemini":
    from llm_gemini import llm
elif LLM_PROVIDER == "openai":
    from llm_openai import llm
else:
    llm = None

from actions.base import \
        SelectorType, Selector
from actions.actions import \
        ClickAction, DoubleClickAction, NavigateAction, \
        TypeAction, SelectAction, HoverAction, WaitAction, \
        ScrollAction, SubmitAction, DragAndDropAction, \
        ScreenshotAction, SendKeysIWAAction, GetDropDownOptions, \
        SelectDropDownOption, UndefinedAction, IdleAction



# Basic configuration
browser_config = BrowserConfig(
    headless=BROWSER_HEADLESS,
    disable_security=True
)



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
                result_action = GetDropDownOptions(selector=selector)
            case 'select_dropdown_option':
                if 'text' in action and action['text']:
                    text = action['text']
                else:
                    text = None 
                result_action = SelectDropDownOption(selector=selector, text=text)

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


async def llm_get_actions(task: Dict) -> List:
    logger.debug("getting inference for actions");
    logger.debug(f"task: {task}")

    myclient = pymongo.MongoClient(MONGO_DB_URL)
    mydb = myclient[MONGO_DB_NAME]
    mycol = mydb["task_solutions"]
    x = mycol.find_one({"prompt" : task['prompt'], "url" : task['url']})
    if x:
        logger.debug("found in db")
        logger.debug(f"actions {x['actions']}")
        return x['actions']

    browser = Browser(config=browser_config) 

    controller = Controller(exclude_actions=[
                            'search_google',
                            'save_pdf'
                            'open_tab',
                            'extract_content'
                            ])

    task_prompt = task.get("prompt", None)
    
    page_url = task.get("url", None)
    message_context = f"""
The url of home page is {page_url}.
All actions must start from this url.
"""

    is_web_real = bool(task.get("is_web_real", False))
    if is_web_real:
        message_context += """
This home page is on a real web site.
"""
    else:
        message_context += """
This home page is not a real web page, so failure is not a concern.
"""

#    scope = task.get("scope", "local")
#    if scope == "local":
#        message_context += """
#This home page is on the local site.
#"""

    specifications = task.get("specifications", None)
    if specifications:
        viewport_width = specifications.get("viewport_width", None)
        viewport_height = specifications.get("viewport_height", None)
        if viewport_width and viewport_height:
            message_context += f"""
The size of viewport is {viewport_width}x{viewport_height}.
"""
        screen_width = specifications.get("screen_width", None)
        screen_height = specifications.get("screen_height", None)
        if screen_width and screen_height:
            message_context += f"""
The size of screen is {screen_width}x{screen_height}.
"""

    relevant_data = task.get("relevant_data", None)
    if relevant_data:
        message_context += f"""
The relevant data is as following.
{relevant_data}
"""

    logger.debug(f"task is {task_prompt}")
    logger.debug(f"message_context is {message_context}")
    agent = Agent(
        browser=browser,
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
        actions = _convert_actions(model_actions)
        logger.debug(f"actions {actions}")
        if history.is_done() and len(actions) > 2:
            logger.debug("insert into db...")
            mycol.insert_one({"prompt": task['prompt'], "url": task['url'], "actions": actions})

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

        browser = Browser(config=browser_config)

        logger.debug(f"input: {s_input}")
        task = json.loads(s_input)
        actions = await llm_get_actions(task)
        
        actions_dump = [action.model_dump() for action in actions]
        logger.debug(f"dump: {actions_dump}")
        f_out.write(json.dumps(actions_dump))

    asyncio.run(main())
