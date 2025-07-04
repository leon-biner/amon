import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import csv

from amon.src.utils import AMON_HOME, getPoint, getPath, getFunctionFromFile


def showWindrose(args):
    from windrose import WindroseAxes
    wind_data_path = AMON_HOME / 'data' / 'wind_data' / f'wind_data_{args.wind_data_id}'
    
    if not wind_data_path.exists():
        raise ValueError(f"\033[91mError\033[0m: Windrose {args.wind_data_id} does not exist, choose from 1 to 4")

    wind_speed_path     = wind_data_path / 'wind_speed.csv'
    wind_direction_path = wind_data_path / 'wind_direction.csv'
    save_filepath = getPath(args.save) # Ici, si le path exact n'est pas bon, il renvoie une erreur. Est-ce mieux de créer les dossiers s'ils n'existent pas?

    title = f"Wind Rose for Wind Data {args.wind_data_id} (%)"
    WS = pd.read_csv(wind_speed_path, index_col=0)
    WD = pd.read_csv(wind_direction_path, index_col=0)
    ax = WindroseAxes.from_ax()
    WD_values = [WD.values[i][0] for i in range (len(WD.values))]
    WS_values = [WS.values[i][0] for i in range (len(WS.values))]
    ax.bar(WD_values, WS_values, normed=True, opening=0.8, edgecolor="white")

    ax.set_legend(
    title="Wind speed (m/s)",
    bbox_to_anchor=(0.11, 0.11),
    loc='upper right',
    )

    if save_filepath:
        plt.savefig(save_filepath, dpi=130)
    plt.title(title)
    plt.show()


def showZone(args):
    import geopandas as gpd
    import shapefile
    import shapely

    zone_path = AMON_HOME / 'data' / 'zones' / f'zone_{args.zone_id}'
    
    if not zone_path.exists():
        raise ValueError(f"\033[91mError\033[0m: Zone {args.zone_id} does not exist, choose from 1 to 5")

    boundary_zone_path  = zone_path / 'boundary_zone.shp'
    exclusion_zone_path = zone_path / 'exclusion_zone.shp'
    point_filepath = getPath(args.point)
    save_filepath  = getPath(args.save)

    title = f"Zone {args.zone_id}" 

    boundary_zone_content = shapefile.Reader(boundary_zone_path)
    exclusion_zone_content = shapefile.Reader(exclusion_zone_path) if exclusion_zone_path.is_file() else None

    if args.scale_factor == None:
        args.scale_factor = 1

    boundary_zone          = []
    exclusion_zone         = []
    for shape in boundary_zone_content.shapes():
        coords = np.array(shape.points).T*args.scale_factor
        boundary_zone.append(shapely.Polygon(coords.T))

    if exclusion_zone_content:
        for shape in exclusion_zone_content.shapes():
            coords = np.array(shape.points).T*args.scale_factor
            exclusion_zone.append(shapely.Polygon(coords.T))
        

    point = getPoint(point_filepath, None)
    if point:
        x, y = [float(x) for x in point['coords'][0::2]], [float(y) for y in point['coords'][1::2]]
    else:
        x, y = None, None

    ax = plt.subplots()[1]
    boundary_filled = gpd.GeoSeries(boundary_zone)
    boundary = boundary_filled.boundary
    buildable_zone = boundary_filled
    ax.set_facecolor("lightsteelblue")

    if exclusion_zone != []:
        exclusion_zone_filled = gpd.GeoSeries(exclusion_zone)
        boundary_filled_index = gpd.GeoSeries(boundary_zone*len(exclusion_zone)).boundary
        exclusion_zone = exclusion_zone_filled.boundary
        for polygon in exclusion_zone_filled:
            buildable_zone = buildable_zone.difference(polygon)
            null_zone_boundaries = boundary_filled_index.intersection(exclusion_zone_filled)
        buildable_zone.plot(ax=ax, color='lightgreen', alpha=0.5, zorder=1)
        exclusion_zone_filled.plot(ax=ax, color=['gainsboro']*len(exclusion_zone), zorder=3)
        exclusion_zone.plot(ax=ax, color=['darkgrey']*len(exclusion_zone), hatch="///", linewidths=1, zorder=5)
        null_zone_boundaries.plot(ax=ax, color=['darkgreen']*len(exclusion_zone), linestyle='dashed', linewidths=1, zorder=4)
        ax.scatter(x, y, marker="o", s=40, color='red', linewidths=1, alpha=0.5, zorder=6, label='Wind Turbine' if point_filepath is not None else None)
    else:
        buildable_zone.plot(ax=ax, color='lightgreen', alpha=0.5, zorder=1)
        ax.scatter(x, y, marker="o", s=40, color='red', linewidths=1, alpha=0.5, zorder=3, label='Wind Turbine' if point_filepath is not None else None)
    
    if isinstance(boundary_zone, list): 
        boundary.plot(ax=ax, color=['darkgreen']*len(boundary_zone), linewidths=1, zorder=2)
    else:
        boundary.plot(ax=ax, color=['darkgreen'], linewidths=1, zorder=2)

    plt.title(title)
    plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment='right')
    if not args.no_grid:
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

        xticks = ax.get_xticks()
        yticks = ax.get_yticks()
        for x in xticks:
            ax.axvline(x=x, color='gray', linestyle='--', linewidth=0.5, zorder=100)
        for y in yticks:
            ax.axhline(y=y, color='gray', linestyle='--', linewidth=0.5, zorder=100)

        ax.set_xlim(xlim)
        ax.set_ylim(ylim)

    plt.xlabel("x [m]")
    plt.ylabel("y [m]")
    if point_filepath:
        ax.legend(loc='lower left')
    if save_filepath:
        plt.savefig(save_filepath)
    plt.show()


def showTurbine(args):
    turbine_path = AMON_HOME / 'data' / 'wind_turbines' / f'wind_turbine_{args.turbine_id}'
    if not turbine_path.exists():
        raise ValueError(f"\033[91mError\033[0m: Turbine {args.turbine_id} does not exist")
    save_filepath = getPath(args.save)

    with open(turbine_path / 'powerct_curve.csv', 'r') as f:
        reader = csv.DictReader(f)
        power_values, ct_values, windspeed_values = [], [], []
        for row in reader:
            windspeed_values.append(float(row['WindSpeed[m/s]']))
            power_values.append(float(row['Power[MW]']))
            ct_values.append(float(row['Ct']))

    with open(turbine_path / 'properties.csv', 'r') as f:
        props = next(csv.DictReader(f))
    name = props['name']
    diameter = props['diameter[m]']
    hub_height = props['hub_height[m]']


    fig, ax1 = plt.subplots()
    ax1.set_xlabel('Wind Speed [m/s]')
    ax1.set_ylabel('Power [MW]', color='tab:blue')
    line_1 = ax1.plot(windspeed_values, power_values, label='Power [MW]', color='tab:blue')[0]
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    plt.grid()

    ax2 = ax1.twinx()
    ax2.set_ylabel('Ct', color='orange')
    line_2 = ax2.plot(windspeed_values, ct_values, label='Ct', color='orange', linestyle='dashdot')[0]
    ax2.tick_params(axis='y', labelcolor='orange')

    plt.title(f'{name} - Power and Ct vs Wind Speed\nDiameter = {diameter}m, Hub Height = {hub_height}m')
    fig.tight_layout()
    fig.legend([line_1, line_2], ['Power [MW]', 'Ct'])

    if save_filepath:
        plt.savefig(save_filepath)
    plt.show()

def showElevation(args):
    data_filepath = AMON_HOME / 'data' / 'elevation_functions' / f'elevation_function_{args.function_id}.py'
    if not data_filepath.exists():
        raise ValueError(f"\033[91mError\033[0m: Elevation function {args.function_id} does not exist")
    elevation_function = getFunctionFromFile(data_filepath)

    if args.limits is not None:
        [lx, ly, ux, uy] = args.limits
    else:
        [lx, ly, ux, uy] = [-1000, -1000, 1000, 1000]
    x = np.arange(lx, ux, step=(ux-lx)/500)
    y = np.arange(ly, uy, step=(uy-ly)/500)
    X, Y = np.meshgrid(x, y)
    Z = np.array([[elevation_function(x, y) for x, y in zip(row_x, row_y)] for row_x, row_y in zip(X, Y)])
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.set_xlabel("X [m]")
    ax.set_ylabel("Y [m]")
    ax.set_zlabel("Elevation [m]")
    ax.plot_surface(X, Y, Z)
    plt.title(f"Elevation function {args.function_id}")
    plt.show()