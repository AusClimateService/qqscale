## qqscale

NOTE: THIS CODE IS STILL UNDER DEVELOPMENT AND IS NOT READY FOR BROAD USE.

This directory contains command line programs for empirical quantile mapping (a.k.a. quantile-quantile scaling). 

### Traditional methods

QQ-scaling is traditionally applied in one of two contexts:
- *Quantile mapping bias adjustment (QMBA)*:
  The difference (or ratio) between an observational dataset and historical model simulation is calculated for each quantile.
  Those quantile differences are then subtracted from (or ratios multiplied against) historical or future model data
  in order to produce a bias corrected historical or future model time series.
- *Quantile delta change (QDC)*:
  The difference (or ratio) between a future and historical model simulation is calculated for each quantile.
  Those quantile differences are then subtracted from (or ratios multiplied against) an observational dataset
  in order to produce a statistically downscaled climate projection time series.
  Otherwise known as quantile perturbation.

[Cannon et al (2015)](https://doi.org/10.1175/JCLI-D-14-00754.1) provides a nice clear summary of these traditional methods.

The scripts in this repository build on the relevant xclim functionality 
(namely [`xclim.sdba.adjustment.EmpiricalQuantileMapping`](https://xclim.readthedocs.io/en/stable/sdba.html))
in order to implement these traditional QQ-scaling methods.
The `calc_adjustment.py` script is used to calculate the adjustment factors (by month and quantile) between two datasets,
and then `apply_adjustment.py` is used to apply those adjustment factors to a given dataset.
Before calculating and applying adjustment factors,
the `apply_ssr.py` script can be used to apply singularity stochastic removal
([Vrac et al, 2016](https://doi.org/10.1002/2015JD024511)).
This helps avoid divide by zero issues associated with dry days in precipitation datasets. 

TODO: Add more detailed documentation on how to run these scripts.

### Additional methods

[Cannon et al (2015)](https://doi.org/10.1175/JCLI-D-14-00754.1) define
Detrended Quantile Mapping (DQM) and Quantile Delta Mapping (QDM),
both of which build upon the traditional methods.

TODO: Investigate implementing
[` xclim.sdba.adjustment.DetrendedQuantileMapping`](https://xclim.readthedocs.io/en/stable/sdba.html) and 
[`xclim.sdba.adjustment.QuantileDeltaMapping`](https://xclim.readthedocs.io/en/stable/sdba.html).

### Usage

If you're a member of the `wp00` project on NCI
(i.e. if you're part of the CSIRO Climate Innovation Hub),
the easiest way to use the scripts in this directory is to use the cloned copy at `/g/data/wp00/shared_code/qqscale/`.
They can be run using the Python environment at `/g/data/wp00/users/dbi599/miniconda3/envs/cih/bin/python`.

Alternatively, you can clone this GitHub repository
and run the code in a Python environment with the following libraries installed:
`xarray`, `netCDF4`, `dask`, `xclim`, `xesmf`  and `cmdline_provenance`.


### Questions

Questions or comments are welcome at the GitHub repostory
associated with the code:  
https://github.com/climate-resilient-enterprise/qqscale/issues
