# Description: Main entry point for the web agent service.

import sys
import time
import threading
import random

import argparse
import json

from loguru import logger
from flask import Flask, request

from .actions.actions import ClickAction, TypeAction, ScrollAction, WaitAction, ScreenshotAction
from .classes import TaskSolution
from .openai_service import get_pages_to_upload, inference_actions


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


@app.route("/solve_task", methods=["POST"])
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

        is_web_real = task.get("is_web_real", "False")
        page_html = task.get("html", None)

        prompt_list = [ task_prompt ]
        prompt_list.append(f"The url for the web page is {page_url}")
        if is_web_real == "False":
            prompt_list.append("But it is not a url for the real web page, so you must only use it for filling fields in the Action objects.")

        prompt_text = "\n".join(prompt_list)
        pages_to_upload = get_pages_to_upload(prompt_text, page_url, page_html)
        actions = inference_actions(prompt_text, pages_to_upload)
    else:
        x = random.randint(0, DEFAULT_SCREEN_WIDTH - 1)  # Random x coordinate
        y = random.randint(0, DEFAULT_SCREEN_HEIGHT - 1)  # Random y coordinate
        actions.append(ClickAction(x=x, y=y))

    ts = TaskSolution(task_id=task_id, actions=actions, web_agent_id="openai_web_agent")
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
