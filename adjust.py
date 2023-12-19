"""Command line program for applying QQ-scaling adjustment factors."""

import logging
import argparse
from datetime import datetime
from contextlib import suppress

import numpy as np
import xarray as xr
import xclim as xc
from xclim import sdba
import dask.diagnostics

import utils


def apply_cordex_attributes(ds, var, input_attrs, scaling, obs_dataset, bc_period, spatial_grid):
    """Apply file attributes defined for bias adjusted CORDEX simulations.

    Source: http://is-enes-data.github.io/CORDEX_adjust_drs.pdf
    """

    # Variable attributes
    ds[var].attrs['long_name'] = 'Bias-Adjusted ' + ds[var].attrs['long_name']
    with suppress(KeyError):
        del ds[var].attrs['cell_methods']

    # Input global attributes to keep
    keep_attrs = [
        'driving_model_id',
        'driving_model_ensemble_member',
        'driving_experiment_name',
        'experiment_id',
        'rcm_version_id',
        'model_id'
    ]
    for attr in keep_attrs:
        with suppress(KeyError):
            ds.attrs[attr] = input_attrs[attr]
    if spatial_grid == 'input':
       with suppress(KeyError):
           ds.attrs['CORDEX_domain'] = input_attrs['CORDEX_domain']
    elif obs_dataset == 'AGCD':
       ds.attrs['CORDEX_domain'] = 'AUS-05i'

    # Input global attributes to modify/overwrite
    ds.attrs['product'] = 'bias-adjusted-output'
    ds.attrs['project_id'] = 'CORDEX-Adjust'
    ds.attrs['contact'] = 'damien.irving@csiro.au'
    ds.attrs['institution'] = 'Australian Climate Service'
    ds.attrs['institute_id'] = 'ACS'
    ds.attrs['creation_date'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    ds.attrs['tracking_id'] = 'unknown'

    # New global attributes
    bc_info = 'https://github.com/climate-innovation-hub/qqscale/blob/master/docs/method_ecdfm.md' 
    if scaling == 'additive':
        bc_name = 'Equidistant CDF Matching'
        bc_reference = 'Li H, Sheffield J, & Wood EF (2010). Bias correction of monthly precipitation and temperature fields from Intergovernmental Panel on Climate Change AR4 models using equidistant quantile matching. Journal of Geophysical Research, 115(D10), D10101. https://doi.org/10.1029/2009JD012882'
    elif scaling == 'multiplicative':
        bc_name = 'Equiratio CDF Matching'
        bc_reference = 'Wang L, & Chen W (2014). Equiratio cumulative distribution function matching as an improvement to the equidistant approach in bias correction of precipitation. Atmospheric Science Letters, 15(1), 1–6. https://doi.org/10.1002/asl2.454'
    ds.attrs['bc_method'] = f'{bc_name}; {bc_info}; {bc_reference}'
    ds.attrs['bc_method_id'] = 'ecdfm'
    if obs_dataset == 'AGCD':
        ds.attrs['bc_observation'] = 'Australian Gridded Climate Data, version 1-0-1; https://dx.doi.org/10.25914/hjqj-0x55; Jones D, Wang W, & Fawcett R (2009). High-quality spatial climate datasets for Australia. Australian Meteorological and Oceanographic Journal, 58, 233-248. http://www.bom.gov.au/jshess/docs/2009/jones_hres.pdf'
        ds.attrs['bc_observation_id'] = 'AGCD'
    else:
        raise ValueError('Unrecognised obs dataset: {obs_dataset}')
    ds.attrs['bc_period'] = bc_period 
    ds.attrs['bc_info'] = f'ecdfm-{obs_dataset}-{bc_period}'
    ds.attrs['bc_period'] = bc_period 
    ds.attrs['bc_info'] = f'ecdfm-{obs_dataset}-{bc_period}'    
    #ds.attrs['input_tracking_id'] = input_attrs['tracking_id']

    return ds


def adjust(
    ds,
    var,
    ds_adjust,
    spatial_grid='input',
    interp='nearest',
    ssr=False,
    max_af=None,
    ref_time=False,
    valid_min=None,
    valid_max=None,
    output_tslice=None,
    cordex_attrs=None,
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
    max_af : float, optional
        Maximum limit for adjustment factors
    ref_time : bool, default False
        Adjust the output time axis so it matches the reference data
    valid_min : float
        Minimum valid value (input and output data is clipped to this value)
    valid_max : float
        Maximum valid value (input and output data is clipped to this value)
    output_tslice : list, default None
        Return a time slice of the adjusted data
        Format: ['YYYY-MM-DD', 'YYYY-MM-DD']
    cordex_attrs : {'AGCD'}, optional
        Apply file attributes defined for bias adjusted CORDEX simulations for a given obs dataset
        
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
                logging.info('Regridding adjustment factors to input data grid')
                ds_adjust = utils.regrid(ds_adjust, ds)
            elif spatial_grid == 'af':
                logging.info('Regridding input data to adjustment factor grid')
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

    if max_af:
        ds_adjust['af'] = ds_adjust['af'].where(ds_adjust['af'] < max_af, max_af)

    qq = qm.adjust(da, extrapolation='constant', interp=interp)
    qq = qq.rename(var)
    if on_spatial_grid:
        qq['lat'] = ds['lat']
        qq['lon'] = ds['lon']
        qq = qq.transpose('lat', 'lon', ...)
    qq = qq.transpose('time', ...) 

    if ssr:
        qq = utils.reverse_ssr(qq)
        
    if (valid_min is not None) or (valid_max is not None):
        qq = qq.clip(min=valid_min, max=valid_max, keep_attrs=True) 

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
    if cordex_attrs:
        ref_start = ds_adjust.attrs['reference_period_start'][0:4]
        ref_end = ds_adjust.attrs['reference_period_end'][0:4]
        bc_period = f'{ref_start}-{ref_end}'
        scaling = 'additive' if '+' in qq.attrs['xclim'] else 'multiplicative'
        obs_dataset = cordex_attrs
        qq = apply_cordex_attributes(qq, var, ds.attrs, scaling, obs_dataset, bc_period, spatial_grid)

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
        use_cftime=False,
        valid_min=args.valid_min,
        valid_max=args.valid_max,
    )
    ds_adjust = xr.open_dataset(args.adjustment_file)
    qq = adjust(
        ds,
        args.var,
        ds_adjust,
        spatial_grid=args.spatial_grid,
        interp=args.interp,
        ssr=args.ssr,
        max_af=args.max_af,
        ref_time=args.ref_time,
        valid_min=args.valid_min,
        valid_max=args.valid_max,
        output_tslice=args.output_tslice,
        cordex_attrs=args.cordex_attrs,
    )
    infile_logs = {}
    if 'history' in ds_adjust.attrs:
        infile_logs[args.adjustment_file] = ds_adjust.attrs['history']
    if 'history' in ds.attrs:
        infile_logs[args.infiles[0]] = ds.attrs['history']
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
        "--max_af",
        type=float,
        default=None,
        help="Maximum limit for adjustment factors",
    )
    parser.add_argument(
        "--ssr",
        action="store_true",
        default=False,
        help='Perform Singularity Stochastic Removal',
    )
    parser.add_argument(
        "--valid_min",
        type=float,
        default=None,
        help="Minimum valid value",
    )
    parser.add_argument(
        "--valid_max",
        type=float,
        default=None,
        help="Maximum valid value",
    )
    parser.add_argument(
        "--cordex_attrs",
        type=str,
        choices=('AGCD'),
        default=None,
        help='Apply attributes defined for bias adjusted CORDEX simulations for given obs dataset',
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
