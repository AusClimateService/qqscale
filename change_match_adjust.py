"""Command line program for applying mean change match adjustment factors."""

import logging
import argparse

import xarray as xr
import dask.diagnostics

import utils


def change_match_adjust(ds_qdc, qdc_var, adjustment_factors, scaling, timescale):
    """Apply adjustment factors to match model and quantile delta mean change.

    Parameters
    ----------
    ds_qdc : xarray Dataset
        Quantile delta changed dataset
    qdc_var : str
        Variable (in ds_qdc)
    scaling : {'additive', 'multiplicative'}
        Scaling method
    timescale : {'annual', 'monthly'}
        Timescale for mean matching
        
    Returns
    -------
    ds_qdc_adjusted : xarray Dataset
        Quantile delta change dataset adjusted so it matches model mean change    
    """

    if scaling == 'multiplicative':
        if timescale == 'monthly':
            da_qdc_adjusted = ds_qdc[qdc_var].groupby('time.month') * adjustment_factors
        elif timescale == 'annual':
            da_qdc_adjusted = ds_qdc[qdc_var] * adjustment_factors
    elif scaling == 'additive':
        if timescale == 'monthly':
            da_qdc_adjusted = ds_qdc[qdc_var].groupby('time.month') + adjustment_factors
        elif timescale == 'annual':
            da_qdc_adjusted = ds_qdc[qdc_var] + adjustment_factors
    else:
        raise ValueError(f'Invalid scaling method: {scaling}')

    if timescale == 'monthly':
        del da_qdc_adjusted['month']
    da_qdc_adjusted.attrs = ds_qdc[qdc_var].attrs
    ds_qdc_adjusted = da_qdc_adjusted.to_dataset(name=qdc_var)
    ds_qdc_adjusted.attrs = ds_qdc.attrs

    return ds_qdc_adjusted


def main(args):
    """Run the program."""

    dask.diagnostics.ProgressBar().register()
    ds_qdc = utils.read_data(
        args.qdc_file,
        args.qdc_var,
    )
    ds_adjust = xr.open_dataset(args.adjustment_file)

    ds_qdc_adjusted = change_match_adjust(
        ds_qdc,
        args.qdc_var,
        adjustment_factors,
        args.scaling,
        args.timescale
    )

    infile_logs = {args.qdc_file: ds_qdc.attrs['history']}
    ds_qdc_adjusted.attrs['history'] = utils.get_new_log(infile_logs=infile_logs)
    encoding = utils.get_outfile_encoding(
        ds_qdc_adjusted,
        args.qdc_var,
        compress=args.compress,
    )
    ds_qdc_adjusted.to_netcdf(args.outfile, encoding=encoding)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        argument_default=argparse.SUPPRESS,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )            
    parser.add_argument("qdc_file", type=str, help="input QDC-scaled data (to be adjusted)")
    parser.add_argument("qdc_var", type=str, help="variable to process")
    parser.add_argument("adjustment_file", type=str, help="adjustment factor file")
    parser.add_argument("outfile", type=str, help="output file")
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