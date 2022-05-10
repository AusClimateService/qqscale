## qqscale

### Method overview

Quantile-quantile scaling (QQ-scaling) is a technique designed to capture
important changes in the daily variance of weather variables.
It does this for each given location by computing change values on a set of quantiles
derived from the difference between daily historic GCM and future GCM data.
The change values corresponding to the quantiles (derived from the daily observed climate data)
are then applied to the daily observed data following these steps.

The QQ scale method is applied on daily data for each month,
extracted over a climatological historical and future period.
One hundred and one quantiles (0,1,2,…100) are calculated at each grid point
for both historical and future model simulations of a particular month.
A change factor is then calculated between historical and future data for each quantile. 

The reverse quantile is calculated using relevant baseline climatologies
(e.g., Australian Gridded Climate Data (AGCD) or ERA5 reanalysis data)
for a particular month over a defined baseline period (e.g., 1986-2005),
i.e., a quantile value is assigned to each daily value. 

The change factor for that particular quantile is applied
to the observed daily data to get projections data. 

Since the QQ-scaling method is applied on daily data for each month,
it conserves the seasonal variability in observational and model datasets.
The method attempts to minimise model biases as change in quantile is used instead of mean change. 
Finally, the QQ scaled data are corrected so that the change in climatological monthly mean
between observations and QQ-scaled data matches the GCM simulated change in monthly mean.


### Environment

The following Python libraries are dependencies for running the code:
`xarray`, `netCDF4`, `dask`, `xclim`, `xesmf`  and `cmdline_provenance`.


### Questions

Questions or comments are welcome at the GitHub repostory
associated with the code:  
https://github.com/climate-resilient-enterprise/qqscale/issues
