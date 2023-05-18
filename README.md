# qqscale

[![tests](https://github.com/climate-innovation-hub/qqscale/actions/workflows/tests.yml/badge.svg)](https://github.com/climate-innovation-hub/qqscale/actions/workflows/tests.yml)

This directory contains command line programs for quantile mapping (a.k.a. quantile-quantile scaling). 

## Methods

The programs in this repository use the
[bias adjustment and downscaling](https://xclim.readthedocs.io/en/stable/sdba.html) functionality in xclim
to apply what is essentially the most basic method of quantile mapping used in the literature.

Depending on the context, there are few different names for this basic method:
- If quantile delta changes (e.g. between an historical and future model simulation) are applied
  either additively or multiplicatively to observational data in order to produce
  climate projection data for a future time period,
  the method we apply has been referred to as
  *Quantile Delta Mapping* (QDM; [Cannon et al 2015](https://doi.org/10.1175/JCLI-D-14-00754.1)).
- If quantile biases (e.g. between an historical model simulation and observations) are removed
  from model data in order to produce bias corrected model data,
  the method we apply has been referred to as
  *equidistant CDF matching* (EDCDFm; in the case of additive bias correction; [Li et al, 2010](https://doi.org/10.1029/2009JD012882)) or
  *equiratio CDF matching* (EQCDFm; in the case of multiplicative bias correction; [Wang and Chen, 2013](https://doi.org/10.1002/asl2.454)).

As explained by [Cannon et al (2015)](https://doi.org/10.1175/JCLI-D-14-00754.1),
additive/multiplicative Quantile Delta Mapping is actually equivalent to equidistant/equiratio CDF matching.
In other words, you get the same result regardless of whether you apply
model delta changes to observational data or bias correct model data.
See the [developer notes](developer_notes.md) for details.


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
  
In general, QDM and/or CDFm can be achieved using the following scripts:
1. (optional) `ssr.py` to apply Singularity Stochastic Removal (SSR) to the input data
   (just for precipitation data when using multiplicative adjustment)
1. `train.py` to calculate the adjustment factors between an *historical* and *reference* dataset
   (in QDM the reference dataset is a future model simulation; in CDFm it is observations)
1. `adjust.py` to apply the adjustment factors to the *target* data
   (in QDM the target data is observations; in CDFm it is a model simulation)
1. (optional) `match_mean_change.py` to match up the model and QDM mean change 

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
1. Create a configuration file (e.g. `my_config.mk`) based on `config_qdm.mk` or `config_cdfm.mk`
1. Run `make all -f make_ssr.mk CONFIG=my_config.mk` if SSR is required.
1. Run `make apply-adjustment CONFIG=my_config.mk` to implement either QDM or CDFm

Additional processing steps for QDM
(e.g. applying standard CIH file metadata or matching the mean change)
can be applied using `make_qdm_post-processing.mk`.
Help information can be viewed by running `make help -f make_qdm_post-processing.mk`.

#### Performance

The adjustment step (`adjust.py`) is the most time and memory intensive.
Here's some examples of time and memory requirements for different applications:
- 30 years of daily AGCD data (691 x 886 horizontal grid) running on 1 core: 195GB, 5 hours 


### Smaller datasets

When processing a smaller dataset it is also possible to perform the entire QQ-scaling process
from within a single script/notebook.
Starting with historical (`ds_hist`), reference (`ds_ref`) and target (`ds_target`) xarray Datasets
containing the variable of interest (`hist_var`, `ref_var` and `target_var`)
you can import the relevant functions from the scripts mentioned above.
For instance,
a QDM workflow would look something like this:

```python

import ssr
import train
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
ds_qq = adjust.adjust(
    ds_target,
    target_var,
    ds_adjust,
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
