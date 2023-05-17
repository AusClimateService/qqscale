"""Command line program for Singularity Stochastic Removal."""

import argparse
import logging

import numpy as np
import dask.diagnostics

import utils


def apply_ssr(da, threshold=8.64e-4):
    """Apply Singularity Stochastic Removal.

    Used to avoid divide by zero errors in the analysis of precipitation data.
    All near-zero values (i.e. < threshold) are set to a small random non-zero value:
    0 < value <= threshold
    
    Parameters
    ----------
    da : xarray DataArray
        Input precipitation data
    threhsold : float, default 8.64e-4 mm
        Threshold for near-zero rainfall

    Returns
    -------
    da_ssr : xarray DataArray
        Input data with ssr applied

    Reference
    ---------
    Vrac, M., Noel, T., & Vautard, R. (2016). Bias correction of precipitation
    through Singularity Stochastic Removal: Because occurrences matter.
    Journal of Geophysical Research: Atmospheres, 121(10), 5237–5258.
    https://doi.org/10.1002/2015JD024511
    """

    random_array = (1.0 - np.random.random_sample(da.shape)) * threshold
    da_ssr = da.where(da >= threshold, random_array)

    return da_ssr


def reverse_ssr(da_ssr, threshold=8.64e-4):
    """Reverse Singularity Stochastic Removal.

    SSR is used to avoid divide by zero errors in the analysis of precipitation data.
    It involves setting near-zero values (i.e. < threshold) to a small non-zero random value: 0 < value <= threshold.
    This function reverses SSR (commonly at the end of a calculation) by setting all near-zero values (i.e. < threshold) to zero.
    
    Parameters
    ----------
    da_ssr : xarray DataArray
        Input precipitation data (that has had SSR applied)
    threhsold : float, default 8.64e-4 mm
        Threshold for near-zero rainfall

    Returns
    -------
    da_no_ssr : xarray DataArray
        Input data with ssr reversed

    Reference
    ---------
    Vrac, M., Noel, T., & Vautard, R. (2016). Bias correction of precipitation
    through Singularity Stochastic Removal: Because occurrences matter.
    Journal of Geophysical Research: Atmospheres, 121(10), 5237–5258.
    https://doi.org/10.1002/2015JD024511
    """

    da_no_ssr = da_ssr.where(da_ssr >= 8.64e-4, 0.0)

    return da_no_ssr


def main(args):
    """Run the program."""

    dask.diagnostics.ProgressBar().register()

    ds = utils.read_data(
        args.infiles,
        args.var,
        time_bounds=args.time_bounds,
        input_units=args.input_units,
        output_units=args.output_units,
    )
    ds[args.var] = apply_ssr(ds[args.var])
    ds.attrs['history'] = utils.get_new_log()
    ds.to_netcdf(args.outfile)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        argument_default=argparse.SUPPRESS,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
                          
    parser.add_argument("infiles", type=str, nargs='*', help="input data (to be adjusted)")           
    parser.add_argument("var", type=str, help="variable to process")
    parser.add_argument("outfile", type=str, help="output file")

    parser.add_argument("--input_units", type=str, default=None, help="input data units")
    parser.add_argument("--output_units", type=str, default=None, help="output data units")
    parser.add_argument(
        "--time_bounds",
        type=str,
        nargs=2,
        metavar=('START_DATE', 'END_DATE'),
        required=True,
        help="time bounds in YYYY-MM-DD format"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    with dask.diagnostics.ResourceProfiler() as rprof:
        main(args)
    utils.profiling_stats(rprof)
