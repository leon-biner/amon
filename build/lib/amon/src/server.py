# server.py
from flask import Flask, request
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
    os._exit(0)

def runServer(args):
    app.run(port=args.port, debug=False)

