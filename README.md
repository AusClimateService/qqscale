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

### Code

The `qqscale.py` module contains the functions used to perform QQ-scaling.
It can run using the `run_qqscale.py` command line program
or can be imported into your own scripts / notebooks.

For example,

```text
$ python run_qqscale.py \
  /g/data/zv2/agcd/v1/tmax/mean/r005/01day/agcd_v1_tmax_mean_r005_daily_198[1,2,3,4,5].nc \
  tmax tasmax 1 \
  /g/data/wp00/dbi599/monthly_bias_adjusted_values.nc \
  --hist_files /g/data/rr3/CMIP5/output1/CSIRO-BOM/ACCESS1-3/historical/day/atmos/day/r1i1p1/latest/tasmax/tasmax_day_ACCESS1-3_historical_r1i1p1_20000101-20051231.nc \
  --fut_files /g/data/rr3/CMIP5/output1/CSIRO-BOM/ACCESS1-3/rcp45/day/atmos/day/r1i1p1/latest/tasmax/tasmax_day_ACCESS1-3_rcp45_r1i1p1_20060101-20301231.nc \
  --hist_time_bounds 1975-01-01 2005-12-31 \
  --fut_time_bounds 2021-01-01 2040-12-31 \
  --obs_time_bounds 1981-01-01 1985-12-31 
```

### Environment

The following Python libraries are dependencies for running the code:
`xarray`, `netCDF4`, `dask`,  and `cmdline_provenance`.


### Questions

Questions or comments are welcome at the GitHub repostory
associated with the code:  
https://github.com/climate-resilient-enterprise/issues