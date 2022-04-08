"""Command line program for QQ-scaling."""

import argparse

import numpy as np
import xarray as xr
import cmdline_provenance as cmdprov

import qqscale


def main(args):
    """Run the program."""

    ds_obs = xr.open_mfdataset(args.obs_files)
    da_obs = ds_obs[args.obs_variable]
    da_obs_period = da_obs.sel({'time': slice(args.obs_time_bounds)})
    
    ds_hist = xr.open_mfdataset(args.hist_files)
    da_hist = ds_hist[args.model_variable]
    da_hist_period = da_hist.sel({'time': slice(args.hist_time_bounds)})

    ds_fut = xr.open_mfdataset(args.fut_files)
    da_fut = ds_fut[args.model_variable]
    da_fut_period = da_fut.sel({'time': slice(args.fut_time_bounds)})

    ds_qqscale = qqscale.qqscale(
        da_obs_period, da_hist_period, da_fut_period, args.month, args.method
    )
    ds_qqscale.attrs["history"] = cmdprov.new_log()
    ds_qqscale.to_netcdf(args.output_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        argument_default=argparse.SUPPRESS,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
                                     
    parser.add_argument(
        "obs_files", type=str, nargs='*', help="observational data files"
    )
    parser.add_argument(
        "obs_variable", type=str, help="observational variable to process"
    )
    parser.add_argument(
        "model_variable", type=str, help="model variable to process"
    )
    parser.add_argument(
        "month", type=int, choices=np.arange(1, 13), help="month to process"
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
        "--obs_time_bounds",
        type=str,
        nargs=2,
        metavar=('START_DATE', 'END_DATE'),
        required=True,
        help="observations time bounds in YYYY-MM-DD format"
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
