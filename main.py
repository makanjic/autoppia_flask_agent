# Description: Main entry point for the web agent service.

import sys
import time
import threading
import random

import argparse
import json

from loguru import logger
from flask import Flask, request

from .actions.actions import ClickAction, TypeAction, ScrollAction, WaitAction, ScreenshotAction, ActionRegistry
from .classes import TaskSolution


DEFAULT_SCREEN_WIDTH = 1920
DEFAULT_SCREEN_HEIGHT = 1080

SOLVE_TASK_PROMT = """
"""

app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello, I am a web agent!"


@app.route("/solve_task", methods=["POST"])
def random_task_handler():
    actions = []

    try:
        data = request.json or {}

        task = data.get("task", {})
        if task is None:
            return "Task not provided", 400
        
        task_id = task.get("id", None)
        if task_id is None:
            return "Task ID not provided", 400

        specifications = task.get("specifications", None)
        if specifications is None:
            return "Task specifications not provided", 400

        screen_width = specifications.get("screen_width", DEFAULT_SCREEN_WIDTH)
        screen_height = specifications.get("screen_height", DEFAULT_SCREEN_HEIGHT)

        # Print final parameters & stats (optional debug)
        print("[handler] solve_task")
        print(f"  data:       {data}")
        print("[handler] .")

        x = random.randint(0, screen_width - 1)  # Random x coordinate
        y = random.randint(0, screen_height - 1)  # Random y coordinate
        actions.append(ClickAction(x=x, y=y))
        ts = TaskSolution(task_id=task_id, actions=actions, web_agent_id="random_web_agent")
        return json.dump(ts)
    except:
        return "Invalid request format", 400

    return "Hello, I am a random web agent!"


@app.route("/openai_solve_task", methods=["POST"])
def openai_task_handler():
    return "Hello, I am a web agent!"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Autoppia Web Agent")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the service on")
    parser.add_argument("--port", type=int, default=9000, help="Port to run the service on")
    parser.add_argument("--debug", type=bool, default=False, help="Debug flag")
    args = parser.parse_args()

    # Run Flask so it only processes one request at a time
    # by disabling threading.
    app.run(host=args.host, port=args.port, debug=args.debug, use_reloader=False, threaded=False)