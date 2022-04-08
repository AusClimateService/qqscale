"""Functions for QQ-scale analysis."""

import logging
import operator
import time

import xarray as xr

import file_attributes


def qqscale(da_obs, da_hist, da_fut, month, bias_method):
    """Quantile-quantile scaling.
    
    Parameters
    ----------
    da_obs : xarray DataArray
        Observational data
    da_hist : xarray DataArray
        Historical model data
    da_fut : xarray DataArray
        Future model data

    Returns
    -------
    ds_qqscale : xarray Dataset
        QQ-scaled data and associated information (e.g. percentiles, change factors)
    """
    
    time_start = time.perf_counter()
    
    lats = da_obs['lat'].values
    lons = da_obs['lon'].values
    percentiles = xr.DataArray(np.linspace(0, 1, num=101))
    
    logging.info('Processing historical model data ...')
    hist_mon_selection = da_hist['time'].dt.month.isin([month])
    da_hist_month = da_hist.sel({'time': hist_mon_selection})
    da_hist_month_mean = da_hist_month.mean('time')
    da_hist_month_mean_interp = da_hist_month_mean.interp(lat=lats, lon=lons, kwargs={"fill_value": "extrapolate"}) 
    da_hist_month_perc = calc_percentiles(da_hist_month, percentiles)
    da_hist_month_perc_interp = da_hist_month_perc.interp(lat=lats, lon=lons, kwargs={"fill_value": "extrapolate"})
    
    logging.info('Processing future model data ...')
    fut_mon_selection = da_fut['time'].dt.month.isin([month])
    da_fut_month = da_fut.sel({'time': fut_mon_selection})
    da_fut_month_mean = da_fut_month.mean('time')
    da_fut_month_mean_interp = da_fut_month_mean.interp(lat=lats, lon=lons, kwargs={"fill_value": "extrapolate"}) 
    da_fut_month_perc = calc_percentiles(da_fut_month, percentiles)
    da_fut_month_perc_interp = da_fut_month_perc.interp(lat=lats, lon=lons, kwargs={"fill_value": "extrapolate"})

    logging.info('Processing observational data ...')
    obs_mon_selection = da_obs['time'].dt.month.isin([month])
    da_obs_month = da_obs.sel({'time': obs_mon_selection})
    da_obs_month_perc = calc_percentiles(da_obs_month, percentiles)
    
    logging.info('Performing scaling...')
    MO_corrected, change_month = apply_scaling(
        da_obs_month,
        da_obs_month_perc,
        da_hist_month_perc_interp,
        da_fut_month_perc_interp,
        method,
    )
    
    ds_qqscale = xr.Dataset()
    ds_qqscale["lat"] = da_obs['lat']
    ds_qqscale["lon"] = da_obs['lon']
    ds_qqscale["time"] =  MO_corrected['time']
    ds_qqscale["data_month"] = MO_corrected
    ds_qqscale["hist_percentile"] = da_hist_month_perc
    ds_qqscale["fut_percentile"] = da_fut_month_perc
    ds_qqscale["hist_percentile_interp"] = da_hist_month_perc_interp
    ds_qqscale["fut_percentile_interp"] = da_fut_month_perc_interp
    ds_qqscale["change_factor"] = change_month
    
    qqscale.attrs.update(file_attributes.global_atts)
    ds_qqscale.lat.attrs = file_attributes.lat_dim
    ds_qqscale.lon.attrs = file_attributes.lon_dim
    ds_qqscale.time.attrs = file_attributes.time_dim
    ds_qqscale.data_month = file_attributes.data_month_dim
    
    time_end = time.perf_counter()
    logging.info('Duration = {0} minutes'.format((time_end - time_start) / 60.0) )
    
    return ds_qqscale


def apply_scaling(
    da_obs_month,
    da_obs_month_perc,
    da_hist_month_perc_interp,
    da_fut_month_perc_interp,
    method
):
    """Apply QQ-scaling method.
    
    Parameters
    ----------
    da_obs_month : xarray DataArray
        Observational data for a particular month
    da_obs_month_perc : xarray DataArray
        Observational percentiles for a particular month
    da_hist_month_perc_interp : xarray DataArray
        Historical model percentiles for a particular month interpolated to the obs grid
    da_fut_month_perc_interp : xarray DataArray
        Future model percentiles for a particular month interpolated to the obs grid
    method

    Returns
    -------
    ds : xarray Dataset
    
  
    """
    
    if method == "additive":
        op = operator.sub
    elif method == "multiplicative":
        op = operator.truediv
    else:
        raise ValueError(f"Unrecognised scaling method: {method}")
    change_month = op(ds_fut_month_perc_interp, ds_hist_month_perc_interp)
    change_month_stack = change_month.stack(z={"lat", "lon"})

    ds_obs_month_ranked = ds_obs_month.load().rank(dim="time", pct=True, keep_attrs=True) * 100
    ds_obs_month_loc = ds_obs_month_ranked.round()
    ds_obs_month_perc_stack = ds_obs_month_perc.stack(z={"lat", "lon"})
    ds_obs_month_loc_stack = ds_obs_month_loc.stack(z={"lat", "lon"})
    ds_obs_month_stack = ds_obs_month.stack(z={"lat", "lon"})

    temp_var = np.zeros(np.shape(ds_obs_month_loc_stack))
    temp_var = xr.DataArray(data=temp_var, dims=["time", "z"], coords=ds_obs_month_loc_stack.coords)
    
    logging.info("Applying the change factor ...')
    for tt in range(ds_obs_month_stack.time.size):
        if (tt+1) % 10 == 0:
            logging.info("{0} of {1}".format(tt+1, len(ds_obs_month_stack.time)))
        temp_var1 = ds_obs_month_loc_stack[tt,:].astype(int).drop("z")
        temp_var2 = temp_var1.where(temp_var1 < 100, 99)
        temp_var3 = change_month_stack.drop('z')[temp_var1, :]
        change_factor = (ds_obs_month_stack[tt,:] - ds_obs_month_perc_stack[temp_var2, :])
            / (ds_obs_month_perc_stack[temp_var2+1, :] - ds_mon_obs_month_perc_stack[temp_var2, :])
        change_factor_updated = (1 - change_factor) * temp_var3 + change_factor * change_month_stack[temp_var2+1, :]
        change_factor_updated = change_factor_updated.fillna(0)
        temp_var4 = ds_obs_month_stack[tt,:] + change_factor_updated
        temp_var[tt,:] = temp_var4.drop({'z'})       
    ds_obs_month_adjusted = temp_var.unstack()
        
    ratio1 = ds_obs_month_adjusted.mean('time') - ds_obs_month.mean('time')
    ratio2 = ds_fut_month_mean_interp - ds_hist_month_mean_interp
    bias_factor = ratio2 - ratio1
    MO_corrected = ds_obs_month_adjusted + bias_factor

    return MO_corrected, change_month 


def calc_percentiles(ds, percentiles):
    """Calculate percentiles"""
    
    ds = ds.chunk(chunks={"lat": 10, "lon": 10, "time": -1})
    ds_perc = ds.quantile(
        percentiles,
        dim="time",
        interpolation="linear",
        keep_attrs=True,
        skipna=True
    ).compute()
    
    return ds_prec
