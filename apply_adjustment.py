"""Command line program for applying QQ-scaling adjustment factors."""
import pdb
import argparse

import numpy as np
import xarray as xr
from xclim import sdba
import xesmf as xe
import cmdline_provenance as cmdprov


def main(args):
    """Run the program."""

    ds_obs = xr.open_mfdataset(args.obs_files)
    start_obs, end_obs = args.obs_time_bounds
    ds_obs = da_obs.sel({'time': slice(start_obs, end_obs)})
    ds_obs = ds_obs.chunk({'time': -1})
    # TODO: Check units

    ds_adjust = xr.open_dataset(args.adjustment_file)
    qm = sdba.QuantileDeltaMapping.from_dataset(ds)
    regridder = xe.Regridder(qm.ds, ds_obs, "bilinear")
    qm.ds = regridder(qm.ds)
    qm.ds = qm.ds.compute()

    if args.lon_selection:
        start_index, end_index = args.lon_selection
        ds_obs = ds_obs.isel({'lon': slice(start_index, end_index)})
        qm.ds = qm.ds.isel({'lon': slice(start_index, end_index)}) 

    qq_obs = qm.adjust(
        ds_obs[args.variable],
        extrapolation="constant",
        interp="linear"
    )
    qq_obs = qq_obs.rename(args.variable)
    qq_obs = qq_obs.transpose('time', 'lat', 'lon')

    qq_obs.attrs['history'] = cmdprov.new_log(
        infile_logs={args.adjustment_file: qm.ds.attrs['history']},
    )
    qq_obs.to_netcdf(args.output_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        argument_default=argparse.SUPPRESS,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
                          
    parser.add_argument(
        "obs_files", type=str, nargs='*', help="observation data"
    )           
    parser.add_argument(
        "variable", type=str, help="model variable to process"
    )
    parser.add_argument(
        "adjustment_file", type=str, help="adjustment factor file"
    )
    parser.add_argument("output_file", type=str, help="output file")

    parser.add_argument(
        "--lon_selection",
        type=int,
        nargs=2,
        metavar=('START_INDEX', 'END_INDEX'),
        default=None,
        help="take a subset of the data using a longitude selection"
    )
    parser.add_argument(
        "--time_bounds",
        type=str,
        nargs=2,
        metavar=('START_DATE', 'END_DATE'),
        required=True,
        help="observations time bounds in YYYY-MM-DD format"
    )

    args = parser.parse_args()
    main(args)
