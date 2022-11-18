"""Command line program for calculating QQ-scaling adjustment factors."""
import pdb
import argparse
import logging

import git
import numpy as np
import xarray as xr
import xclim as xc
from xclim import sdba
import xesmf as xe
import cmdline_provenance as cmdprov
import dask.diagnostics
from dask.distributed import Client, LocalCluster, progress

    
def get_new_log():
    """Generate command log for output file."""

    try:
        repo = git.Repo()
        repo_url = repo.remotes[0].url.split(".git")[0]
    except (git.exc.InvalidGitRepositoryError, NameError):
        repo_url = None
    new_log = cmdprov.new_log(
        code_url=repo_url,
    )

    return new_log


def read_data(
    infiles,
    var,
    time_bounds=None,
    input_units=None,
    output_units=None,
    lon_chunk_size=None,
):
    """Read and process an input dataset."""

    if len(infiles) == 1:
        ds = xr.open_dataset(infiles[0])
    else:
        ds = xr.open_mfdataset(infiles)

    try:
        ds = ds.drop('height')
    except ValueError:
        pass

    if time_bounds:
        start_date, end_date = time_bounds
        ds = ds.sel({'time': slice(start_date, end_date)})

    chunk_dict = {'time': -1}
    if lon_chunk_size:
        chunk_dict['lon'] = lon_chunk_size
    ds = ds.chunk(chunk_dict)
    logging.info(f'Array size: {ds[var].shape}')
    logging.info(f'Chunk size: {ds[var].chunksizes}')

    if input_units:
        ds[var].attrs['units'] = input_units
    if output_units:
        ds[var] = xc.units.convert_units_to(ds[var], output_units)

    return ds


def adapt_frequency(da_ref, da_hist, threshold):
    """Adapt frequency of values under threshold of historical data to match reference data
    
    Parameters
    ----------
    da_ref : xarray.DataArray
        Reference data
    da_hist : xarray.DataArray
        Historical data
    threshold : str
        Threshold under which to match frequency.
        Typically close to zero (e.g. '0.5 mm d-1').
    
    Returns
    -------
    da_hist_ad : xarray.DataArray
        Adapted historical data
    
    Notes
    -----
    Frequency adaptation is sometimes needed for precipitation data when using multiplicative scaling,
    particularly for dry locations where a number of quantiles are 0.0 mm.
    Problems can arise if the historical data has more zero quantiles
    for a given month than the reference data.
    When you get the first non-zero quantile you end up dividing a relatively large
    reference value by a relatively small historical value,
    leading to a large adjustment factor.
    
    https://xclim.readthedocs.io/en/stable/notebooks/sdba.html#First-example-:-pr-and-frequency-adaptation
    
    The threshold is usually set just above zero
    (because the point is to match the number of zero quantiles)
    but the resulting adjustment factors can be pretty sensitive to whether
    'just above zero' is 0.001 or 0.5 (for instance).
    
    """
    assert da_ref.attrs['units'] in threshold
    assert da_hist.attrs['units'] in threshold
    da_hist_ad, pth, dP0 = sdba.processing.adapt_freq(
        da_ref, da_hist, thresh=threshold, group="time.month"
    )
    
    return da_hist_ad
    

def main(args):
    """Run the program."""
    
    dask.diagnostics.ProgressBar().register()
    
    ds_hist = read_data(
        args.hist_files,
        args.hist_var,
        time_bounds=args.hist_time_bounds,
        input_units=args.input_hist_units,
        output_units=args.output_units,
    )
    ds_ref = read_data(
        args.ref_files,
        args.ref_var,
        time_bounds=args.ref_time_bounds,
        input_units=args.input_ref_units,
        output_units=args.output_units,
    )

    if len(ds_hist['lat']) != len(ds_ref['lat']):
        regridder = xe.Regridder(ds_hist, ds_ref, "bilinear")
        ds_hist = regridder(ds_hist)
    
    mapping_methods = {'additive': '+', 'multiplicative': '*'}
    qm = sdba.EmpiricalQuantileMapping.train(
        ds_ref[args.ref_var],
        ds_hist[args.hist_var],
        nquantiles=100,
        group="time.month",
        kind=mapping_methods[args.method]
    )
    qm_reverse = sdba.EmpiricalQuantileMapping.train(
        ds_hist[args.hist_var],
        ds_ref[args.ref_var],
        nquantiles=100,
        group="time.month",
        kind=mapping_methods[args.method]
    )
    qm.ds['ref_q'] = qm_reverse.ds['hist_q']
    if args.adapt_freq:
        assert args.method == 'multiplicative', \
            "Frequency adaptation is only needed for multiplicative scaling"
        da_hist_adapted = adapt_frequency(
            ds_ref[args.ref_var],
            ds_hist[args.hist_var],
            args.adapt_freq,
        )
        qm_ad = sdba.EmpiricalQuantileMapping.train(
            ds_ref[args.ref_var],
            da_hist_adapted,
            nquantiles=100,
            group="time.month",
            kind=mapping_methods[args.method]
        )
        qm.ds['hist_q_ad'] = qm_ad.ds['hist_q']
        qm.ds['af_ad'] = qm_ad.ds['af']
        
    qm.ds = qm.ds.assign_coords({'lat': ds_ref['lat'], 'lon': ds_ref['lon']}) #xclim strips lat/lon attributes
    qm.ds = qm.ds.transpose('quantiles', 'month', 'lat', 'lon')

    qm.ds.attrs['history'] = get_new_log()
    qm.ds.attrs['historical_period_start'] = args.hist_time_bounds[0]
    qm.ds.attrs['historical_period_end'] = args.hist_time_bounds[1]
    qm.ds.attrs['reference_period_start'] = args.ref_time_bounds[0]
    qm.ds.attrs['reference_period_end'] = args.ref_time_bounds[1]
    qm.ds.to_netcdf(args.output_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        argument_default=argparse.SUPPRESS,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )          
    parser.add_argument("hist_var", type=str, help="historical variable to process")
    parser.add_argument("ref_var", type=str, help="reference variable to process")
    parser.add_argument("output_file", type=str, help="output file")
    parser.add_argument(
        "--hist_files",
        type=str,
        nargs='*',
        required=True,
        help="historical data files"
    )
    parser.add_argument(
        "--ref_files",
        type=str,
        nargs='*',
        required=True,
        help="reference data files"
    )
    parser.add_argument(
        "--hist_time_bounds",
        type=str,
        nargs=2,
        metavar=('START_DATE', 'END_DATE'),
        required=True,
        help="historical time bounds in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--ref_time_bounds",
        type=str,
        nargs=2,
        metavar=('START_DATE', 'END_DATE'),
        required=True,
        help="reference time bounds in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--method",
        type=str,
        choices=('additive', 'multiplicative'),
        default='additive',
        help="scaling method",
    )
    parser.add_argument(
        "--input_hist_units",
        type=str,
        default=None,
        help="input historical data units"
    )
    parser.add_argument(
        "--input_ref_units",
        type=str,
        default=None,
        help="input reference data units"
    )
    parser.add_argument(
        "--output_units",
        type=str,
        default=None,
        help="output data units"
    )
    parser.add_argument(
        "--adapt_freq",
        type=str,
        default=None,
        help="""adapt historical frequency of values under this threshold to match reference (e.g. '0.5 mm d-1')"""
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help='Set logging level to DEBUG',
    )
    args = parser.parse_args()
    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level)
    main(args)
