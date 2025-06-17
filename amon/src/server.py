# server.py
from flask import Flask, request, jsonify
import os


app = Flask(__name__)

# _cached_instance_or_param_file = None
# _cached_blackbox = None
# _cached_wind_farm_data = None

# Import your functions once here
from amon.src.blackbox import runBB # , buildBB

@app.route("/run", methods=["POST"])
def run_blackbox():
    # global _cached_instance_or_param_file, _cached_blackbox, _cached_wind_farm_data
    data = request.json
    args = type("Args", (), data)() # Make object to use same syntax as argparse in runBB

    # if args.instance_or_param_file != _cached_instance_or_param_file:
        # _cached_blackbox, _cached_wind_farm_data = buildBB(args)
        # _cached_instance_or_param_file = args.instance_or_param_file

    result = runBB(args) # , _cached_blackbox, _cached_wind_farm_data)
    # return f"{jsonify({'status': 'success'})}\n{result}"
    return result

'''
@app.route("/show-windrose", methods=["POST"])
def show_windrose():
    data = request.json
    args = type("Args", (), data)()
    showWindrose(args)
    return jsonify({"status": "success"})

@app.route("/show-terrain", methods=["POST"])
def show_terrain():
    data = request.json
    args = type("Args", (), data)()
    showTerrain(args)
    return jsonify({"status": "success"})
'''

@app.route("/shutdown", methods=["POST"])
def shutdown():
    os._exit(0)

def runServer(args):
    app.run(port=args.port, debug=False)

