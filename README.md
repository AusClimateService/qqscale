## qqscale

NOTE: THIS CODE IS STILL UNDER DEVELOPMENT AND IS NOT READY FOR BROAD USE.

This directory contains command line programs for producing future climate data
using the quantile-quantile scaling method.

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
