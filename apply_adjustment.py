"""Command line program for applying QQ-scaling adjustment factors."""

import logging
import argparse

import git
import numpy as np
import xarray as xr
import xclim as xc
from xclim import sdba
import xesmf as xe
import cmdline_provenance as cmdprov
import dask.diagnostics

import calc_adjustment


def get_new_log(infile_name, infile_history):
    """Generate command log for output file."""

    try:
        repo = git.Repo()
        repo_url = repo.remotes[0].url.split(".git")[0]
    except (git.exc.InvalidGitRepositoryError, NameError):
        repo_url = None
    new_log = cmdprov.new_log(
        infile_logs={infile_name: infile_history},
        code_url=repo_url,
    )

    return new_log


def profiling_stats(rprof):
    """Record profiling information."""

    max_memory = np.max([result.mem for result in rprof.results])
    max_cpus = np.max([result.cpu for result in rprof.results])

    logging.info(f'Peak memory usage: {max_memory}MB')
    logging.info(f'Peak CPU usage: {max_cpus}%')


def main(args):
    """Run the program."""

    dask.diagnostics.ProgressBar().register()

    ds = calc_adjustment.read_data(
        args.infiles,
        args.var,
        time_bounds=args.time_bounds,
        input_units=args.input_units,
        output_units=args.output_units,
        ssr=args.ssr,
    )
    ds_adjust = xr.open_dataset(args.adjustment_file)
    ds_adjust = ds_adjust[['af', 'hist_q']]
    assert ds_adjust['af'].attrs['units'] == ds[args.variable].attrs['units']     
    ds_adjust = ds_adjust.where(ds_adjust.apply(np.isfinite), 0.0)
    qm = sdba.QuantileDeltaMapping.from_dataset(ds_adjust)

    if len(ds_adjust['lat']) != len(ds['lat']):
        regridder = xe.Regridder(qm.ds, ds, "bilinear")
        qm.ds = regridder(qm.ds)

    hist_q_shape = qm.ds['hist_q'].shape
    hist_q_chunksizes = qm.ds['hist_q'].chunksizes
    af_shape = qm.ds['af'].shape
    af_chunksizes = qm.ds['af'].chunksizes
    logging.info(f'hist_q array size: {hist_q_shape}')
    logging.info(f'hist_q chunk size: {hist_q_chunksizes}')
    logging.info(f'af array size: {af_shape}')
    logging.info(f'af chunk size: {af_chunksizes}')

    qq = qm.adjust(ds[args.var], extrapolation="constant", interp="linear")
    qq = qq.rename(args.var)
    qq = qq.transpose('time', 'lat', 'lon')
    if ssr:
        qq[args.var] = qq[args.var].where(qq[args.var] >= 8.64e-4, 0.0)
    
    if args.ref_time:
        new_start_date = ds_adjust.attrs['reference_period_start'] 
        time_adjustment = np.datetime64(new_start_date) - qq['time'][0]
        qq['time'] = qq['time'] + time_adjustment

    qq.attrs['history'] = get_new_log(args.adjustment_file, ds_adjust.attrs['history'])
    qq.to_netcdf(args.output_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        argument_default=argparse.SUPPRESS,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
                          
    parser.add_argument("infiles", type=str, nargs='*', help="input data (to be adjusted)")           
    parser.add_argument("var", type=str, help="variable to process")
    parser.add_argument("adjustment_file", type=str, help="adjustment factor file")
    parser.add_argument("output_file", type=str, help="output file")

    parser.add_argument("--input_units", type=str, default=None, help="input data units")
    parser.add_argument("--output_units", type=str, default=None, help="output data units")
    parser.add_argument(
        "--time_bounds",
        type=str,
        nargs=2,
        metavar=('START_DATE', 'END_DATE'),
        required=True,
        help="time bounds in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help='Set logging level to DEBUG',
    )
    parser.add_argument(
        "--ref_time",
        action="store_true",
        default=False,
        help='Shift output time axis to match reference dataset',
    )
    parser.add_argument(
        "--ssr",
        action="store_true",
        default=False,
        help='Adjustment factors used Singularity Stochastic Removal',
    )
    args = parser.parse_args()
    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level)
    with dask.diagnostics.ResourceProfiler() as rprof:
        main(args)
    profiling_stats(rprof)
