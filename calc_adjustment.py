"""Command line program for calculating QQ-scaling adjustment factors."""
import pdb
import argparse

import numpy as np
import xarray as xr
from xclim import sdba
import cmdline_provenance as cmdprov


def main(args):
    """Run the program."""
    
    ds_hist = xr.open_mfdataset(args.hist_files)
    da_hist = ds_hist[args.model_variable]
    start_hist, end_hist = args.hist_time_bounds
    da_hist_period = da_hist.sel({'time': slice(start_hist, end_hist)})
    da_hist_period = da_hist_period.chunk({'time': -1})
    # TODO: check/fix units

    ds_fut = xr.open_mfdataset(args.fut_files)
    da_fut = ds_fut[args.model_variable]
    start_fut, end_fut = args.fut_time_bounds
    da_fut_period = da_fut.sel({'time': slice(start_fut, end_fut)})
    da_fut_period = da_fut_period.chunk({'time': -1})
    # TODO: check/fit units

    qm = sdba.EmpiricalQuantileMapping.train(
        da_fut,
        da_hist,
        nquantiles=100,
        group="time.month",
        kind="+"
    )
    qm.ds = qm.ds.assign_coords({'lat': da_fut['lat'], 'lon': da_fut['lon']}) #xclim strips lat/lon attributes
    qm.ds = qm.ds.transpose('quantiles', 'month', 'lat', 'lon')

    qm.ds.attrs['history'] = cmdprov.new_log()
    qm.ds.to_netcdf(args.output_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        argument_default=argparse.SUPPRESS,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
                                     
    parser.add_argument(
        "model_variable", type=str, help="model variable to process"
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

    args = parser.parse_args()
    main(args)
