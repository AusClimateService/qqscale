"""Command line program for calculating quantiles."""

import argparse
import logging

import dask.diagnostics
import xclim as xc

import utils


def main(args):
    """Run the program."""

    dask.diagnostics.ProgressBar().register()

    ds_in = utils.read_data(
        args.infiles,
        args.var,
        time_bounds=args.time_bounds,
        input_units=args.input_units,
        output_units=args.output_units,
    )
    invar_attrs = ds_in[args.var].attrs

    quantiles = xc.sdba.utils.equally_spaced_nodes(args.nquantiles)
    da_q = utils.get_quantiles(ds_in[args.var], quantiles, timescale='monthly')
    ds_out = da_q.to_dataset(name=args.var)    
    ds_out[args.var].attrs = invar_attrs
    
    ds_out.attrs['history'] = utils.get_new_log()
    ds_out.to_netcdf(args.outfile)


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
