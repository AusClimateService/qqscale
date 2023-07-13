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

See [method_ecdfm.md](method_ecdfm.md) and [method_qdm.md](method_qdm.md) for a detailed description
of these methods and how they are implemented in the qqscale software.

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

### Command line
  
At the command line, QDM and/or ECDFm can be achieved by running the following scripts:
1. `train.py` to calculate the adjustment factors between an *historical* and *reference* dataset
   (in QDM the reference dataset is a future model simulation; in ECDFm it is observations)
1. `adjust.py` to apply the adjustment factors to the *target* data
   (in QDM the target data is observations; in ECDFm it is a model simulation)

### Jupyter notebook

Starting with historical (`ds_hist`), reference (`ds_ref`) and target (`ds_target`) xarray Datasets
containing the variable of interest (`hist_var`, `ref_var` and `target_var`)
you can import the relevant functions from the scripts mentioned above.
For instance,
a QDM workflow would look something like this:

```python

import train
import adjust


ds_adjust = train.train(
    ds_hist,
    ds_ref,
    hist_var,
    ref_var,
    scaling='additive',  # use multiplicative for precip data
    time_grouping='monthly',
    nquantiles=100,
    ssr=False,  # Use True for precip data
)
ds_qq = adjust.adjust(
    ds_target,
    target_var,
    ds_adjust,
    ssr=False,  # Use True for precip data
    ref_time=True,
    interp='nearest', 
)
```

### Performance

The adjustment step (`adjust.py`) is the most time and memory intensive.
Here's some examples of time and memory requirements for different applications:
- 30 years of daily AGCD data (691 x 886 horizontal grid) running on 1 core: 220GB, 2 hours 

## Questions

Questions or comments are welcome at the GitHub repostory
associated with the code:  
https://github.com/climate-innovation-hub/qqscale/issues
