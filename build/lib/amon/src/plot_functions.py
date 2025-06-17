import pandas as pd
import matplotlib.pyplot as plt

from amon.src.utils import AMON_HOME, getPoint, getPath


def showWindrose(args):
    print(f"Showing windrose for wind data {args.wind_data_id}, saving to {args.save}")

    wind_data_path = AMON_HOME / 'data' / 'wind_data' / f'wind_data_{args.wind_data_id}'

    wind_speed_path     = wind_data_path / 'wind_speed.csv'
    wind_direction_path = wind_data_path / 'wind_direction.csv'
    save_filepath = getPath(args.save) # Ici, si le path exact n'est pas bon, il renvoie une erreur. Est-ce mieux de créer les dossiers s'ils n'existent pas?

    plotWindRose(f"Wind Rose for Wind Data {args.wind_data_id} (%)", wind_speed_path, wind_direction_path, save_filepath)


def showTerrain(args):
    print(f"Showing terrain {args.zone_id} with point {args.point}, saving to {args.save}, not showing grid : {args.no_grid}, scale factor {args.scale_factor}")

    zone_path = AMON_HOME / 'data' / 'zones' / f'zone_{args.zone_id}'

    boundary_zone_path  = zone_path / 'boundary_zone.shp'
    exclusion_zone_path = zone_path / 'exclusion_zone.shp'
    point_filepath = getPath(args.point)
    save_filepath  = getPath(args.save)

    plotTerrain(f"Terrain {args.zone_id}", boundary_zone_path, exclusion_zone_path, point_filepath, save_filepath, not args.no_grid, args.scale_factor)


def plotWindRose(title, wind_speed_path, wind_direction_path, save_filepath=None):
    from windrose import WindroseAxes
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



def plotTerrain(title, boundary_zone_path, exclusion_zone_path, point_filepath=None, save_filepath=None, grid=False, scale_factor=None):
    import numpy as np
    import geopandas as gpd
    import shapefile
    import shapely

    print(boundary_zone_path, exclusion_zone_path, point_filepath, scale_factor)
    boundary_zone_content = shapefile.Reader(boundary_zone_path)
    exclusion_zone_content = shapefile.Reader(exclusion_zone_path) if exclusion_zone_path.is_file() else None

    if scale_factor == None:
        scale_factor = 1

    boundary_zone          = []
    exclusion_zone         = []
    for shape in boundary_zone_content.shapes():
        coords = np.array(shape.points).T*scale_factor
        boundary_zone.append(shapely.Polygon(coords.T))

    if exclusion_zone_content:
        for shape in exclusion_zone_content.shapes():
            coords = np.array(shape.points).T*scale_factor
            exclusion_zone.append(shapely.Polygon(coords.T))
        

    # if point_filepath:
    x, y = getPoint(point_filepath)

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
    if grid:
        # Save current limits
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

        xticks = ax.get_xticks()
        yticks = ax.get_yticks()
        for x in xticks:
            ax.axvline(x=x, color='gray', linestyle='--', linewidth=0.5, zorder=100)
        for y in yticks:
            ax.axhline(y=y, color='gray', linestyle='--', linewidth=0.5, zorder=100)

        # Restore original limits
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)

    # if grid:
        # ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='black')
    plt.xlabel("x (m)")
    plt.ylabel("y (m)")
    if point_filepath:
        ax.legend(loc='lower left')
    if save_filepath:
        plt.savefig(save_filepath)
    plt.show()

