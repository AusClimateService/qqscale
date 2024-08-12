"""Command line program for calculating adjustment factors for matching up the model and QDC-scaled mean change."""

import logging
import argparse

import dask.diagnostics

import utils


def change_match_train(ds_qdc, qdc_var, da_hist, da_ref, da_target, scaling, timescale):
    """Get adjustment factors for matching the model and QDC-scaled mean change.

    Parameters
    ----------
    ds_qdc : xarray Dataset
        Quantile delta changed dataset
    qdc_var : str
        Variable (in ds_qdc)
    da_hist : xarray DataArray
        Historical model data
    da_ref : xarray DataArray
        Reference model data
    da_target : xarray DataArray
        Data that the quantile delta changes were applied to
    scaling : {'additive', 'multiplicative'}
        Scaling method
    timescale : {'annual', 'monthly'}
        Timescale for mean matching
        
    Returns
    -------
    adjustment_factor : xarray Dataset    
    """

    if timescale == 'monthly':
        hist_clim = da_hist.groupby('time.month').mean('time', keep_attrs=True)
        ref_clim = da_ref.groupby('time.month').mean('time', keep_attrs=True)
        target_clim = da_target.groupby('time.month').mean('time', keep_attrs=True)
        qdc_clim = ds_qdc[qdc_var].groupby('time.month').mean('time', keep_attrs=True)
    elif timescale == 'annual':
        hist_clim = da_hist.mean('time', keep_attrs=True)
        ref_clim = da_ref.mean('time', keep_attrs=True)
        target_clim = da_target.mean('time', keep_attrs=True)
        qdc_clim = ds_qdc[qdc_var].mean('time', keep_attrs=True)
    else:
        raise ValueError(f'Invalid mean match timescale: {timescale}')

    dims = ds_qdc[qdc_var].dims
    on_spatial_grid = ('lat' in dims) and ('lon' in dims)
    if on_spatial_grid:
        assert len(target_clim['lat']) != len(qdc_clim['lat'])
        assert len(target_clim['lon']) != len(qdc_clim['lon'])
        target_clim['lat'] = qdc_clim['lat']
        target_clim['lon'] = qdc_clim['lon'] 

    if scaling == 'multiplicative':
        ref_hist_clim_ratio = ref_clim / hist_clim
        if on_spatial_grid:
            if len(ref_hist_clim_ratio['lat']) != len(qdc_clim['lat']):
                logging.info('Regridding input data to QDC grid')
                ref_hist_clim_ratio = utils.regrid(ref_hist_clim_ratio, qdc_clim)
        adjustment_factors = (ref_hist_clim_ratio * target_clim) / qdc_clim
    elif scaling == 'additive':
        ref_hist_clim_diff = ref_clim - hist_clim
        if on_spatial_grid:
            if len(ref_hist_clim_diff['lat']) != len(qdc_clim['lat']):
                logging.info('Regridding input data to QDC grid')
                ref_hist_clim_diff = utils.regrid(ref_hist_clim_diff, qdc_clim)                
        adjustment_factors = ref_hist_clim_diff - (qdc_clim - target_clim)
    else:
        raise ValueError(f'Invalid scaling method: {scaling}')

    return adjustment_factors


def main(args):
    """Run the program."""

    dask.diagnostics.ProgressBar().register()
    ds_qdc = utils.read_data(
        args.qdc_file,
        args.qdc_var,
    )
    units = ds_qdc[args.qdc_var].attrs['units']
    ds_hist = utils.read_data(
        args.hist_files,
        args.hist_var,
        time_bounds=args.hist_time_bounds,
        input_units=args.input_hist_units,
        output_units=units,
    )
    ds_ref = utils.read_data(
        args.ref_files,
        args.ref_var,
        time_bounds=args.ref_time_bounds,
        input_units=args.input_ref_units,
        output_units=units,
    )
    ds_target = utils.read_data(
        args.target_files,
        args.qdc_var,
        time_bounds=args.target_time_bounds,
        input_units=args.input_target_units,
        output_units=units,
    )
    adjustment_factors = change_match_train(
        ds_qdc,
        args.qdc_var,
        ds_hist[args.hist_var],
        ds_ref[args.ref_var],
        ds_target[args.qdc_var],
        args.scaling,
        args.timescale
    )

    if args.short_history:
        unique_dirnames = utils.get_unique_dirnames(
            args.hist_files + args.ref_files + args.target_files
        )
    else:
        unique_dirnames = []
    adjustment_factors.attrs['history'] = utils.get_new_log(wildcard_prefixes=unique_dirnames)

    encoding = utils.get_outfile_encoding(adjustment_factors, args.qdc_var)
    adjustment_factors.to_netcdf(args.outfile, encoding=encoding)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        argument_default=argparse.SUPPRESS,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )            
    parser.add_argument("qdc_file", type=str, help="input QDC-scaled data (to be adjusted)")
    parser.add_argument("qdc_var", type=str, help="variable to process")
    parser.add_argument("outfile", type=str, help="output file")

    parser.add_argument(
        "--hist_files",
        type=str,
        nargs='*',
        required=True,
        help="historical data files"
    )
    parser.add_argument(
        "--hist_var",
        type=str,
        required=True,
        help="historical variable"
    )
    parser.add_argument(
        "--input_hist_units",
        type=str,
        default=None,
        help="input historical data units"
    )
    parser.add_argument(
        "--hist_time_bounds",
        type=str,
        nargs=2,
        metavar=('START_DATE', 'END_DATE'),
        default=None,
        help="time bounds for historical period (in YYYY-MM-DD format)"
    )

    parser.add_argument(
        "--ref_files",
        type=str,
        nargs='*',
        required=True,
        help="reference data files"
    )
    parser.add_argument(
        "--ref_var",
        type=str,
        required=True,
        help="reference variable"
    )
    parser.add_argument(
        "--input_ref_units",
        type=str,
        default=None,
        help="input reference data units")
    parser.add_argument(
        "--ref_time_bounds",
        type=str,
        nargs=2,
        metavar=('START_DATE', 'END_DATE'),
        default=None,
        help="time bounds for the reference/future period (in YYYY-MM-DD format)"
    )

    parser.add_argument(
        "--target_files",
        type=str,
        nargs='*',
        required=True,
        help="target data files"
    )
    parser.add_argument(
        "--input_target_units",
        type=str,
        default=None,
        help="input target data units"
    )
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
        "--timescale",
        type=str,
        choices=('annual', 'monthly'),
        default='annual',
        help="timescale for mean matching",
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