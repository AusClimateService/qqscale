"""Command line program for applying mean change match adjustment factors."""

import logging
import argparse

import xarray as xr
import dask.diagnostics

import utils


def change_match_adjust(ds_qdc, qdc_var, adjustment_factors, scaling, time_grouping=None):
    """Apply adjustment factors to match model and quantile delta mean change.

    Parameters
    ----------
    ds_qdc : xarray Dataset
        Quantile delta changed dataset
    qdc_var : str
        Variable (in ds_qdc)
    scaling : {'additive', 'multiplicative'}
        Scaling method
    time_grouping : {'monthly'}, optional
        Time grouping for mean matching
        
    Returns
    -------
    ds_qdc_adjusted : xarray Dataset
        Quantile delta change dataset adjusted so it matches model mean change    
    """

    if scaling == 'multiplicative':
        if time_grouping == 'monthly':
            da_qdc_adjusted = ds_qdc[qdc_var].groupby('time.month') * adjustment_factors
        else:
            da_qdc_adjusted = ds_qdc[qdc_var] * adjustment_factors
    elif scaling == 'additive':
        if time_grouping == 'monthly':
            da_qdc_adjusted = ds_qdc[qdc_var].groupby('time.month') + adjustment_factors
        else:
            da_qdc_adjusted = ds_qdc[qdc_var] + adjustment_factors
    else:
        raise ValueError(f'Invalid scaling method: {scaling}')

    if time_grouping == 'monthly':
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
        ds_adjust[args.qdc_var],
        args.scaling,
        args.time_grouping,
    )

    infile_logs = {
        args.qdc_file: ds_qdc.attrs['history'],
        args.adjustment_file: ds_adjust.attrs['history'],
    }
    ds_qdc_adjusted.attrs['history'] = utils.get_new_log(infile_logs=infile_logs)
    encoding = utils.get_outfile_encoding(
        ds_qdc_adjusted,
        args.qdc_var,
        time_units=args.output_time_units
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
        "--time_grouping",
        type=str,
        choices=('monthly'),
        default=None,
        help="time grouping for mean matching",
    )
    parser.add_argument(
        "--output_time_units",
        type=str,
        default=None,
        help="""Time units for output file (e.g. 'days_since_1950-01-01')""",
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
