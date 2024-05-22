"""Command line program for clipping the maximum values of a dataset."""

import argparse
import logging

import dask
import dask.diagnostics
import xarray as xr

import utils


def main(args):
    """Run the program."""

    dask.diagnostics.ProgressBar().register()

    ds = xr.open_dataset(args.infile, decode_times=False)

    max_ds = utils.read_data(
        args.maxfiles,
        args.maxvar,
        time_bounds=args.maxtbounds,
        output_units=ds[args.var].attrs['units'],
        use_cftime=False,
    )
    if len(ds['lat']) != len(max_ds['lat']):
        logging.info('Regridding max data to match input data')
        max_ds = utils.regrid(max_ds, ds)
        assert len(max_ds['lat']) == len(ds['lat'])
        assert len(max_ds['lon']) == len(ds['lon'])
    else:
        max_ds['lat'] = ds['lat']
        max_ds['lon'] = ds['lon']
    max_ds['time'] = ds['time']
    max_da = max_ds[args.maxvar]

    ds[args.var] = xr.apply_ufunc(dask.array.minimum, ds[args.var], max_da, keep_attrs=True, dask='allowed')

    infile_logs = {}
    if 'history' in ds.attrs:
        infile_logs[args.infile] = ds.attrs['history']
    if args.short_history:
        unique_dirnames = utils.get_unique_dirnames(args.maxfiles)
    else:
        unique_dirnames = []
    ds.attrs['history'] = utils.get_new_log(
        infile_logs=infile_logs,
        wildcard_prefixes=unique_dirnames,
    )

    encoding = utils.get_outfile_encoding(ds, args.var, compress=args.compress)
    ds.to_netcdf(args.outfile, encoding=encoding)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        argument_default=argparse.SUPPRESS,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )                      
    parser.add_argument("infile", type=str, help="input data (to be clipped)")           
    parser.add_argument("var", type=str, help="variable to process")
    parser.add_argument("outfile", type=str, help="output file")

    parser.add_argument(
        "--maxfiles",
        type=str,
        nargs='*',
        help="data files containing maximum valid values"
    )
    parser.add_argument(
        "--maxvar",
        type=str,
        help="variable in maxfiles"
    )
    parser.add_argument(
        "--maxtbounds",
        type=str,
        nargs=2,
        metavar=('START_DATE', 'END_DATE'),
        default=None,
        help="time period to extract from the maxfiles [use YYYY-MM-DD format]"
    )
    parser.add_argument(
        "--compress",
        action="store_true",
        default=False,
        help="compress the output data file"
    )
    parser.add_argument(
        "--short_history",
        action='store_true',
        default=False,
        help="Use wildcards to shorten the maxfile list in the outfile history attribute",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args)
