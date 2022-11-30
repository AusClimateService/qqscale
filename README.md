## qqscale

NOTE: THIS CODE IS STILL UNDER DEVELOPMENT AND IS NOT READY FOR BROAD USE.

This directory contains command line programs for empirical quantile mapping (a.k.a. quantile-quantile scaling). 

QQ-scaling is typically applied in one of two contexts:
- *Quantile mapping bias adjustment (QMBA)*:
  The difference (or ratio) between an observational dataset and historical model simulation is calculated for each quantile.
  Those quantile differences are then subtracted from (or ratios multiplied against) historical or future model data
  in order to produce a bias corrected historical or future model time series.
- *Quantile mapping delta change (QMDC)*:
  The difference (or ratio) between a future and historical model simulation is calculated for each quantile.
  Those quantile differences are then subtracted from (or ratios multiplied against) an observational dataset
  in order to produce a statistically downscaled climate projection time series.

The programs make use of the “Bias Adjustment and Downscaling Algorithms” capability built into the xclim library,
which is described at: https://xclim.readthedocs.io/en/stable/sdba.html

If you're a member of the `wp00` project on NCI
(i.e. if you're part of the CSIRO Climate Innovation Hub),
the easiest way to use the scripts in this directory is to use the cloned copy at `/g/data/wp00/shared_code/qqscale/`.
They can be run using the Python environment at `/g/data/wp00/users/dbi599/miniconda3/envs/cih/bin/python`.

Alternatively, you can clone this GitHub repository
and run the code in a Python environment with the following libraries installed:
`xarray`, `netCDF4`, `dask`, `xclim`, `xesmf`  and `cmdline_provenance`.

The data processing is a two step process.
The `calc_adjustment.py` script is used to calculate the adjustment factors
for a given CMIP experiment and time period (e.g. RCP4.5 for 1995-2014 to 2040-2059),
and then `apply_adjustment.py` is used to apply those adjustment factors
to a given observational dataset (e.g. AGCD data from 1995-2014).

TODO: Add documentation on how to run these two scripts.

### Questions

Questions or comments are welcome at the GitHub repostory
associated with the code:  
https://github.com/climate-resilient-enterprise/qqscale/issues
