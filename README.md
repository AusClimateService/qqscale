# qqscale

This directory contains command line programs for empirical quantile mapping (a.k.a. quantile-quantile scaling). 

## Methods

QQ-scaling is traditionally applied in one of two contexts:
- *Quantile mapping bias adjustment (QMBA)*:
  The difference (or ratio) between an observational dataset and historical model simulation is calculated for each quantile.
  Those quantile differences are then subtracted from (or ratios multiplied against) model data
  in order to produce a bias corrected model time series.
- *Quantile delta change (QDC)*:
  The difference (or ratio) between a future and historical model simulation is calculated for each quantile.
  Those quantile differences are then subtracted from (or ratios multiplied against) an observational dataset
  in order to produce a statistically downscaled climate projection time series.
  Otherwise known as quantile perturbation.

Both methods can be achieved using this scripts in this repository (see examples below).

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

## Data processing
  
In general, QDC and QMBA can be achieved by running the following programs in sequence:
1. `apply_ssr.py` to apply Singularity Stochastic Removal (SSR) to all the data you'll be working with
   (optional: just for precipitation data when using multiplicative adjustment)
1. `calc_adjustment.py` to calculate the adjustment factors between an historical and reference dataset
   (in QDC the reference dataset is a future model simulation; in QMBA it is observations)
1. `calc_quantiles.py` to calculate the quantiles of the target data
   (i.e. the data to be adjusted - that's observational data for QDC or model data for QMBA)
1. `apply_adjustment.py` to apply the adjustment factors to the target data

In order to simplify the process of sequencing those steps
and making sure the outputs of one step are correctly input into the next,
a `Makefile` (see the `example_workflows` directory) has been produced.
The steps involved in using the `Makefile` are:
1. Create a configuration file based on `config_qdc.mk` or `config_qmba.mk`
1. Run `make all -f make_ssr.mk CONFIG=config_[method].mk` if SSR is required.
1. Run `make apply-adjustment CONFIG=config_[method].mk` to implement either QDC or QMBA

Additional processing steps for QDC
(e.g. applying standard CIH file metadata)
can be applied using `make_qdc_post-processing.mk`.
Help information can be viewed by running `make help -f make_qdc_post-processing.mk`.

## Questions

Questions or comments are welcome at the GitHub repostory
associated with the code:  
https://github.com/climate-resilient-enterprise/qqscale/issues
