"""Command line program for matching up GCM and QQ-scaled mean change."""

import logging
import argparse

import dask.diagnostics
import xesmf as xe

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
    
    ds_ref = utils.read_data(
        args.ref_files,
        args.ref_var,
        time_bounds=args.ref_time_bounds,
        input_units=args.input_ref_units,
        output_units=args.output_units,
    )

    ds_target = utils.read_data(
        args.target_files,
        args.qq_var,
        time_bounds=args.hist_time_bounds,
        input_units=args.input_target_units,
        output_units=args.output_units,
    )

    ds_qq = utils.read_data(
        args.qq_file,
        args.qq_var,
    )

    hist_clim = ds_hist[args.hist_var].mean('time', keep_attrs=True)
    ref_clim = ds_ref[args.ref_var].mean('time', keep_attrs=True)
    hist_ref_clim_ratio = ref_clim / hist_clim

    target_clim = ds_target[args.qq_var].mean('time', keep_attrs=True)
    qq_clim = ds_qq[args.qq_var].mean('time', keep_attrs=True)

    if len(hist_ref_clim_ratio['lat']) != len(qq_clim['lat']):
       regridder = xe.Regridder(hist_ref_clim_ratio, qq_clim, 'bilinear')
       hist_ref_clim_ratio = regridder(hist_ref_clim_ratio)

    if args.scaling == 'multiplicative':
        adjustment_factor =  (hist_ref_clim_ratio * target_clim) / qq_clim
        da_qq_adjusted = ds_qq[args.qq_var] * adjustment_factor
    elif args.scaling == 'additive':
        adjustment_factor = (ref_clim - hist_clim) - (qq_clim - target_clim)
        da_qq_adjusted = ds_qq[args.qq_var] + adjustment_factor
    else:
        raise ValueError(f'Invalid scaling method: {scaling}')

    da_qq_adjusted.attrs = ds_qq[args.qq_var].attrs
    ds_qq_adjusted = da_qq_adjusted.to_dataset(name=args.qq_var)
    ds_qq_adjusted.attrs = ds_qq.attrs
    infile_logs = {args.qq_file: ds_qq.attrs['history']}
    ds_qq_adjusted.attrs['history'] = utils.get_new_log(infile_logs=infile_logs)
    ds_qq_adjusted.to_netcdf(args.outfile)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        argument_default=argparse.SUPPRESS,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
                          
    parser.add_argument("qq_file", type=str, help="input qq-scaled data (to be adjusted)")
    parser.add_argument("qq_var", type=str, help="variable to process")
    parser.add_argument("outfile", type=str, help="output file")

    parser.add_argument("--output_units", type=str, default=None, help="output data units")
    parser.add_argument(
        "--hist_files",
        type=str,
        nargs='*',
        required=True,
        help="historical data files"
    )
    parser.add_argument("--hist_var", type=str, required=True, help="historical variable")
    parser.add_argument("--input_hist_units", type=str, default=None, help="input historical data units")
    parser.add_argument(
        "--ref_files",
        type=str,
        nargs='*',
        required=True,
        help="reference data files"
    )
    parser.add_argument("--ref_var", type=str, required=True, help="reference variable")
    parser.add_argument("--input_ref_units", type=str, default=None, help="input reference data units")
    parser.add_argument(
        "--target_files",
        type=str,
        nargs='*',
        required=True,
        help="target data files"
    )
    parser.add_argument("--input_target_units", type=str, default=None, help="input target data units")
    parser.add_argument(
        "--hist_time_bounds",
        type=str,
        nargs=2,
        metavar=('START_DATE', 'END_DATE'),
        default=None,
        help="time bounds for historical period (in YYYY-MM-DD format)"
    )
    parser.add_argument(
        "--ref_time_bounds",
        type=str,
        nargs=2,
        metavar=('START_DATE', 'END_DATE'),
        default=None,
        help="time bounds for the reference/future period (in YYYY-MM-DD format)"
    )
    parser.add_argument(
        "--scaling",
        type=str,
        choices=('additive', 'multiplicative'),
        default='additive',
        help="scaling method",
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
    main(args)

