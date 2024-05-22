"""Utility functions"""

import os
import logging

import cftime
import git
import numpy as np
import xarray as xr
import xclim as xc
from xclim import sdba
from xclim.sdba import nbutils
import xesmf as xe

import cmdline_provenance as cmdprov


def get_outfile_encoding(ds, var, time_units=None, compress=False):
    """Define output file encoding."""

    encoding = {}
    ds_vars = list(ds.coords) + list(ds.keys())
    for ds_var in ds_vars:
        encoding[ds_var] = {'_FillValue': None}
    if compress:
        encoding[var]['least_significant_digit'] = 2
        encoding[var]['zlib'] = True
    if time_units:
        encoding['time']['units'] = time_units.replace('_', ' ')

    return encoding


def get_unique_dirnames(file_list):
    """Get a list of unique dirnames from a file list"""

    return list(set(map(os.path.dirname, file_list)))


def get_new_log(infile_logs={}, wildcard_prefixes=[]):
    """Generate command log for output file."""

    try:
        repo = git.Repo()
        repo_url = repo.remotes[0].url.split(".git")[0]
        commit_hash = str(repo.heads[0].commit)
        code_info = f'{repo_url}, {commit_hash[0:7]}'
    except (git.exc.InvalidGitRepositoryError, NameError):
        code_info = None
    new_log = cmdprov.new_log(
        infile_logs=infile_logs,
        code_url=code_info,
        wildcard_prefixes=wildcard_prefixes,
    )

    return new_log


def profiling_stats(rprof):
    """Record profiling information."""

    max_memory = np.max([result.mem for result in rprof.results])
    max_cpus = np.max([result.cpu for result in rprof.results])

    logging.info(f'Peak memory usage: {max_memory}MB')
    logging.info(f'Peak CPU usage: {max_cpus}%')


def convert_calendar(ds, output_calendar):
    """Convert time calendar."""

    valid_calendars = {
        cftime._cftime.DatetimeGregorian: cftime.DatetimeGregorian,
        cftime._cftime.DatetimeProlepticGregorian: cftime.DatetimeProlepticGregorian,
        cftime._cftime.DatetimeNoLeap: cftime._cftime.DatetimeNoLeap,
    }

    output_calendar_name = str(output_calendar).split('.')[-1][:-2]
    if output_calendar in valid_calendars:
        input_calendar_name = str(type(ds['time'].values[0])).split('.')[-1][:-2]
        output_calendar_name = str(output_calendar).split('.')[-1][:-2]
        logging.info(f'Convering input {input_calendar_name} calendar to {output_calendar_name}')

        is_noleap = output_calendar == cftime._cftime.DatetimeNoLeap
        if is_noleap:
            ds = ds.sel(time=~((ds['time'].dt.month == 2) & (ds['time'].dt.day == 29)))

        new_times = []
        calendar_func = valid_calendars[output_calendar]
        for old_time in ds['time'].values:
            new_time = calendar_func(old_time.year, old_time.month, old_time.day, old_time.hour)
            new_times.append(new_time)
        time_attrs = ds['time'].attrs
        ds = ds.assign_coords({'time': new_times})
        ds['time'].attrs = time_attrs

        if 'time_bnds' in ds:
            new_time_bnds = []
            for old_start, old_end in ds['time_bnds'].values:
                if is_noleap and (old_start.day == 29) and (old_start.month == 2):
                    old_start_day = 28
                    old_start_month = 2
                else:
                    old_start_day = old_start.day
                    old_start_month = old_start.month
                if is_noleap and (old_end.day == 29) and (old_end.month == 2):
                    old_end_day = 1
                    old_end_month = 3
                else:
                    old_end_day = old_end.day
                    old_end_month = old_end.month
                new_start = calendar_func(old_start.year, old_start_month, old_start_day, old_start.hour)
                new_end = calendar_func(old_end.year, old_end_month, old_end_day, old_end.hour)
                time_diff = new_end - new_start
                assert time_diff == np.timedelta64(1, 'D')
                new_time_bnds.append([new_start, new_end])

            da_time_bnds = xr.DataArray(
                new_time_bnds,
                dims=ds['time_bnds'].dims,
                coords={"time": ds['time']},
            )
            ds['time_bnds'] = da_time_bnds
    else:
        raise ValueError(f'Conversion to {output_calendar_name} not supported')

    return ds


def joules_to_watts(da):
    """Convert from Joules to Watts"""

    input_units = da.attrs["units"]
    input_freq = xr.infer_freq(da.indexes['time'][0:3])[0]
    assert input_freq == 'D'

    if (input_units[0] == 'M') or (input_units[0:4] == 'mega'):
        da = da * 1e6
    seconds_in_day = 60 * 60 * 24
    da = da / seconds_in_day

    return da


def convert_units(da, target_units):
    """Convert units.

    Parameters
    ----------
    da : xarray DataArray
        Input array containing a units attribute
    target_units : str
        Units to convert to

    Returns
    -------
    da : xarray DataArray
       Array with converted units
    """

    custom_conversions = {
        ("MJ m-2", "W m-2"): joules_to_watts,
        ("megajoule/meter2", "W m-2"): joules_to_watts,
    }
    try:
        da = xc.units.convert_units_to(da, target_units)
    except Exception as e:
        var_attrs = da.attrs
        conversion = (da.attrs["units"], target_units)
        if conversion in custom_conversions:
            da = custom_conversions[conversion](da)
            da.attrs = var_attrs
        else:
            raise e

    return da


def read_data(
    infiles,
    input_var,
    rename_var=None,
    time_bounds=None,
    lat_bounds=None,
    lon_bounds=None,
    input_units=None,
    output_units=None,
    lon_chunk_size=None,
    apply_ssr=False,
    use_cftime=True,
    output_calendar=None,
    valid_min=None,
    valid_max=None,
):
    """Read and process an input dataset.

    Parameters
    ----------
    infiles : list
        Input files    
    input_var : str, optional
        Variable to read from infiles
    rename_var : str, optional
        Rename var to value of rename_var
    time_bounds : list, optional
        Time period to extract from infiles [YYYY-MM-DD, YYYY-MM-DD]
    lat_bnds : list, optional
        Latitude bounds: [south bound, north bound] 
    lon_bnds : list, optional
        Longitude bounds: [west bound, east bound]    
    input_units : str, optional
        Units of input data (if not provided will attempt to read file metadata)
    output_units : str, optional
        Desired units for output data (conversion will be applied if necessary)
    lon_chunk_size : int, optional
        Put this number of longitudes in each data chunk
    apply_ssr : bool, default False
        Apply Singularity Stochastic Removal to the data
    use_cftime : bool, default True
        Use cftime for time axis
    output_calendar : cftime calendar, optional
        Desired calendar for output data
    valid_min : float, optional
        Clip data to valid minimum value
    valid_max : float, optional
        Clip data to valid maximum value

    Returns
    -------
    ds : xarray Dataset

    """

    if len(infiles) == 1:
        try:
            ds = xr.open_dataset(infiles[0], use_cftime=use_cftime)
        except ValueError:
            ds = xr.open_dataset(infiles[0])
    else:
        try:
            ds = xr.open_mfdataset(infiles, use_cftime=use_cftime)
        except ValueError:
            ds = xr.open_mfdataset(infiles)

    try:
        ds = ds.drop('height')
    except ValueError:
        pass

    if rename_var:
        ds = ds.rename({input_var: rename_var})
        var = rename_var
    else:
        var = input_var
        
    if 'latitude' in ds.dims:
        ds = ds.rename({'latitude': 'lat'})
    if 'longitude' in ds.dims:
        ds = ds.rename({'longitude': 'lon'})

    if time_bounds:
        start_date, end_date = time_bounds
        ds = ds.sel({'time': slice(start_date, end_date)})        
    if lat_bounds:
        ds = subset_lat(ds, lat_bounds)
    if lon_bounds:
        ds = subset_lon(ds, lon_bounds)

    if output_calendar:
        input_calendar = type(ds['time'].values[0])
        if input_calendar != output_calendar:
            ds = convert_calendar(ds, output_calendar)  

    if input_units:
        ds[var].attrs['units'] = input_units
    if output_units:
        ds[var] = convert_units(ds[var], output_units)
        ds[var].attrs['units'] = output_units

    if (valid_min is not None) or (valid_max is not None):
        ds[var] = ds[var].clip(min=valid_min, max=valid_max, keep_attrs=True)

    chunk_dict = {'time': -1}
    if lon_chunk_size:
        chunk_dict['lon'] = lon_chunk_size
    ds = ds.chunk(chunk_dict)
    logging.info(f'Array size: {ds[var].shape}')
    logging.info(f'Chunk size: {ds[var].chunksizes}')
    
    return ds


def apply_ssr(da, threshold='8.64e-4 mm day-1'):
    """Apply Singularity Stochastic Removal.

    Used to avoid divide by zero errors in the analysis of precipitation data.
    All near-zero values (i.e. < threshold) are set to a small random non-zero value:
    0 < value <= threshold
    
    Parameters
    ----------
    da : xarray DataArray
        Input precipitation data
    threhsold : str, default '8.64e-4 mm day-1'
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

    da_ssr = sdba.processing.jitter_under_thresh(da, '8.64e-4 mm day-1')

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

    da_no_ssr = da_ssr.where(da_ssr >= threshold, 0.0)

    return da_no_ssr


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

