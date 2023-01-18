"""Command line program for applying QQ-scaling adjustment factors."""

import logging
import argparse

import numpy as np
import xarray as xr
import xclim as xc
from xclim import sdba
import dask.diagnostics

import utils


def match_mean(da_qq, da_target, ref_clim, hist_clim, scaling):
    """Adjust QQ-scaled data so change in annual mean matches hist to ref change.
    
    Used in quantile delta change methods to make sure the change in the annual mean
      between a historical (hist_clim) and future (ref_clim) model simulation
      matches the change between the original observational data (da_target)
      and the QQ-scaled observational data (da_qq).
    
    Parameters
    ----------
    da_qq : xarray DataArray
        QQ-scaled data to be adjusted
    da_target : xarray DataArray
        Data prior to qq-scaling
    ref_clim : xarray DataArray
        Reference climatology
    hist_clim : xarray DataArray
        Historical climatology    
    scaling : {'additive', 'multiplicative'}
        Variable to restore attributes for
    
    Returns
    -------
    da_qq_adjusted : xarray DataArray
    
    """
    
    qq_clim = da_qq.mean('time', keep_attrs=True)
    target_clim = da_target.mean('time', keep_attrs=True)
    if scaling == 'multiplicative':
        adjustment_factor =  ((ref_clim / hist_clim) * target_clim) / qq_clim
        da_qq_adjusted = da_qq * adjustment_factor
    elif scaling == 'additive':
        adjustment_factor = (ref_clim - hist_clim) - (qq_clim - target_clim)
        da_qq_adjusted = da_qq + adjustment_factor
    else:
        raise ValueError(f'Invalid scaling method: {scaling}')
    da_qq_adjusted.attrs = da_qq.attrs

    return da_qq_adjusted


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
    infile_units = ds[args.var].attrs['units']
    
    ds_adjust = xr.open_dataset(args.adjustment_file)
    ds_adjust = ds_adjust[['af', 'hist_q']]

    af_units = ds_adjust['hist_q'].attrs['units']
    assert infile_units == af_units, \
        f"input file units {infile_units} differ from adjustment units {af_units}"

    if len(ds_adjust['lat']) != len(ds['lat']):
        if args.output_grid == 'infiles':
            ds_adjust = utils.regrid(ds_adjust, ds)
        elif args.output_grid == 'adjustment':
            ds = utils.regrid(ds, ds_adjust, variable=args.var)
        else:
            raise ValueError(f'Invalid requested output grid: {args.output_grid}')

    if args.reference_quantile_file:
        ds_q = utils.read_data(args.reference_quantile_file, args.var)
        ds_adjust['hist_q'] = ds_q[args.reference_quantile_var]

    mapping_methods = {'qm': sdba.EmpiricalQuantileMapping, 'qdm': sdba.QuantileDeltaMapping}
    qm = mapping_methods[args.mapping].from_dataset(ds_adjust)

    hist_q_shape = qm.ds['hist_q'].shape
    hist_q_chunksizes = qm.ds['hist_q'].chunksizes
    af_shape = qm.ds['af'].shape
    af_chunksizes = qm.ds['af'].chunksizes
    logging.info(f'hist_q array size: {hist_q_shape}')
    logging.info(f'hist_q chunk size: {hist_q_chunksizes}')
    logging.info(f'af array size: {af_shape}')
    logging.info(f'af chunk size: {af_chunksizes}')

    qq = qm.adjust(ds[args.var], extrapolation='constant', interp='linear')
    qq = qq.rename(args.var)
    qq = qq.transpose('time', 'lat', 'lon') 

    if args.match_mean:
        qq = match_mean(
            qq, ds[args.var], ds_adjust['ref_clim'], ds_adjust['hist_clim'], args.scaling
        )
    if args.ssr:
        qq = qq.where(qq >= 8.64e-4, 0.0)
    qq = qq.to_dataset()
    
    if args.ref_time:
        new_start_date = ds_adjust.attrs['reference_period_start'] 
        time_adjustment = np.datetime64(new_start_date) - qq['time'][0]
        qq['time'] = qq['time'] + time_adjustment

    infile_logs = {
        args.infiles[0]: ds.attrs['history'],
        args.adjustment_file: ds_adjust.attrs['history'],
    }
    qq.attrs['history'] = utils.get_new_log(infile_logs=infile_logs)
    qq.attrs['xclim_version'] = xc.__version__
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
    parser.add_argument("output_grid", type=str, choices=('infiles', 'adjustment'), help="output_grid")
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
        "--mapping",
        type=str,
        choices=('qm', 'qdm'),
        default='qm',
        help="mapping method (qm = empirical quantile mapping; qdm = quantile delta mapping)",
    )
    parser.add_argument(
        "--scaling",
        type=str,
        choices=('additive', 'multiplicative'),
        default='additive',
        help="scaling method",
    )
    parser.add_argument(
        "--ref_time",
        action="store_true",
        default=False,
        help='Shift output time axis to match reference dataset',
    )
    parser.add_argument(
        "--match_mean",
        action="store_true",
        default=False,
        help='Scale the QQ-scaled data so mean change matches the change between ref and hist',
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
