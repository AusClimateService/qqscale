# qqscale

[![tests](https://github.com/climate-innovation-hub/qqscale/actions/workflows/tests.yml/badge.svg)](https://github.com/climate-innovation-hub/qqscale/actions/workflows/tests.yml)

This directory contains command line programs for empirical quantile mapping (a.k.a. quantile-quantile scaling). 

## Methods

QQ-scaling is traditionally applied in one of two contexts:
- *Quantile mapping bias adjustment (QMBA)*:
  The difference (or ratio) between an observational dataset and historical model simulation is calculated for each quantile.
  Those quantile differences are then added to (or ratios multiplied against) model data
  in order to produce a bias corrected model time series.
- *Quantile delta change (QDC)*:
  The difference (or ratio) between a future and historical model simulation is calculated for each quantile.
  Those quantile differences are then added to (or ratios multiplied against) an observational dataset
  in order to produce a statistically downscaled climate projection time series.
  Otherwise known as quantile perturbation.

Both methods can be achieved using this scripts in this repository (see examples below).

## Software environment

The scripts in this respository depend on the following Python libraries:
[netCDF4](https://unidata.github.io/netcdf4-python/),
[xclim](https://xclim.readthedocs.io),
[xesmf](https://xesmf.readthedocs.io),
[cmdline_provenance](https://cmdline-provenance.readthedocs.io),
[gitpython](https://gitpython.readthedocs.io),
and [pytest](https://docs.pytest.org) (if running the tests).
A copy of the scripts and a software environment with those libraries installed
can be accessed or created in a number of ways (see below):

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
$ conda install -c conda-forge netCDF4 xclim xesmf cmdline_provenance gitpython
```

You can then clone this GitHub repository and run the help option
on one of the command line programs to check that everything is working.
For example:

```
$ git clone git@github.com:climate-innovation-hub/qqscale.git
$ cd qqscale
$ python calc_adjustment.py -h
```

## Data processing
  
In general, QDC and QMBA can be achieved using the following scripts:
1. (optional) `ssr.py` to apply Singularity Stochastic Removal (SSR) to the input data
   (just for precipitation data when using multiplicative adjustment)
1. `train.py` to calculate the adjustment factors between an *historical* and *reference* dataset
   (in QDC the reference dataset is a future model simulation; in QMBA it is observations)
1. `quantiles.py` to calculate the quantiles of the *target* data
   (i.e. the data to be adjusted - that's observational data for QDC or model data for QMBA)
1. `adjust.py` to apply the adjustment factors to the target data
1. (optional) `match_mean_change.py` to match up the GCM and QDC mean change 

### Large datasets

For large datasets (e.g. Australia at 5km spatial resolution)
it is desirable to break QQ-scaling into a number of steps.
This helps reduce the indcidence of memory errors or large complicated dask task graphs,
and by producing intermediary files at each step you can avoid repeating some steps in future.

This step-by-step process can be achieved by running the scripts listed above
(in the order presented) as command line programs.
A `Makefile` is available to simplify the process of sequencing the steps
and to make sure the outputs of one step are correctly input into the next.
The steps involved in using the `Makefile` are:
1. Create a configuration file (e.g. `my_config.mk`) based on `config_qdc.mk` or `config_qmba.mk`
1. Run `make all -f make_ssr.mk CONFIG=my_config.mk` if SSR is required.
1. Run `make apply-adjustment CONFIG=my_config.mk` to implement either QDC or QMBA

Additional processing steps for QDC
(e.g. applying standard CIH file metadata or matching the mean change)
can be applied using `make_qdc_post-processing.mk`.
Help information can be viewed by running `make help -f make_qdc_post-processing.mk`.

### Smaller datasets

When processing a smaller dataset it is also possible to perform the entire QQ-scaling process
from within a single script/notebook.
Starting with historical (`ds_hist`), reference (`ds_ref`) and target (`ds_target`) xarray Datasets
containing the variable of interest (`hist_var`, `ref_var` and `target_var`)
you can import the relevant functions from the scripts mentioned above.
For instance,
a QDC workflow would look something like this:

```python

import ssr
import train
import quantiles
import adjust
import match_mean_change


scaling = 'additive'
apply_ssr = False  # Use True for precip data
mean_match = False

if apply_ssr:
    ds_hist[hist_var] = ssr.apply_ssr(ds_hist[hist_var])
    ds_ref[ref_var] = ssr.apply_ssr(ds_ref[ref_var])
    ds_target[target_var] = ssr.apply_ssr(ds_target[target_var])

ds_adjust = train.train(ds_hist, ds_ref, hist_var, ref_var, scaling)
ds_target_q = quantiles.quantiles(ds_target, target_var, 100)
ds_qq = adjust.adjust(
    ds_target,
    target_var,
    ds_adjust,
    da_q=ds_target_q[target_var],
    reverse_ssr=apply_ssr,
    ref_time=True
)

if mean_match:
    match_timescale = 'annual'  # can be annual or monthly   
    ds_qq_mmc = match_mean_change.match_mean_change(
        ds_qq,
        target_var,
        ds_hist[hist_var],
        da_ref[ref_var],
        da_target[target_var],
        scaling,
        match_timescale
    )
```

## Questions

Questions or comments are welcome at the GitHub repostory
associated with the code:  
https://github.com/climate-innovation-hub/qqscale/issues
