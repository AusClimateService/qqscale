"""Command line program for calculating QQ-scaling adjustment factors."""

import argparse
import logging

import xclim as xc
from xclim import sdba
import dask.diagnostics

import utils


def train(
    ds_hist,
    ds_ref,
    hist_var,
    ref_var,
    scaling,
    time_grouping=None,
    nquantiles=100,
    spatial_grid='hist',
    ssr=False
):
    """Calculate qq-scaling adjustment factors.

    Parameters
    ----------
    ds_hist : xarray Dataset
        Historical data
    ds_ref : xarray Dataset
        Reference data
    hist_var : str
        Historical variable (i.e. in ds_hist)
    ref_var : str
        Reference variable (i.e. in ds_ref)
    scaling : {'additive', 'multiplicative'}
        Scaling method
    time_grouping : {'monthly', '3monthly'} default None
        Time period grouping (default is no grouping)
    nquantiles : int, default 100
        Number of quantiles to process
    spatial_grid : {'hist', 'ref'}, default 'hist'
        Spatial grid for output data (hist or ref grid)
    ssr : bool, default False
        Perform singularity stochastic removal 
        
    Returns
    -------
    xarray Dataset
    """

    hist_units = ds_hist[hist_var].attrs['units']
    ref_units = ds_ref[ref_var].attrs['units']
    
    dims = ds_hist[hist_var].dims
    on_spatial_grid = ('lat' in dims) and ('lon' in dims)
    if on_spatial_grid:
        if len(ds_hist['lat']) != len(ds_ref['lat']):
            if spatial_grid == 'ref':
                ds_hist = utils.regrid(ds_hist, ds_ref, variable=hist_var)
                logging.info('Regridding hist data to ref grid')
                spatial_coords = {'lat': ds_ref['lat'], 'lon': ds_ref['lon']}
            elif spatial_grid == 'hist':
                ds_ref = utils.regrid(ds_ref, ds_hist, variable=ref_var)
                logging.info('Regridding ref data to hist grid')
                spatial_coords = {'lat': ds_hist['lat'], 'lon': ds_hist['lon']}
        else:
            spatial_coords = {'lat': ds_ref['lat'], 'lon': ds_ref['lon']}
        assert len(ds_hist['lat']) == len(ds_ref['lat'])
        assert len(ds_hist['lon']) == len(ds_ref['lon'])    

    scaling_methods = {'additive': '+', 'multiplicative': '*'}

    if time_grouping == 'monthly':
        group = 'time.month'
    elif time_grouping == '3monthly':
        group = sdba.Grouper('time.month', window=3)
    else:
        group = 'time'

    if ssr:
        da_ref = utils.apply_ssr(ds_ref[ref_var])
        da_hist = utils.apply_ssr(ds_hist[hist_var])
    else:
        da_ref = ds_ref[ref_var]
        da_hist = ds_hist[hist_var]

    qm = sdba.QuantileDeltaMapping.train(
        da_ref,
        da_hist,
        nquantiles=nquantiles,
        group=group,
        kind=scaling_methods[scaling]
    )
    qm.ds = qm.ds.squeeze()
    try:
        qm.ds = qm.ds.drop_vars('group')
    except ValueError:
        pass
    qm.ds['hist_q'].attrs['units'] = hist_units
    if on_spatial_grid:
        qm.ds = qm.ds.assign_coords(spatial_coords) #xclim strips lat/lon attributes
        qm.ds = qm.ds.transpose('lat', 'lon', ...)
    if 'month' in qm.ds.dims:
        qm.ds = qm.ds.transpose('month', ...)
    qm.ds = qm.ds.transpose('quantiles', ...)
    
    hist_times = ds_hist['time'].dt.strftime('%Y-%m-%d').values
    qm.ds.attrs['historical_period_start'] = hist_times[0]
    qm.ds.attrs['historical_period_end'] = hist_times[-1]
    ref_times = ds_ref['time'].dt.strftime('%Y-%m-%d').values
    qm.ds.attrs['reference_period_start'] = ref_times[0]
    qm.ds.attrs['reference_period_end'] = ref_times[-1]

    qm.ds.attrs['xclim_version'] = xc.__version__

    return qm.ds 


def main(args):
    """Run the program."""
    
    dask.diagnostics.ProgressBar().register()
    ds_hist = utils.read_data(
        args.hist_files,
        args.hist_var,
        time_bounds=args.hist_time_bounds,
        input_units=args.input_hist_units,
        output_units=args.output_units,
        valid_min=args.valid_min,
        valid_max=args.valid_max,
        drop_vars=args.hist_drop_vars,
    )
    calendar_hist = type(ds_hist['time'].values[0])
    ds_ref = utils.read_data(
        args.ref_files,
        args.ref_var,
        time_bounds=args.ref_time_bounds,
        lat_bounds=args.lat_bounds,
        lon_bounds=args.lon_bounds,
        input_units=args.input_ref_units,
        output_units=args.output_units,
        output_calendar=calendar_hist,
        valid_min=args.valid_min,
        valid_max=args.valid_max,
        drop_vars=args.ref_drop_vars,
    )
    ds_out = train(
        ds_hist,
        ds_ref,
        args.hist_var,
        args.ref_var,
        args.scaling,
        time_grouping=args.time_grouping,
        nquantiles=args.nquantiles,
        spatial_grid=args.spatial_grid,
        ssr=args.ssr,
    )

    if args.short_history:
        unique_dirnames = utils.get_unique_dirnames(args.hist_files + args.ref_files)
    else:
        unique_dirnames = []
    ds_out.attrs['history'] = utils.get_new_log(wildcard_prefixes=unique_dirnames)

    encoding = {}
    outfile_vars = list(ds_out.coords) + list(ds_out.keys())
    for outfile_var in outfile_vars:
        encoding[outfile_var] = {'_FillValue': None}
    if args.compress:
        encoding['af']['least_significant_digit'] = 2
        encoding['af']['zlib'] = True
        encoding['hist_q']['least_significant_digit'] = 2
        encoding['hist_q']['zlib'] = True
    ds_out.to_netcdf(args.output_file, encoding=encoding)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        argument_default=argparse.SUPPRESS,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )          
    parser.add_argument("hist_var", type=str, help="historical variable to process")
    parser.add_argument("ref_var", type=str, help="reference variable to process")
    parser.add_argument("output_file", type=str, help="output file")
    parser.add_argument(
        "--hist_files",
        type=str,
        nargs='*',
        required=True,
        help="historical data files"
    )
    parser.add_argument(
        "--ref_files",
        type=str,
        nargs='*',
        required=True,
        help="reference data files"
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
        "--ref_time_bounds",
        type=str,
        nargs=2,
        metavar=('START_DATE', 'END_DATE'),
        required=True,
        help="reference time bounds in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--lat_bounds",
        type=float,
        nargs=2,
        default=None,
        help='Latitude bounds for reference data: (south_bound, north_bound)',
    )
    parser.add_argument(
        "--lon_bounds",
        type=float,
        nargs=2,
        default=None,
        help='Longitude bounds for reference data: (west_bound, east_bound)',
    )
    parser.add_argument(
        "--nquantiles",
        type=int,
        default=100,
        help="Number of quantiles to process",
    )
    parser.add_argument(
        "--scaling",
        type=str,
        choices=('additive', 'multiplicative'),
        default='additive',
        help="scaling method",
    )
    parser.add_argument(
        "--time_grouping",
        type=str,
        choices=('monthly', '3monthly'),
        default=None,
        help="Time period grouping",
    )
    parser.add_argument(
        "--spatial_grid",
        type=str,
        choices=('hist', 'ref'),
        default='hist',
        help="Spatial grid for output data (hist or ref grid)",
    )
    parser.add_argument(
        "--input_hist_units",
        type=str,
        default=None,
        help="input historical data units"
    )
    parser.add_argument(
        "--input_ref_units",
        type=str,
        default=None,
        help="input reference data units"
    )
    parser.add_argument(
        "--output_units",
        type=str,
        default=None,
        help="output data units"
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
        "--ssr",
        action="store_true",
        default=False,
        help='Apply Singularity Stochastic Removal to input data',
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help='Set logging level to INFO',
    )
    parser.add_argument(
        "--compress",
        action="store_true",
        default=False,
        help="compress the output data file"
    )
    parser.add_argument(
        "--short_history",
        action='store_true',
        default=False,
        help="Use wildcards to shorten the file lists in output_file history attribute",
    )
    parser.add_argument(
        "--hist_drop_vars",
        type=str,
        nargs='*',
        default=[],
        help="File variables to drop when reading hist files"
    )
    parser.add_argument(
        "--ref_drop_vars",
        type=str,
        nargs='*',
        default=[],
        help="File variables to drop when reading ref files"
    )
    args = parser.parse_args()
    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level)
    with dask.diagnostics.ResourceProfiler() as rprof:
        main(args)
    utils.profiling_stats(rprof)
