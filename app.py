# Description: Main entry point for the web agent service.

import sys
import os
import time
import threading
import random
import argparse
import json
import asyncio
# import trio
import tempfile
import subprocess

from distutils.util import strtobool
from loguru import logger
from flask import Flask, request

from .actions.actions import ClickAction
from .classes import TaskSolution
from .openai_service import openai_infer_actions
# from .llm_agent import llm_get_actions


DEFAULT_SCREEN_WIDTH = 1920
DEFAULT_SCREEN_HEIGHT = 1080


app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello, I am a web agent!"


@app.route("/random_solve_task", methods=["POST"])
def random_task_handler():
    # return "Hello, I am a random web agent!"
    actions = []

    try:
        task = request.json or {}

        logger.info(f"task {task}")
        
        task_id = task.get("id", None)
        if task_id is None:
            return "Task ID not provided", 400

        specifications = task.get("specifications", None)
        if specifications is None:
            return "Task specifications not provided", 400

        # logger.debug("getting screen resolution")
        screen_width = specifications.get("screen_width", DEFAULT_SCREEN_WIDTH)
        screen_height = specifications.get("screen_height", DEFAULT_SCREEN_HEIGHT)
        # logger.debug(f"screen {screen_width}x{screen_height}")
    except:
        return "Invalid request format", 400

    x = random.randint(0, screen_width - 1)  # Random x coordinate
    y = random.randint(0, screen_height - 1)  # Random y coordinate
    actions.append(ClickAction(x=x, y=y))
    ts = TaskSolution(task_id=task_id, actions=actions, web_agent_id="random_web_agent")
    return ts.nested_model_dump()


@app.route("/openai_solve_task", methods=["POST"])
def openai_task_handler():
    # return "Hello, I am a openai web agent!"
    actions = []

    if True:
        task = request.json or {}

        logger.info(f"task {task}")
        
        task_id = task.get("id", None)
        if task_id is None:
            return "Task ID not provided", 400

        task_prompt = task.get("prompt", None)
        if task_prompt is None:
            return "Task prompt not provided", 400

        page_url = task.get("url", None)
        if page_url is None:
            return "Page URL not provided", 400

        is_web_real = bool(task.get("is_web_real", False))
        page_html = task.get("html", None)

        actions = openai_infer_actions(task_prompt, page_url, page_html)
    else:
        x = random.randint(0, DEFAULT_SCREEN_WIDTH - 1)  # Random x coordinate
        y = random.randint(0, DEFAULT_SCREEN_HEIGHT - 1)  # Random y coordinate
        actions.append(ClickAction(x=x, y=y))

    ts = TaskSolution(task_id=task_id, actions=actions, web_agent_id="openai_web_agent")
    return ts.nested_model_dump()

actions_cache = {}

@app.route("/solve_task", methods=["POST"])
async def llm_task_handler():
    # return "Hello, I am a openai web agent!"
    actions = []

    if True:
        task = request.json or {}

        logger.info(f"task {task}")
        
        task_id = task.get("id", None)
        if task_id is None:
            return "Task ID not provided", 400
        task_prompt = task.get("prompt", None)
        if task_prompt is None:
            return "Task prompt not provided", 400
        page_url = task.get("url", None)
        if page_url is None:
            return "Page URL not provided", 400

        if task_prompt in actions_cache.keys():
            log.debug("using cached actions...")
            actions = actions_cache[task_prompt]
            log.debug(f"cached: {actions}")
        else:
#        if True:
            # actions = await llm_get_actions(task)
            # actions = trio.run(llm_get_actions, task)
            # asyncio.set_event_loop(asyncio.ProactorEventLoop())
            # loop = asyncio.get_event_loop()
            # actions = loop.run_until_complete(llm_get_actions(task))
            # loop.close()

            actions = []
            tf_in, in_path = tempfile.mkstemp()
            tf_out, out_path = tempfile.mkstemp()
            with open(in_path, "w") as f:
                f.write(json.dumps(task))

            agent_pathname = "llm_agent.py"
            ret = subprocess.run(["python3", agent_pathname, in_path, out_path])
            if ret.returncode == 0:
                with open(out_path, "r") as f:
                    s_output = f.read()
                    logger.debug(f"agent output {s_output}")
                    actions = json.loads(s_output)

            os.close(tf_in)
            os.close(tf_out)
            os.unlink(in_path)
            os.unlink(out_path)

            if actions and len(actions) > 2:
                logger.debug("caching actions...")
                actions_cache[task_prompt] = actions
    else:
        x = random.randint(0, DEFAULT_SCREEN_WIDTH - 1)  # Random x coordinate
        y = random.randint(0, DEFAULT_SCREEN_HEIGHT - 1)  # Random y coordinate
        actions.append(ClickAction(x=x, y=y))

    # return actions
    ts = TaskSolution(task_id=task_id, actions=actions, web_agent_id="llm_web_agent")
    return ts.nested_model_dump()
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Autoppia Web Agent")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the service on")
    parser.add_argument("--port", type=int, default=9000, help="Port to run the service on")
    parser.add_argument("--debug", type=bool, default=False, help="Debug flag")
    args = parser.parse_args()

    # Run Flask so it only processes one request at a time
    # by disabling threading.
    app.run(host=args.host, port=args.port, debug=args.debug, use_reloader=False, threaded=False)
