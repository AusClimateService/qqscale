"""Command line program for matching up GCM and QQ-scaled mean change."""

import logging
import argparse

import dask.diagnostics
import xesmf as xe

import utils


def match_mean_change(ds_qq, qq_var, da_hist, da_ref, da_target, scaling):
    """Match the model and quantile delta mean change.

    Parameters
    ----------
    ds_qq : xarray Dataset
        Quantile delta changed dataset
    qq_var : str
        Variable (in ds_qq)
    da_hist : xarray DataArray
        Historical model data
    da_ref : xarray DataArray
        Reference model data
    da_target : xarray DataArray
        Data that the quantile delta changes were applied to
    scaling : {'additive', 'multiplicative'}
        Scaling method
        
    Returns
    -------
    ds_qq_adjusted : xarray Dataset
        Quantile delta change dataset adjusted so it matches model mean change    
    """

    hist_clim = da_hist.mean('time', keep_attrs=True)
    ref_clim = da_ref.mean('time', keep_attrs=True)
    target_clim = da_target.mean('time', keep_attrs=True)
    qq_clim = ds_qq[qq_var].mean('time', keep_attrs=True)
    qq_clim['lat'] = target_clim['lat']
    qq_clim['lon'] = target_clim['lon']

    if scaling == 'multiplicative':
        ref_hist_clim_ratio = ref_clim / hist_clim
        if len(ref_hist_clim_ratio['lat']) != len(qq_clim['lat']):
            regridder = xe.Regridder(ref_hist_clim_ratio, qq_clim, 'bilinear')
            ref_hist_clim_ratio = regridder(ref_hist_clim_ratio)
        adjustment_factor = (ref_hist_clim_ratio * target_clim) / qq_clim
        da_qq_adjusted = ds_qq[qq_var] * adjustment_factor
    elif args.scaling == 'additive':
        ref_hist_clim_diff = ref_clim - hist_clim
        if len(ref_hist_clim_diff['lat']) != len(qq_clim['lat']):
            regridder = xe.Regridder(ref_hist_clim_diff, qq_clim, 'bilinear')
            ref_hist_clim_diff = regridder(ref_hist_clim_diff)
        adjustment_factor = ref_hist_clim_diff - (qq_clim - target_clim)
        da_qq_adjusted = ds_qq[qq_var] + adjustment_factor
    else:
        raise ValueError(f'Invalid scaling method: {scaling}')

    da_qq_adjusted.attrs = ds_qq[qq_var].attrs
    ds_qq_adjusted = da_qq_adjusted.to_dataset(name=qq_var)
    ds_qq_adjusted.attrs = ds_qq.attrs

    return ds_qq_adjusted


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
        time_bounds=args.target_time_bounds,
        input_units=args.input_target_units,
        output_units=args.output_units,
    )
    ds_qq = utils.read_data(
        args.qq_file,
        args.qq_var,
    )
    ds_qq_adjusted = match_mean_change(
        ds_qq,
        args.qq_var,
        ds_hist[args.hist_var],
        ds_ref[args.ref_var],
        ds_target[args.qq_var],
        args.scaling
    )
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

    parser.add_argument("--hist_files", type=str, nargs='*', required=True, help="historical data files")
    parser.add_argument("--hist_var", type=str, required=True, help="historical variable")
    parser.add_argument("--input_hist_units", type=str, default=None, help="input historical data units")
    parser.add_argument(
        "--hist_time_bounds",
        type=str,
        nargs=2,
        metavar=('START_DATE', 'END_DATE'),
        default=None,
        help="time bounds for historical period (in YYYY-MM-DD format)"
    )
    parser.add_argument("--ref_files", type=str, nargs='*', required=True, help="reference data files")
    parser.add_argument("--ref_var", type=str, required=True, help="reference variable")
    parser.add_argument("--input_ref_units", type=str, default=None, help="input reference data units")
    parser.add_argument(
        "--ref_time_bounds",
        type=str,
        nargs=2,
        metavar=('START_DATE', 'END_DATE'),
        default=None,
        help="time bounds for the reference/future period (in YYYY-MM-DD format)"
    )
    parser.add_argument("--target_files", type=str, nargs='*', required=True, help="target data files")
    parser.add_argument("--input_target_units", type=str, default=None, help="input target data units")
    parser.add_argument(
        "--target_time_bounds",
        type=str,
        nargs=2,
        metavar=('START_DATE', 'END_DATE'),
        default=None,
        help="time bounds for the target data (in YYYY-MM-DD format)"
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

