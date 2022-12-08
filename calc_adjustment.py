"""Command line program for calculating QQ-scaling adjustment factors."""

import argparse
import logging

import xclim as xc
from xclim import sdba
import dask.diagnostics

import utils


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
    hist_units = ds_hist[args.hist_var].attrs['units']
    
    ds_ref = utils.read_data(
        args.ref_files,
        args.ref_var,
        time_bounds=args.ref_time_bounds,
        input_units=args.input_ref_units,
        output_units=args.output_units,
    )
    ref_units = ds_ref[args.ref_var].attrs['units']

    if len(ds_hist['lat']) != len(ds_ref['lat']):
        ds_hist = utils.regrid(ds_hist, ds_ref, variable=args.hist_var)
    
    scaling_methods = {'additive': '+', 'multiplicative': '*'}
    if args.grouping == 'monthly':
        group_operator = 'time.month'
        group_axis = 'month'
    elif args.grouping == '31day':
        group_operator = sdba.Grouper('time.dayofyear', window=31)
        group_axis = 'dayofyear'
    else:
        raise ValueError(f'Invalid grouping: {args.grouping}')

    mapping_methods = {'qm': sdba.EmpiricalQuantileMapping, 'qdm': sdba.QuantileDeltaMapping}
    qm = mapping_methods[args.mapping].train(
        ds_ref[args.ref_var],
        ds_hist[args.hist_var],
        nquantiles=100,
        group=group_operator,
        kind=scaling_methods[args.scaling]
    )
    qm.ds['hist_q'].attrs['units'] = hist_units
    qm.ds = qm.ds.assign_coords({'lat': ds_ref['lat'], 'lon': ds_ref['lon']}) #xclim strips lat/lon attributes
    qm.ds = qm.ds.transpose('quantiles', group_axis, 'lat', 'lon')

    if args.grouping == 'monthly':
        qm.ds['ref_q'] = utils.get_ref_q(ds_ref[args.ref_var], qm.ds['quantiles'].data)
        qm.ds['ref_q'].attrs['units'] = ref_units
   
    qm.ds.attrs['history'] = utils.get_new_log()
    qm.ds.attrs['historical_period_start'] = args.hist_time_bounds[0]
    qm.ds.attrs['historical_period_end'] = args.hist_time_bounds[1]
    qm.ds.attrs['reference_period_start'] = args.ref_time_bounds[0]
    qm.ds.attrs['reference_period_end'] = args.ref_time_bounds[1]
    qm.ds.attrs['xclim_version'] = xc.__version__
    qm.ds.to_netcdf(args.output_file)


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
        "--grouping",
        type=str,
        choices=('monthly', '31day'),
        default='monthly',
        help="Temporal grouping",
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
