"""Command line program for calculating QQ-scaling adjustment factors."""

import argparse

import numpy as np
import xarray as xr
import xclim as xc
from xclim import sdba
import cmdline_provenance as cmdprov

import spatial_selection


def read_data(
    infiles,
    var,
    time_bounds=None,
    spatial_sel=None,
    spatial_agg="none",
    input_units=None,
    output_units=None,
    lon_chunk_size=20,
):
    """Read and process a multi-file dataset."""

    ds = xr.open_mfdataset(infiles)
    try:
        ds = ds.drop('height')
    except ValueError:
        pass

    if time_bounds:
        start_date, end_date = time_bounds
        ds = ds.sel({'time': slice(start_date, end_date)})
    ds = ds.chunk({'time': -1, 'lon': lon_chunk_size})

    if spatial_sel is None:
        pass
    elif len(spatial_sel) == 4:
        ds = spatial_selection.select_box_region(ds, spatial_sel, agg=spatial_agg)
    elif len(spatial_sel) == 2:
        ds = spatial_selection.select_point_region(ds, spatial_sel)
    else:
        msg = "spatial sel must be None, a box (list of 4 floats) or a point (list of 2 floats)"
        raise ValueError(msg)

    if input_units:
        ds[var].attrs['units'] = input_units
    if output_units:
        ds[var] = xc.units.convert_units_to(ds[var], output_units)

    return ds
     

def main(args):
    """Run the program."""
    
    ds_hist = read_data(
        args.hist_files,
        args.variable,
        time_bounds=args.hist_time_bounds,
        input_units=args.input_units,
        output_units=args.output_units,
        lon_chunk_size=args.lon_chunk_size,
    )
    ds_fut = read_data(
        args.fut_files,
        args.variable,
        time_bounds=args.fut_time_bounds,
        input_units=args.input_units,
        output_units=args.output_units,
        lon_chunk_size=args.lon_chunk_size,
    )

    mapping_methods = {'additive': '+', 'multiplicative': '*'}
    qm = sdba.EmpiricalQuantileMapping.train(
        ds_fut[args.variable],
        ds_hist[args.variable],
        nquantiles=100,
        group="time.month",
        kind=mapping_methods[args.method]
    )
    qm.ds = qm.ds.assign_coords({'lat': ds_fut['lat'], 'lon': ds_fut['lon']}) #xclim strips lat/lon attributes
    qm.ds = qm.ds.transpose('quantiles', 'month', 'lat', 'lon')

    qm.ds.attrs['history'] = cmdprov.new_log()
    qm.ds.attrs['base_period_start'] = args.hist_time_bounds[0]
    qm.ds.attrs['base_period_end'] = args.hist_time_bounds[1]
    qm.ds.attrs['future_period_start'] =args.fut_time_bounds[0]
    qm.ds.attrs['future_period_end'] = args.fut_time_bounds[1]
    qm.ds.to_netcdf(args.output_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        argument_default=argparse.SUPPRESS,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
                                     
    parser.add_argument(
        "variable", type=str, help="model variable to process"
    )
    parser.add_argument("output_file", type=str, help="output file")

    parser.add_argument(
        "--hist_files",
        type=str,
        nargs='*',
        required=True,
        help="historical GCM data files"
    )
    parser.add_argument(
        "--fut_files",
        type=str,
        nargs='*',
        required=True,
        help="future GCM data files"
    )
    parser.add_argument(
        "--hist_time_bounds",
        type=str,
        nargs=2,
        metavar=('START_DATE', 'END_DATE'),
        required=True,
        help="historical time bounds in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--fut_time_bounds",
        type=str,
        nargs=2,
        metavar=('START_DATE', 'END_DATE'),
        required=True,
        help="future time bounds in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--method",
        type=str,
        choices=('additive', 'multiplicative'),
        default='additive',
        help="scaling method",
    )
    parser.add_argument(
        "--input_units", type=str, default=None, help="input data units"
    )
    parser.add_argument(
        "--output_units", type=str, default=None, help="output data units"
    )
    parser.add_argument(
        "--lon_chunk_size", type=int, default=-1, help="chunk size along the longitude axis"
    )

    args = parser.parse_args()
    main(args)
