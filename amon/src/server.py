# server.py
from flask import Flask, request
import threading
import time
import os

from amon.src.blackbox import runBB


app = Flask(__name__)

@app.route("/run", methods=["POST"])
def run_blackbox():
    data = request.json
    args = type("Args", (), data)() # Make object to use same syntax as argparse in runBB
    result = runBB(args)
    return result

@app.route("/shutdown", methods=["POST"])
def shutdown():
    def delay_kill():
        time.sleep(0.2)
        os._exit(0)

    threading.Thread(target=delay_kill).start()
    return '', 200

def runServer(args):
    app.run(port=args.port, debug=False)

