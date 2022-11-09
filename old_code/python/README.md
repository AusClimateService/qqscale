This directory contains a Python implementation of QQ-scaling code adapted from:  
https://github.com/climate-resilient-enterprise/workflows/tree/master/notebooks/qq_scale

(Rakima Dey wrote the Python code at that link in early 2022.)

The `qqscale.py` module contains the functions used to perform QQ-scaling.
It can run using the `run_qqscale.py` command line program
or can be imported into your own scripts / notebooks.

For example,

```text
$ python run_qqscale.py /g/data/zv2/agcd/v1/tmax/mean/r005/01day/agcd_v1_tmax_mean_r005_daily_198[1,2,3,4,5].nc tmax tasmax 1 /g/data/wp00/dbi599/monthly_bias_adjusted_values.nc --hist_files /g/data/rr3/publications/CMIP5/output1/CSIRO-BOM/ACCESS1-3/historical/day/atmos/day/r1i1p1/latest/tasmax/tasmax_day_ACCESS1-3_historical_r1i1p1_19750101-19991231.nc /g/data/rr3/publications/CMIP5/output1/CSIRO-BOM/ACCESS1-3/historical/day/atmos/day/r1i1p1/latest/tasmax/tasmax_day_ACCESS1-3_historical_r1i1p1_20000101-20051231.nc --fut_files /g/data/rr3/publications/CMIP5/output1/CSIRO-BOM/ACCESS1-3/rcp45/day/atmos/day/r1i1p1/latest/tasmax/tasmax_day_ACCESS1-3_rcp45_r1i1p1_20060101-20301231.nc /g/data/rr3/publications/CMIP5/output1/CSIRO-BOM/ACCESS1-3/rcp45/day/atmos/day/r1i1p1/latest/tasmax/tasmax_day_ACCESS1-3_rcp45_r1i1p1_20310101-20551231.nc --hist_time_bounds 1975-01-01 2005-12-31 --fut_time_bounds 2021-01-01 2040-12-31 --obs_time_bounds 1981-01-01 1985-12-31
```

The following Python libraries are dependencies for running the code:
`xarray`, `netCDF4`, `dask`, `bottleneck`, `scipy`  and `cmdline_provenance`.
