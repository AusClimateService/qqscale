"""Command line program for applying QQ-scaling adjustment factors."""

import logging
import argparse

import numpy as np
import xarray as xr
import xclim as xc
from xclim import sdba
import dask.diagnostics

import utils
import ssr


def adjust(ds, var, ds_adjust, da_q=None, reverse_ssr=False, ref_time=False, interp='linear'):
    """Apply qq-scale adjustment factors.

    Parameters
    ----------
    ds : xarray Dataset
        Data to be adjusted
    var : str
        Variable to be adjusted (i.e. in ds)
    ds_adjust : xarray Dataset
        Adjustment factors calculated using calc_adjustment.adjust
    da_q : xarray DataArray
        Replacement for the historical quantiles used to determine
        which adjustment factor to apply to each value in ds.
        Calculated using calc_quantiles.py
        (Typically observational quantiles for quantile delta change)
    reverse_ssr : bool, default False
        Reverse singularity stochastic removal after adjustment
    ref_time : bool, default False
        Adjust the output time axis so it matches the reference data
    interp : {'nearest', 'linear', 'cubic'}, default 'linear'
        Method for interpolation of adjustment factors
        
    Returns
    -------
    xarray Dataset    
    """

    ds_adjust = ds_adjust[['af', 'hist_q']]
    af_units = ds_adjust['hist_q'].attrs['units']
    infile_units = ds[var].attrs['units']    
    assert infile_units == af_units, \
        f"input file units {infile_units} differ from adjustment factor units {af_units}"

    if len(ds_adjust['lat']) != len(ds['lat']):
        ds_adjust = utils.regrid(ds_adjust, ds)

    if not type(da_q) == type(None):
        ds_adjust['hist_q'] = da_q
    q_units = ds_adjust['hist_q'].attrs['units']
    assert infile_units == q_units, \
        f"input file units {infile_units} differ from quantile units {q_units}"
   
    qm = sdba.EmpiricalQuantileMapping.from_dataset(ds_adjust)

    hist_q_shape = qm.ds['hist_q'].shape
    hist_q_chunksizes = qm.ds['hist_q'].chunksizes
    af_shape = qm.ds['af'].shape
    af_chunksizes = qm.ds['af'].chunksizes
    logging.info(f'hist_q array size: {hist_q_shape}')
    logging.info(f'hist_q chunk size: {hist_q_chunksizes}')
    logging.info(f'af array size: {af_shape}')
    logging.info(f'af chunk size: {af_chunksizes}')

    qq = qm.adjust(ds[var], extrapolation='constant', interp='nearest')
    qq = qq.rename(var)
    qq = qq.transpose('time', 'lat', 'lon') 

    if reverse_ssr:
        qq = ssr.reverse_ssr(qq)

    qq = qq.to_dataset()    
    if ref_time:
        new_start_date = ds_adjust.attrs['reference_period_start'] 
        time_adjustment = np.datetime64(new_start_date) - qq['time'][0]
        qq['time'] = qq['time'] + time_adjustment
    qq.attrs['xclim_version'] = xc.__version__

    return qq


def main(args):
    """Run the program."""

    dask.diagnostics.ProgressBar().register()
    ds = utils.read_data(
        args.infiles,
        args.var,
        time_bounds=args.time_bounds,
        input_units=args.input_units,
        output_units=args.output_units,
    )
    ds_adjust = xr.open_dataset(args.adjustment_file)
    ds_adjust = ds_adjust[['af', 'hist_q']]
    if args.reference_quantile_file:
        ds_q = xr.open_dataset(args.reference_quantile_file)
        da_q = ds_q[args.reference_quantile_var]
    else:
        da_q = None
    qq = adjust(
        ds, args.var, ds_adjust, da_q=da_q, reverse_ssr=args.ssr, ref_time=args.ref_time
    )
    infile_logs = {
        args.adjustment_file: ds_adjust.attrs['history'],
        args.infiles[0]: ds.attrs['history'],
    }
    qq.attrs['history'] = utils.get_new_log(infile_logs=infile_logs)
    qq.to_netcdf(args.outfile)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        argument_default=argparse.SUPPRESS,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
                          
    parser.add_argument("infiles", type=str, nargs='*', help="input data (to be adjusted)")           
    parser.add_argument("var", type=str, help="variable to process")
    parser.add_argument("adjustment_file", type=str, help="adjustment factor file")
    parser.add_argument("outfile", type=str, help="output file")

    parser.add_argument("--input_units", type=str, default=None, help="input data units")
    parser.add_argument("--output_units", type=str, default=None, help="output data units")
    parser.add_argument(
        "--time_bounds",
        type=str,
        nargs=2,
        metavar=('START_DATE', 'END_DATE'),
        default=None,
        help="time bounds in YYYY-MM-DD format"
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
        help='Reverse Singularity Stochastic Removal when writing outfile',
    )
    parser.add_argument(
        "--reference_quantile_file",
        type=str,
        default=None,
        help="quantile file to refer for adjustment factor mapping",
    )
    parser.add_argument(
        "--reference_quantile_var",
        type=str,
        default=None,
        help="quantile file variable",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help='Set logging level to INFO',
    )
    args = parser.parse_args()
    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level)
    with dask.diagnostics.ResourceProfiler() as rprof:
        main(args)
    utils.profiling_stats(rprof)
