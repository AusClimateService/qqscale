"""Command line program for clipping the maximum values of a dataset."""

import argparse
import logging
import dask.diagnostics

import utils


def main(args):
    """Run the program."""

    dask.diagnostics.ProgressBar().register()

    ds = utils.read_data(args.infile, args.var)
    max_ds = utils.read_data(
        args.maxfiles,
        args.maxvar,
        output_units=ds[args.var].attrs['units'],
        use_cftime=False,
    )
    if len(ds['lat']) != len(max_ds['lat']):
        logging.info('Regridding adjustment factors to input data grid')
        max_ds = utils.regrid(max_ds, ds)
        assert len(max_ds['lat']) == len(ds['lat'])
        assert len(max_ds['lon']) == len(ds['lon'])
    else:
        max_ds['lat'] = ds['lat']
        max_ds['lon'] = ds['lon']
    max_ds['time'] = ds['time']
    max_da = max_ds[args.maxvar]

    ds[args.var] = ds[args.var].where(ds[args.var] < max_da, max_da)

    infile_logs = {}
    if 'history' in ds.attrs:
        infile_logs[args.infile] = ds.attrs['history']
    ds.attrs['history'] = utils.get_new_log(infile_logs=infile_logs)
    ds.to_netcdf(args.outfile, encoding={args.var: {'least_significant_digit': 2, 'zlib': True}})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        argument_default=argparse.SUPPRESS,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )                      
    parser.add_argument("infile", type=str, help="input data (to be clipped)")           
    parser.add_argument("var", type=str, help="variable to process")
    parser.add_argument("outfile", type=str, help="output file")

    parser.add_argument("--maxfiles", type=str, nargs='*', help="data files containing maximum valid values")
    parser.add_argument("--maxvar", type=str, help="variable in maxfiles")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args)
