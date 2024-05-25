# qqscale

[![tests](https://github.com/climate-innovation-hub/qqscale/actions/workflows/tests.yml/badge.svg)](https://github.com/climate-innovation-hub/qqscale/actions/workflows/tests.yml)

This directory contains command line programs for applying quantile scaling. 

## Methods

The programs in this repository use the
[bias adjustment and downscaling](https://xclim.readthedocs.io/en/stable/sdba.html)
functionality in xclim to apply quantile scaling.

Depending on the context, there are two different ways the programs can be used:
- To apply *quantile delta changes* (QDC) between an historical and future model simulation
  either additively or multiplicatively to observational data in order to produce
  climate projection data for a future time period.
- To remove quantile biases between an historical model simulation and observations
  from model data in order to produce bias corrected model data.
  This has been referred to as
  *equidistant CDF matching* (EDCDFm; in the case of additive bias correction; [Li et al, 2010](https://doi.org/10.1029/2009JD012882)) or
  *equiratio CDF matching* (EQCDFm; in the case of multiplicative bias correction; [Wang and Chen, 2013](https://doi.org/10.1002/asl2.454)).

See [docs/method_ecdfm.md](docs/method_ecdfm.md) and [docs/method_qdc.md](docs/method_qdc.md) for a detailed description
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

### For members of the Australian Climate Service...

If you're a member of the `xv83` project on NCI
(i.e. if you're part of the Australian Climate Service),
you have access the code and an appropriate conda environment
at `/g/data/xv83/quantile-mapping`.

You can therefore run the scripts as follows. e.g.:

```
$ /g/data/xv83/quantile-mapping/miniconda3/envs/qq-workflows/bin/python /g/data/xv83/quantile-mapping/qqscale/adjust.py -h
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
$ git clone git@github.com:AusClimateService/qqscale.git
$ cd qqscale
$ python adjust.py -h
```

## Data processing

### Command line
  
At the command line, QDC and/or ECDFm can be achieved by running the following scripts:
1. `train.py` to calculate the adjustment factors between an *historical* and *reference* dataset
   (in QDC the reference dataset is a future model simulation; in ECDFm it is observations)
1. `adjust.py` to apply the adjustment factors to the *target* data
   (in QDC the target data is observations; in ECDFm it is a model simulation)

See the files named `docs/example_*.md` for detailed worked examples using these two command line programs.

### Jupyter notebook

Starting with historical (`ds_hist`), reference (`ds_ref`) and target (`ds_target`) xarray Datasets
containing the variable of interest (`hist_var`, `ref_var` and `target_var`)
you can import the relevant functions from the scripts mentioned above.
For instance,
a QDC workflow would look something like this:

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

EDCDFm with 30 years of daily CORDEX and AGCD data (on AUS-05i 691 x 886 horizontal grid):
- Training step: Compute (1 core) requires 250GB and 1hr 30min. Produces 1.3GB adjustment factor file.
- Adjustment step: Compute (1 core) requires 185GB and 1hr 50min. Produces output files of approx 200MB per year.
- Regridding the target data prior to performing the adjustment makes very little difference to processing time.

EDCDFm with 20 years of daily CORDEX and AGCD data (on AUS-20i 171 x 211 horizontal grid):
- Training step: Compute (1 core) requires 7.3GB and 3min.
- Adjustment step: Compute (1 core) requires 7.9GB and 4min.

## Questions

Questions or comments are welcome at the GitHub repostory
associated with the code:  
https://github.com/AusClimateService/qqscale/issues
