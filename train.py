"""Command line program for calculating QQ-scaling adjustment factors."""

import argparse
import logging

import xclim as xc
from xclim import sdba
import dask.diagnostics

import utils


def train(ds_hist, ds_ref, hist_var, ref_var, scaling):
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
        
    Returns
    -------
    xarray Dataset
    """

    hist_units = ds_hist[hist_var].attrs['units']
    ref_units = ds_ref[ref_var].attrs['units']

    if len(ds_hist['lat']) != len(ds_ref['lat']):
        ds_hist = utils.regrid(ds_hist, ds_ref, variable=hist_var)
    
    scaling_methods = {'additive': '+', 'multiplicative': '*'}
    qm = sdba.EmpiricalQuantileMapping.train(
        ds_ref[ref_var],
        ds_hist[hist_var],
        nquantiles=100,
        group='time.month',
        kind=scaling_methods[scaling]
    )
    qm.ds['hist_q'].attrs['units'] = hist_units
    qm.ds = qm.ds.assign_coords({'lat': ds_ref['lat'], 'lon': ds_ref['lon']}) #xclim strips lat/lon attributes
    qm.ds = qm.ds.transpose('quantiles', 'month', 'lat', 'lon')

    qm.ds['ref_q'] = utils.get_quantiles(ds_ref[ref_var], qm.ds['quantiles'].data)
    qm.ds['ref_q'].attrs['units'] = ref_units
    qm.ds['hist_clim'] = ds_hist[hist_var].mean('time', keep_attrs=True)
    qm.ds['ref_clim'] = ds_ref[ref_var].mean('time', keep_attrs=True)   
    
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
    )
    ds_ref = utils.read_data(
        args.ref_files,
        args.ref_var,
        time_bounds=args.ref_time_bounds,
        lat_bounds=args.lat_bounds,
        lon_bounds=args.lon_bounds,
        input_units=args.input_ref_units,
        output_units=args.output_units,
    )
    ds_out = train(ds_hist, ds_ref, args.hist_var, args.ref_var, args.scaling)
    ds_out.attrs['history'] = utils.get_new_log()
    ds_out.to_netcdf(args.output_file)


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
        "--scaling",
        type=str,
        choices=('additive', 'multiplicative'),
        default='additive',
        help="scaling method",
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
