"""Command line program for calculating QQ-scaling adjustment factors."""

import argparse
import logging

import git
import numpy as np
import xarray as xr
import xclim as xc
from xclim import sdba
import cmdline_provenance as cmdprov
import dask.diagnostics
from dask.distributed import Client, LocalCluster, progress


def profiling_stats(rprof):
    """Record profiling information."""

    max_memory = np.max([result.mem for result in rprof.results])
    max_cpus = np.max([result.cpu for result in rprof.results])

    logging.debug(f'Peak memory usage: {max_memory}MB')
    logging.debug(f'Peak CPU usage: {max_cpus}%')

    
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
    lon_chunk_size=20,
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
    logging.debug(f'Array size: {ds[var].shape}')
    logging.debug(f'Chunk size: {ds[var].chunksizes}')

    if input_units:
        ds[var].attrs['units'] = input_units
    if output_units:
        ds[var] = xc.units.convert_units_to(ds[var], output_units)

    return ds
     

def main(args):
    """Run the program."""
    
    if args.local_cluster:
        assert args.dask_dir, "Must provide --dask_dir for local cluster"
        dask.config.set(temporary_directory=args.dask_dir)
        cluster = LocalCluster(n_workers=args.nworkers)
        client = Client(cluster)
        print("Watch progress at http://localhost:8787/status")
    else:
        dask.diagnostics.ProgressBar().register()
    
    ds_hist = read_data(
        args.hist_files,
        args.variable,
        time_bounds=args.hist_time_bounds,
        input_units=args.input_units,
        output_units=args.output_units,
        lon_chunk_size=args.lon_chunk_size,
    )
    ds_fut = read_data(
        args.fut_files,
        args.variable,
        time_bounds=args.fut_time_bounds,
        input_units=args.input_units,
        output_units=args.output_units,
        lon_chunk_size=args.lon_chunk_size,
    )

    mapping_methods = {'additive': '+', 'multiplicative': '*'}
    qm = sdba.EmpiricalQuantileMapping.train(
        ds_fut[args.variable],
        ds_hist[args.variable],
        nquantiles=100,
        group="time.month",
        kind=mapping_methods[args.method]
    )
    if args.local_cluster:
        qm = qm.persist()
        progress(qm)
    
    qm.ds = qm.ds.assign_coords({'lat': ds_fut['lat'], 'lon': ds_fut['lon']}) #xclim strips lat/lon attributes
    qm.ds = qm.ds.transpose('quantiles', 'month', 'lat', 'lon')

    qm.ds.attrs['history'] = get_new_log()
    qm.ds.attrs['base_period_start'] = args.hist_time_bounds[0]
    qm.ds.attrs['base_period_end'] = args.hist_time_bounds[1]
    qm.ds.attrs['future_period_start'] =args.fut_time_bounds[0]
    qm.ds.attrs['future_period_end'] = args.fut_time_bounds[1]
    qm.ds.to_netcdf(args.output_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        argument_default=argparse.SUPPRESS,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )          
    parser.add_argument("variable", type=str, help="model variable to process")
    parser.add_argument("output_file", type=str, help="output file")
    parser.add_argument(
        "--hist_files",
        type=str,
        nargs='*',
        required=True,
        help="historical GCM data files"
    )
    parser.add_argument(
        "--fut_files",
        type=str,
        nargs='*',
        required=True,
        help="future GCM data files"
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
        "--fut_time_bounds",
        type=str,
        nargs=2,
        metavar=('START_DATE', 'END_DATE'),
        required=True,
        help="future time bounds in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--method",
        type=str,
        choices=('additive', 'multiplicative'),
        default='additive',
        help="scaling method",
    )
    parser.add_argument(
        "--input_units",
        type=str,
        default=None,
        help="input data units"
    )
    parser.add_argument(
        "--output_units",
        type=str,
        default=None,
        help="output data units"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help='Set logging level to DEBUG',
    )
    parser.add_argument(
        "--local_cluster",
        action="store_true",
        default=False,
        help='Use a local dask cluster',
    )
    parser.add_argument(
        "--dask_dir",
        type=str,
        default=None,
        help='Directory where dask worker space files can be written. Required for local cluster.',
    )
    parser.add_argument(
        "--nworkers",
        type=int,
        default=None,
        help='Number of workers for cluster',
    )
    parser.add_argument(
        "--lon_chunk_size",
        type=int,
        default=None,
        help='Size of longitude chunks (i.e. number of lons in each chunk)',
    )
    args = parser.parse_args()
    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level)
    with dask.diagnostics.ResourceProfiler() as rprof:
        main(args)
    profiling_stats(rprof)
