#argparsing.py
import argparse

def create_parser(run_function, windrose_function, show_terrain_function, server_start_function, server_stop_function):
    parser = argparse.ArgumentParser(description="AMON, a Wind Farm Blackbox\nUse AMON_HOME in filepaths to refer to {AMON_HOME}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: run
    parser_run = subparsers.add_parser("run", help="Run Blackbox")
    parser_run.add_argument("instance_or_param_file", metavar="INSTANCE/PARAM_FILE", help=f"Id of instance or path from current directory to parameter file.")
    parser_run.add_argument("point", metavar="POINT", help=f"Path from current directory to file containing point to evaluate. ")
    parser_run.add_argument("-s", action='store_true', help="Send requests to the server instead of directly running")
    parser_run.add_argument("--port", metavar="PORT", help="Port number")
    parser_run.set_defaults(func=run_function)

    # Subcommand: windrose (to show the windrose of wind_data_n folder)
    parser_windrose = subparsers.add_parser("show-windrose", help="Display windrose plot")
    parser_windrose.add_argument("wind_data_id", type=int, metavar="WIND_DATA_ID", help="Id of wind data")
    parser_windrose.add_argument("--save", metavar="FIGURE_PATH_PNG", help="Save figure(png) to provided path") 
    parser_windrose.set_defaults(func=windrose_function)

    # Subcommand: show-terrain (to show zone_n, optionally with a given point)
    parser_terrain = subparsers.add_parser("show-terrain", help="Display terrain")
    parser_terrain.add_argument("zone_id", type=int, metavar="ZONE_ID", help="Id of the zone")
    parser_terrain.add_argument("--point", metavar="POINT", help="Display points in provided file on figure")
    parser_terrain.add_argument("--save", metavar="FIGURE_PATH_PNG", help="Save figure (png) to provided path")
    parser_terrain.add_argument("--no-grid", action='store_true', help="Remove grid from figure")
    parser_terrain.add_argument("--scale-factor", type=float, metavar="SCALE_FACTOR", help="Factor by which to multiply the size of the terrain")
    parser_terrain.set_defaults(func=show_terrain_function)

    # Subcommand: start server
    parser_server = subparsers.add_parser("serve", help="Start server")
    parser_server.add_argument("--port", type=int, metavar="PORT", help="Port number")
    parser_server.set_defaults(func=server_start_function)

    #Subcommand : stop server
    parser_server = subparsers.add_parser("shutdown", help="Stop server")
    parser_server.add_argument("--port", type=int, metavar="PORT", help="Port number")
    parser_server.set_defaults(func=server_stop_function)

    return parser