#argparsing.py
import argparse

from amon.src.utils import AMON_HOME

def create_parser(run_f, windrose_f, show_zone_f, show_turbine_f, show_elevation_f, instance_info_f, check_f, start_server_f, shutdown_server_f):
    parser = argparse.ArgumentParser(description=f"AMON, a Wind Farm Blackbox. Use \033[94mAMON_HOME\033[0m in filepaths to refer to: \033[94m{AMON_HOME}\033[0m. The provided starting points are in \033[94mAMON_HOME/starting_pts/xn.txt\033[0m")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Command: run
    parser_run = subparsers.add_parser("run", help="\033[94mRun Blackbox\033[0m")
    parser_run.add_argument("instance_or_param_file", metavar="INSTANCE/PARAM_FILE", help=f"\033[94mId of instance or path from current directory to parameter file.\033[0m")
    parser_run.add_argument("point", metavar="POINT", help=f"\033[94mPath from current directory to file containing point to evaluate.\033[0m")
    parser_run.add_argument("-r", action='store_true', help="Send requests to the server instead of directly running")
    parser_run.add_argument("-s", type=int, metavar='SEED', help='Set the seed')
    parser_run.add_argument("--port", metavar="PORT", help="Port number")
    parser_run.add_argument("--debug", action='store_true', help='Show full error messages')
    parser_run.set_defaults(func=run_f)

    # Command: windrose (to show the windrose of wind_data_n folder)
    parser_windrose = subparsers.add_parser("show-windrose", help="\033[94mDisplay windrose plot\033[0m")
    parser_windrose.add_argument("wind_data_id", type=int, metavar="WIND_DATA_ID", help="\033[94mId of wind data\033[0m")
    parser_windrose.add_argument("--save", metavar="FIGURE_PATH_PNG", help="Save figure(png) to provided path") 
    parser_windrose.add_argument("--debug", action='store_true', help='Show full error messages')
    parser_windrose.set_defaults(func=windrose_f)

    # Command: show-zone (to show zone_n, optionally with a given point)
    parser_zone = subparsers.add_parser("show-zone", help="\033[94mDisplay zone\033[0m")
    parser_zone.add_argument("zone_id", type=int, metavar="ZONE_ID", help="\033[94mId of the zone\033[0m")
    parser_zone.add_argument("--point", metavar=("POINT_FILE", "NB_TURBINES"), nargs=2, help="Display points in provided file on figure")
    parser_zone.add_argument("--save", metavar="FIGURE_PATH_PNG", help="Save figure (png) to provided path")
    parser_zone.add_argument("--no-grid", action='store_true', help="Remove grid from figure")
    parser_zone.add_argument("--scale-factor", type=float, metavar="SCALE_FACTOR", help="Factor by which to multiply the size of the zone")
    parser_zone.add_argument("--debug", action='store_true', help='Show full error messages')
    parser_zone.set_defaults(func=show_zone_f)

    # Command: show-turbine (to show the powerct curve and properties of turbine n)
    parser_turbine = subparsers.add_parser("show-turbine", help="\033[94mDisplay power/ct curve of turbine\033[0m")
    parser_turbine.add_argument("turbine_id", type=int, metavar="TURBINE_ID", help="\033[94mId of the turbine\033[0m")
    parser_turbine.add_argument("--save", metavar="FIGURE_PATH_PNG", help="Save figure (png) to provided path")
    parser_turbine.add_argument("--debug", action='store_true', help='Show full error messages')
    parser_turbine.set_defaults(func=show_turbine_f)

    # Command: show-elevation (to show the elevation function in 3D)
    parser_elevation = subparsers.add_parser("show-elevation", help="\033[94mDisplay elevation function\033[0m")
    parser_elevation.add_argument("function_id", type=int, metavar="FUNCTION_ID", help="\033[94mId of the elevation function\033[0m")
    parser_elevation.add_argument("--limits", type=float ,nargs=4, metavar=('X_LOW', 'Y_LOW', 'X_HIGH', 'Y_HIGH'), help="\033[94mDomain over which to plot the function\033[0m")
    parser_elevation.add_argument("--save", metavar="FIGURE_PATH_PNG", help="Save figure (png) to provided path")
    parser_elevation.add_argument("--debug", action='store_true', help='Show full error messages')
    parser_elevation.set_defaults(func=show_elevation_f)

    # Command: instance-info (show details about an instance)
    parser_instance = subparsers.add_parser("instance-info", help="\033[94mShow information about an instance\033[0m")
    parser_instance.add_argument("instance_id", type=int, metavar='INSTANCE', help="\033[94mInstance id\033[0m")
    parser_instance.add_argument("--debug", action='store_true', help='Show full error messages')
    parser_instance.set_defaults(func=instance_info_f)

    # Command : check
    parser_check = subparsers.add_parser("check", help='\033[94mValidate output\033[0m')
    parser_check.add_argument("--debug", action='store_true', help='Show full error messages')
    parser_check.set_defaults(func=check_f)

    # Command: start server
    parser_server = subparsers.add_parser("serve", help="\033[94mStart server\033[0m")
    parser_server.add_argument("--port", type=int, metavar="PORT", help="Port number")
    parser_server.add_argument("--debug", action='store_true', help='Show full error messages')
    parser_server.set_defaults(func=start_server_f)

    # Command : stop server
    parser_server = subparsers.add_parser("shutdown", help="\033[94mStop server\033[0m")
    parser_server.add_argument("--port", type=int, metavar="PORT", help="Port number")
    parser_server.add_argument("--debug", action='store_true', help='Show full error messages')
    parser_server.set_defaults(func=shutdown_server_f)

    return parser