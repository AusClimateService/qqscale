"""Command line program for applying QQ-scaling adjustment factors."""

import logging
import argparse

import numpy as np
import xarray as xr
import xclim as xc
from xclim import sdba
import dask.diagnostics

import utils


def adjust(
    ds,
    var,
    ds_adjust,
    spatial_grid='input',
    interp='nearest',
    ssr=False,
    ref_time=False,
    output_tslice=None
):
    """Apply qq-scale adjustment factors.

    Parameters
    ----------
    ds : xarray Dataset
        Data to be adjusted
    var : str
        Variable to be adjusted (i.e. in ds)
    ds_adjust : xarray Dataset
        Adjustment factors calculated using train.train
    spatial_grid : {'input', 'af'}, default 'input'
        Spatial grid for output data (choices are input data or adjustment factor grid)
    interp : {'nearest', 'linear', 'cubic'}, default 'nearest'
        Method for interpolation of adjustment factors
    ssr : bool, default False
        Perform singularity stochastic removal
    ref_time : bool, default False
        Adjust the output time axis so it matches the reference data
    output_tslice : list, default None
        Return a time slice of the adjusted data
        Format: ['YYYY-MM-DD', 'YYYY-MM-DD'] 
        
    Returns
    -------
    xarray Dataset    
    """

    ds_adjust = ds_adjust[['af', 'hist_q']]
    af_units = ds_adjust['hist_q'].attrs['units']
    infile_units = ds[var].attrs['units']    
    assert infile_units == af_units, \
        f"input file units {infile_units} differ from adjustment factor units {af_units}"

    dims = ds[var].dims
    on_spatial_grid = ('lat' in dims) and ('lon' in dims)
    if on_spatial_grid:
        if len(ds_adjust['lat']) != len(ds['lat']):
            if spatial_grid == 'input':
                ds_adjust = utils.regrid(ds_adjust, ds)
            elif spatial_grid == 'af':
                ds = utils.regrid(ds, ds_adjust, variable=var)
        assert len(ds_adjust['lat']) == len(ds['lat'])
        assert len(ds_adjust['lon']) == len(ds['lon'])

    qm = sdba.QuantileDeltaMapping.from_dataset(ds_adjust)
    hist_q_shape = qm.ds['hist_q'].shape
    hist_q_chunksizes = qm.ds['hist_q'].chunksizes
    af_shape = qm.ds['af'].shape
    af_chunksizes = qm.ds['af'].chunksizes
    logging.info(f'hist_q array size: {hist_q_shape}')
    logging.info(f'hist_q chunk size: {hist_q_chunksizes}')
    logging.info(f'af array size: {af_shape}')
    logging.info(f'af chunk size: {af_chunksizes}')

    if ssr:
        da = utils.apply_ssr(ds[var])
    else:
        da = ds[var]

    qq = qm.adjust(da, extrapolation='constant', interp=interp)
    qq = qq.rename(var)
    if on_spatial_grid:
        qq = qq.transpose('lat', 'lon', ...)
    qq = qq.transpose('time', ...) 

    if ssr:
        qq = utils.reverse_ssr(qq)

    qq = qq.to_dataset()    
    if ref_time:
        new_start_date = ds_adjust.attrs['reference_period_start'] 
        time_adjustment = np.datetime64(new_start_date) - qq['time'][0]
        qq['time'] = qq['time'] + time_adjustment

    if output_tslice:
        start_date, end_date = output_tslice
        qq = qq.sel({'time': slice(start_date, end_date)}) 

    qq.attrs['xclim'] = qq[var].attrs['history']
    del qq[var].attrs['history']
    del qq[var].attrs['bias_adjustment']

    return qq


def main(args):
    """Run the program."""

    dask.diagnostics.ProgressBar().register()
    ds = utils.read_data(
        args.infiles,
        args.var,
        time_bounds=args.adjustment_tbounds,
        input_units=args.input_units,
        output_units=args.output_units,
        no_leap=args.no_leap,
    )
    ds_adjust = xr.open_dataset(args.adjustment_file)
    qq = adjust(
        ds,
        args.var,
        ds_adjust,
        spatial_grid=args.spatial_grid,
        interp=args.interp,
        ssr=args.ssr,
        ref_time=args.ref_time,
        output_tslice=args.output_tslice,
    )
    infile_logs = {
        args.adjustment_file: ds_adjust.attrs['history'],
        args.infiles[0]: ds.attrs['history'],
    }
    qq.attrs['history'] = utils.get_new_log(infile_logs=infile_logs)
    qq.to_netcdf(args.outfile, encoding={args.var: {'least_significant_digit': 2, 'zlib': True}})


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
        "--adjustment_tbounds",
        type=str,
        nargs=2,
        metavar=('START_DATE', 'END_DATE'),
        default=None,
        help="time bounds over which to calculate quantiles for adjustments [use YYYY-MM-DD format]"
    )
    parser.add_argument(
        "--output_tslice",
        type=str,
        nargs=2,
        metavar=('START_DATE', 'END_DATE'),
        default=None,
        help="return a time slice of the adjusted data [use YYYY-MM-DD format]"
    )
    parser.add_argument(
        "--ref_time",
        action="store_true",
        default=False,
        help='Shift output time axis to match reference dataset',
    )
    parser.add_argument(
        "--spatial_grid",
        type=str,
        choices=('input', 'af'),
        default='input',
        help="Spatial grid for output data (input data or adjustment factor grid)",
    )
    parser.add_argument(
        "--interp",
        type=str,
        choices=('nearest', 'linear', 'cubic'),
        default='nearest',
        help="Method for interpolation of adjustment factors",
    )
    parser.add_argument(
        "--ssr",
        action="store_true",
        default=False,
        help='Perform Singularity Stochastic Removal',
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help='Set logging level to INFO',
    )
    parser.add_argument(
        "--no_leap",
        action="store_true",
        default=False,
        help='Remove leap days',
    )
    args = parser.parse_args()
    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level)
    with dask.diagnostics.ResourceProfiler() as rprof:
        main(args)
    utils.profiling_stats(rprof)
