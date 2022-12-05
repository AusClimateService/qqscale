# qqscale

This directory contains command line programs for empirical quantile mapping (a.k.a. quantile-quantile scaling). 

## Methods

### Traditional

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

[Cannon et al (2015)](https://doi.org/10.1175/JCLI-D-14-00754.1) provides a nice clear summary of these traditional methods
and [Boe et al (2007)](https://doi.org/10.1002/joc.1602) has a nice schematic (Figure 2) of how the mapping works.

The command line programs in this repository build on the relevant xclim functionality 
(namely [`xclim.sdba.adjustment.EmpiricalQuantileMapping`](https://xclim.readthedocs.io/en/stable/sdba.html))
in order to implement these traditional QQ-scaling methods.
The `calc_adjustment.py` script is used to calculate the adjustment factors (by month and quantile) between two datasets,
and then `apply_adjustment.py` is used to apply those adjustment factors to a given dataset.
Before calculating and applying adjustment factors,
the `apply_ssr.py` script can be used to apply singularity stochastic removal
([Vrac et al, 2016](https://doi.org/10.1002/2015JD024511)).
This helps avoid divide by zero issues associated with dry days in precipitation datasets. 

### Additional

[Cannon et al (2015)](https://doi.org/10.1175/JCLI-D-14-00754.1) define
Detrended Quantile Mapping (DQM) and Quantile Delta Mapping (QDM),
both of which build upon the traditional methods.

TODO: Investigate implementing
[` xclim.sdba.adjustment.DetrendedQuantileMapping`](https://xclim.readthedocs.io/en/stable/sdba.html) and 
[`xclim.sdba.adjustment.QuantileDeltaMapping`](https://xclim.readthedocs.io/en/stable/sdba.html).

## Software environment

### For members of the CSIRO Climate Innovation Hub...

If you're a member of the `wp00` project on NCI
(i.e. if you're part of the CSIRO Climate Innovation Hub),
the easiest way to use the scripts in this directory is to use the cloned copy at `/g/data/wp00/shared_code/qqscale/`.
They can be run using the Python environment at `/g/data/wp00/users/dbi599/miniconda3/envs/cih/bin/python`.

For example, to view the help information for the `apply_adjustment.py` script
a member of the `wp00` project could run the following:

```
$ /g/data/wp00/users/dbi599/miniconda3/envs/cih/bin/python /g/data/wp00/shared_code/qqscale/apply_adjustment.py -h
```

### For members of the Australian Climate Service...

If you're a member of the `xv83` project on NCI
(i.e. if you're part of the Australian Climate Service),
you'll need to clone this GitHub repository.

```
$ git clone git@github.com:climate-innovation-hub/qqscale.git
$ cd qqscale
```

You can then run the scripts using the Python environment at `/g/data/xv83/dbi599/miniconda3/envs/qqscale`. e.g.:

```
$ /g/data/xv83/dbi599/miniconda3/envs/qqscale/bin/python apply_adjustment.py -h
```

### For everyone else...

If you don't have access to a Python environment with the required packages
pre-installed you'll need to create your own.
For example:

```
$ conda install -c conda-forge xarray netCDF4 dask xclim xesmf cmdline_provenance gitpython
```

You can then clone this GitHub repository and run the help option
on one of the command line programs to check that everything is working.
For example:

```
$ git clone git@github.com:climate-innovation-hub/qqscale.git
$ cd qqscale
$ python calc_adjustment.py -h
```

## Examples

Reminders:
- Information about the input arguments for any of the command line programs
  can be viewed by using the `-h` option.
- While the examples below simply run `python`,
  you might use one of the pre-installed environments 
  (i.e. `/g/data/wp00/users/dbi599/miniconda3/envs/cih/bin/python` or
  `/g/data/xv83/dbi599/miniconda3/envs/qqscale/bin/python`
  if you're a member of those projects on NCI)
- While the examples below simply give the name of the command line program,
  you may use a copy of those scripts at `/g/data/wp00/shared_code/qqscale/`
  

### Example 1: Quantile delta change for daily maximum temperature

**Step 1:** Calculate the adjustment factors for the ACCESS-ESM1-5 model
between the historical (1995-2014) and ssp370 future (2035-2064) experiments
using the additive (as opposed to multiplicative) method.

```
$ python calc_adjustment.py tasmax tasmax adjustment-factors.nc --hist_files /g/data/fs38/publications/CMIP6/CMIP/CSIRO/ACCESS-ESM1-5/historical/r1i1p1f1/day/tasmax/gn/latest/tasmax_day_ACCESS-ESM1-5_historical_r1i1p1f1_gn_*.nc --ref_files /g/data/fs38/publications/CMIP6/ScenarioMIP/CSIRO/ACCESS-ESM1-5/ssp370/r1i1p1f1/day/tasmax/gn/latest/tasmax_day_ACCESS-ESM1-5_ssp370_r1i1p1f1_gn_*.nc --hist_time_bounds 1995-01-01 2014-12-31 --ref_time_bounds 2035-01-01 2064-12-31 --method additive --input_hist_units K --input_ref_units K --output_units C --verbose
```
The input data files are in Kelvin but we want to work in Celsius,
so the `--output_units` option was used to specify Celsius.

**Step 2:** Apply the adjustment factors to 30 years of AGCD data.

```
$ python apply_adjustment.py /g/data/xv83/agcd-csiro/tmax/daily/tmax_AGCD-CSIRO_r005_19100101-20220404_daily_space-chunked.zarr tmax adjustment-factors.nc tmax-qqscaled_2035-2064.nc --time_bounds 1990-01-01 2019-12-31 --ref_time --verbose
```

The `--ref_time` option adjusts the output time axis
so it starts at the same time as the future experiment (in this case, 2035-01-01).

### Example 2: Quantile delta change for daily precipitation

For precipitation it is common to use multiplicative (as opposed to additive) QQ-scaling
to avoid producing negative daily rainfall totals.
In order to avoid divide by zero issues associated with quantiles containing all dry days,
we provide a script for applying singularity stochastic removal
(SSR; [Vrac et al, 2016](https://doi.org/10.1002/2015JD024511) to each of the input datasets.
This basically takes all days with scarcely any rain (zero up to `8.64e-4`mm)
and replaces the daily rainfall total with a random value that lies between `0 > total > 8.64e-4`
so that no quantiles are zero.

**Step 1:** Apply SSR to each of the input datasets

```
$ python apply_ssr.py /g/data/fs38/publications/CMIP6/CMIP/CSIRO/ACCESS-ESM1-5/historical/r1i1p1f1/day/pr/gn/latest/pr_day_ACCESS-ESM1-5_historical_r1i1p1f1_gn_*.nc pr pr-ssr_day_ACCESS-ESM1-5_historical_r1i1p1f1_gn_19950101-20141231.nc --time_bounds 1995-01-01 2014-12-31 --input_units "kg m-2 s-1" --output_units "mm d-1"
```

```
$ python apply_ssr.py /g/data/fs38/publications/CMIP6/ScenarioMIP/CSIRO/ACCESS-ESM1-5/ssp370/r1i1p1f1/day/pr/gn/latest/pr_day_ACCESS-ESM1-5_ssp370_r1i1p1f1_gn_*.nc pr pr-ssr_day_ACCESS-ESM1-5_ssp370_r1i1p1f1_gn_20350101-20641231.nc --time_bounds 2035-01-01 2064-12-31 --input_units "kg m-2 s-1" --output_units "mm d-1"
```

```
$ python apply_ssr.py /g/data/xv83/agcd-csiro/precip/daily/precip-total_AGCD-CSIRO_r005_19000101-20220405_daily_space-chunked.zarr precip precip-total-ssr_AGCD-CSIRO_r005_19900101-20191231_daily.nc --time_bounds 1990-01-01 2019-12-31
```

**Step 2:** Calculate the adjustment factors for the ACCESS-ESM1-5 model
between the historical (1995-2014) and ssp370 future (2035-2064) experiments
using the multiplicative method.

```
$ python calc_adjustment.py pr pr adjustment-factors.nc --hist_files pr-ssr_day_ACCESS-ESM1-5_historical_r1i1p1f1_gn_19950101-20141231.nc --ref_files pr-ssr_day_ACCESS-ESM1-5_ssp370_r1i1p1f1_gn_20350101-20641231.nc --method multiplicative --hist_time_bounds 1995-01-01 2014-12-31 --ref_time_bounds 2035-01-01 2064-12-31 --verbose
```

**Step 3:** Apply the adjustment factors to 30 years of AGCD data.

```
$ python apply_adjustment.py precip-total-ssr_AGCD-CSIRO_r005_19900101-20191231_daily.nc precip adjustment-factors.nc pr-qqscaled_2035-2064.nc --verbose --ref_time --ssr
```

In this case the `--ssr` option reverses the singularity stochastic removal
after the QQ-scaling has been applied,
setting all days with scarely any rain (less than `8.64e-4`mm) back to zero.


## Questions

Questions or comments are welcome at the GitHub repostory
associated with the code:  
https://github.com/climate-resilient-enterprise/qqscale/issues
