"""Command line program for calculating QQ-scaling adjustment factors."""

import argparse

import numpy as np
import xarray as xr
import xclim as xc
from xclim import sdba
import cmdline_provenance as cmdprov


def read_data(infiles, var, time_bounds, input_units, output_units):
    """Read and process a multi-file dataset."""

    ds = xr.open_mfdataset(infiles)
    try:
        ds = ds.drop('height')
    except ValueError:
        pass
    da = ds[var]
    start_date, end_date = time_bounds
    da_period = da.sel({'time': slice(start_date, end_date)})
    da_period = da_period.chunk({'time': -1})
    if input_units:
        da_period.attrs['units'] = input_units
    if output_units:
        da_period = xc.units.convert_units_to(da_period, output_units)

    return da_period
     

def main(args):
    """Run the program."""
    
    da_hist = read_data(
        args.hist_files,
        args.variable,
        args.hist_time_bounds,
        args.input_units,
        args.output_units
    )
    da_fut = read_data(
        args.fut_files,
        args.variable,
        args.fut_time_bounds,
        args.input_units,
        args.output_units
    )

    mapping_methods = {'additive': '+', 'multiplicative': '*'}
    qm = sdba.EmpiricalQuantileMapping.train(
        da_fut,
        da_hist,
        nquantiles=100,
        group="time.month",
        kind=mapping_methods[args.method]
    )
    qm.ds = qm.ds.assign_coords({'lat': da_fut['lat'], 'lon': da_fut['lon']}) #xclim strips lat/lon attributes
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

    args = parser.parse_args()
    main(args)
