"""Command line program for calculating quantiles."""

import argparse
import logging

import dask.diagnostics
import xclim as xc

import utils


def quantiles(ds, var, nquantiles):
    """Calculate quantiles for each month.

    Parameters
    ----------
    ds : xarray Dataset
        Input data
    var : str
        Variable (in ds) 
    nquantiles : int
        Number of quantiles to calculate

    Returns
    -------
    ds_q : xarray Dataset
        Quantiles for each month
    """

    invar_attrs = ds[var].attrs
    quantile_array = xc.sdba.utils.equally_spaced_nodes(nquantiles)
    da_q = utils.get_quantiles(ds[var], quantile_array, timescale='monthly')
    ds_q = da_q.to_dataset(name=var)    
    ds_q[var].attrs = invar_attrs

    return ds_q


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
    ds_q = quantiles(ds, args.var, args.nquantiles)
    ds_q.attrs['history'] = utils.get_new_log()
    ds_q.to_netcdf(args.outfile)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        argument_default=argparse.SUPPRESS,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
                          
    parser.add_argument("infiles", type=str, nargs='*', help="input data (to be adjusted)")           
    parser.add_argument("var", type=str, help="variable to process")
    parser.add_argument("nquantiles", type=int, help="number of quantiles")
    parser.add_argument("outfile", type=str, help="output file")

    parser.add_argument("--input_units", type=str, default=None, help="input data units")
    parser.add_argument("--output_units", type=str, default=None, help="output data units")
    parser.add_argument(
        "--time_bounds",
        type=str,
        nargs=2,
        default=None,
        metavar=('START_DATE', 'END_DATE'),
        help="time bounds in YYYY-MM-DD format"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args)
