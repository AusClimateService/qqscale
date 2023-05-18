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
    lat_bounds=None,
    lon_bounds=None,
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
    if lat_bounds:
        ds = subset_lat(ds, lat_bounds)
    if lon_bounds:
        ds = subset_lon(ds, lon_bounds)

    if input_units:
        ds[var].attrs['units'] = input_units
    if output_units:
        ds[var] = xc.units.convert_units_to(ds[var], output_units)
        ds[var].attrs['units'] = output_units
        
    chunk_dict = {'time': -1}
    if lon_chunk_size:
        chunk_dict['lon'] = lon_chunk_size
    ds = ds.chunk(chunk_dict)
    logging.info(f'Array size: {ds[var].shape}')
    logging.info(f'Chunk size: {ds[var].chunksizes}')
    
    return ds


def get_quantiles(da, quantiles, timescale='monthly'):
    """Get quantiles.

    Required because sdba.EmpiricalQuantileMapping.train only
    outputs hist_q and not others like ref_q.    
    """

    if timescale == 'monthly':
        months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        q_list = []
        for month in months:
            mth = nbutils.quantile(da[da['time'].dt.month == month], quantiles, ['time'])
            q_list.append(mth)
        da_q = xr.concat(q_list, dim='month')
        da_q.coords['month'] = months
        try:
            da_q = da_q.transpose('quantiles', 'month', 'lat', 'lon')
        except ValueError:
            da_q = da_q.transpose('quantiles', 'month')
    elif timescale == 'annual':
        da_q = nbutils.quantile(da, quantiles, ['time'])
        try:
            da_q = da_q.transpose('quantiles', 'lat', 'lon')
        except ValueError:
            pass
    else:
        raise ValueError('Invalid timescale: {timescale}')

    da_q.attrs['standard_name'] = 'Quantiles'
    da_q.attrs['long_name'] = 'Quantiles'

    return da_q


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


def subset_lat(ds, lat_bnds):
    """Select grid points that fall within latitude bounds.

    Parameters
    ----------
    ds : Union[xarray.DataArray, xarray.Dataset]
        Input data
    lat_bnds : list
        Latitude bounds: [south bound, north bound]

    Returns
    -------
    Union[xarray.DataArray, xarray.Dataset]
        Subsetted xarray.DataArray or xarray.Dataset
    """

    if 'latitude' in ds.dims:
        ds = ds.rename({'latitude': 'lat'})

    south_bound, north_bound = lat_bnds
    assert -90 <= south_bound <= 90, "Valid latitude range is [-90, 90]"
    assert -90 <= north_bound <= 90, "Valid latitude range is [-90, 90]"
    
    lat_axis = ds['lat'].values
    if lat_axis[-1] > lat_axis[0]:
        # monotonic increasing lat axis (e.g. -90 to 90)
        ds = ds.sel({'lat': slice(south_bound, north_bound)})
    else:
        # monotonic decreasing lat axis (e.g. 90 to -90)
        ds = ds.sel({'lat': slice(north_bound, south_bound)})

    return ds


def avoid_cyclic(ds, west_bound, east_bound):
    """Alter longitude axis if requested bounds straddle cyclic point"""

    west_bound_360 = (west_bound + 360) % 360
    east_bound_360 = (east_bound + 360) % 360
    west_bound_180 = ((west_bound + 180) % 360) - 180
    east_bound_180 = ((east_bound + 180) % 360) - 180
    if east_bound_360 < west_bound_360:
        ds = ds.assign_coords({'lon': ((ds['lon'] + 180) % 360) - 180})
        ds = ds.sortby(ds['lon'])
    elif east_bound_180 < west_bound_180:
        ds = ds.assign_coords({'lon': (ds['lon'] + 360) % 360}) 
        ds = ds.sortby(ds['lon'])

    return ds


def subset_lon(ds, lon_bnds):
    """Select grid points that fall within longitude bounds.

    Parameters
    ----------
    ds : Union[xarray.DataArray, xarray.Dataset]
        Input data
    lon_bnds : list
        Longitude bounds: [west bound, east bound]

    Returns
    -------
    Union[xarray.DataArray, xarray.Dataset]
        Subsetted xarray.DataArray or xarray.Dataset
    """

    if 'longitude' in ds.dims:
        ds = ds.rename({'longitude': 'lon'})
    assert ds['lon'].values.max() > ds['lon'].values.min()

    west_bound, east_bound = lon_bnds

    ds = avoid_cyclic(ds, west_bound, east_bound)

    lon_axis_max = ds['lon'].values.max()
    lon_axis_min = ds['lon'].values.min()
    if west_bound > lon_axis_max:
        west_bound = west_bound - 360
        assert west_bound <= lon_axis_max
    if east_bound > lon_axis_max:
        east_bound = east_bound - 360
        assert east_bound <= lon_axis_max
    if west_bound < lon_axis_min:
        west_bound = west_bound + 360
        assert west_bound >= lon_axis_min
    if east_bound < lon_axis_min:
        east_bound = east_bound + 360
        assert east_bound >= lon_axis_min

    ds = ds.sel({'lon': slice(west_bound, east_bound)})

    return ds

