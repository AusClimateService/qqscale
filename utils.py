"""Utility functions"""

import logging

import git
import numpy as np
import xarray as xr
import xclim as xc
from xclim.sdba import nbutils
import xesmf as xe

import cmdline_provenance as cmdprov


def get_new_log(infile_logs={}):
    """Generate command log for output file."""

    try:
        repo = git.Repo()
        repo_url = repo.remotes[0].url.split(".git")[0]
    except (git.exc.InvalidGitRepositoryError, NameError):
        repo_url = None
    new_log = cmdprov.new_log(
        infile_logs=infile_logs,
        code_url=repo_url,
    )

    return new_log


def profiling_stats(rprof):
    """Record profiling information."""

    max_memory = np.max([result.mem for result in rprof.results])
    max_cpus = np.max([result.cpu for result in rprof.results])

    logging.info(f'Peak memory usage: {max_memory}MB')
    logging.info(f'Peak CPU usage: {max_cpus}%')


def read_data(
    infiles,
    var,
    time_bounds=None,
    input_units=None,
    output_units=None,
    lon_chunk_size=None,
    ssr=False,
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
        
    if input_units:
        ds[var].attrs['units'] = input_units
    if output_units:
        ds[var] = xc.units.convert_units_to(ds[var], output_units)
        ds[var].attrs['units'] = output_units
        
    if ssr:
        threshold = 8.64e-4
        random_array = (1.0 - np.random.random_sample(ds[var].shape)) * threshold
        ds[var] = ds[var].where(ds[var] >= threshold, random_array)
        
    chunk_dict = {'time': -1}
    if lon_chunk_size:
        chunk_dict['lon'] = lon_chunk_size
    ds = ds.chunk(chunk_dict)
    logging.info(f'Array size: {ds[var].shape}')
    logging.info(f'Chunk size: {ds[var].chunksizes}')
    
    return ds


def get_ref_q(da, quantiles):
    """Get reference quantiles.

    Required because sdba.EmpiricalQuantileMapping.train only
    outputs hist_q and not ref_q too.    
    """

    months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    q_list = []
    for month in months:
        mth = nbutils.quantile(da[da['time'].dt.month == month], quantiles, ['time'])
        q_list.append(mth)
    ref_q = xr.concat(q_list, dim='month')
    ref_q.coords['month'] = months
    ref_q = ref_q.transpose('quantiles', 'month', 'lat', 'lon')
    ref_q.attrs['standard_name'] = 'Reference quantiles'
    ref_q.attrs['long_name'] = 'Quantiles of reference on the reference period'

    return ref_q


def regrid(ds, ds_grid, variable=None, method='bilinear'):
    """Regrid data
    
    Parameters
    ----------
    ds : xarray Dataset
        Dataset to be regridded
    ds_grid : xarray Dataset
        Dataset containing target horizontal grid
    variable : str, optional
        Variable to restore attributes for
    method : str, default bilinear
        Method for regridding
    
    Returns
    -------
    ds : xarray Dataset
    
    """
    
    global_attrs = ds.attrs
    if variable:
        var_attrs = ds[variable].attrs        
    regridder = xe.Regridder(ds, ds_grid, method)
    ds = regridder(ds)
    ds.attrs = global_attrs
    if variable:
        ds[variable].attrs = var_attrs
    
    return ds
