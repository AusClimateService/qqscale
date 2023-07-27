# Worked example: CIH

The CSIRO Climate Innovation Hub (CIH) intends produce
application ready climate projections data
by applying relative changes simulated by CMIP6 global climate models
to observational data.

The following example describes how to produce projections data
for the 2056-2085 period using the quantile delta mapping method
(see [method_qdm.md](method_qdm.md) for details)
for a given variable (pr),
global climate model (ACCESS-ESM1-5),
model experiment (ssp370),
model run (r1i1p1f1),
observation reference period (1990-2019 = "2005")
and historical model baseline (1995-2014 = "2005").

> **Shortcut**
>
> You'll see in steps 1-3 below that there are lots of
> positional arguments and program options/flags to remember,
> which means it can be easy to forget something or make an error.
>
> If you don't already have a process for managing complicated workflows like this,
> using a build tool like Make can be helpful.
> The Makefile and CIH configuation file at https://github.com/climate-innovation-hub/qq-workflows
> have been built to coordinate the bias correction workflow described below.
>
> To run steps 1-3 below,
> you could simply clone the qq-workflows repo and run the following at the command line:
> ```
> git clone git@github.com:climate-innovation-hub/qq-workflows.git
> cd qq-workflows
> make validation CONFIG=cih/config_cih.mk VAR=pr MODEL=ACCESS-ESM1-5 EXPERIMENT=ssp370 RUN=r1i1p1f1 REF_START=2056 REF_END=2085
> ```

## Step 1: Training

The `train.py` command line program can be used to compare future and historical model data
in order to produce the "adjustment factors" that need to be applied to observations in the adjustment step.
You can run `python train.py -h` at the command line to view the positional arguments
and options/flags associated with the program.
To give an example,
the options/flags for the CIH projections described above would be as follows...

The `--hist_files` flag is used to specify the historical model data files
(in this case for the 1995-2014 reference period):
```
--hist_files
/g/data/fs38/publications/CMIP6/CMIP/CSIRO/ACCESS-ESM1-5/historical/r1i1p1f1/day/pr/gn/v20191115/pr_day_ACCESS-ESM1-5_historical_r1i1p1f1_gn_19500101-19991231.nc
/g/data/fs38/publications/CMIP6/CMIP/CSIRO/ACCESS-ESM1-5/historical/r1i1p1f1/day/pr/gn/v20191115/pr_day_ACCESS-ESM1-5_historical_r1i1p1f1_gn_20000101-20141231.nc
```

The `--ref_files` flag is used to specify the reference ssp370 data files:

```
--ref_files
/g/data/fs38/publications/CMIP6/ScenarioMIP/CSIRO/ACCESS-ESM1-5/ssp370/r1i1p1f1/day/pr/gn/v20191115/pr_day_ACCESS-ESM1-5_ssp370_r1i1p1f1_gn_20150101-20641231.nc
/g/data/fs38/publications/CMIP6/ScenarioMIP/CSIRO/ACCESS-ESM1-5/ssp370/r1i1p1f1/day/pr/gn/v20191115/pr_day_ACCESS-ESM1-5_ssp370_r1i1p1f1_gn_20650101-21001231.nc
```

There are a number of other flags that are also required to complete this task:
- `--scaling multiplicative`: Multiplicative scaling is typically used for rainfall (and `additive` for temperature).
- `--nquantiles 100`: We like to use 100 quantiles.
- `--input_hist_units "kg m-2 s-1"`, `--input_ref_units "kg m-2 s-1"`, `--output_units "mm day-1"`: Specify input and desired output units and the code will convert units if required.
- `--hist_time_bounds 1995-01-01 2014-12-31`: Time bounds for historical period.
- `--ref_time_bounds 1990-01-01 2019-12-31`: Time bounds for reference period.
- `--ssr`: Apply Singularity Stochasitc Removal (for precipitation data).
- `--verbose`: As the program runs it will print progess updates to the screen.

We would use the `--time_grouping monthly` for temperature data but no time grouping for precipitation
(see [method_qdm.md](method_qdm.md) for an explanation).

Putting these options together with the positional arguments (the historical variable, reference variable and output adjustment factor file name) looks as follows:

```
python train.py pr pr /g/data/wp00/data/QQ-CMIP6/ACCESS-ESM1-5/historical/r1i1p1f1/day/pr/v20191115/pr-qdm-multiplicative-monthly-q100-adjustment-factors_ACCESS-ESM1-5_ssp370_r1i1p1f1_gn_20560101-20851231_wrt_19950101-20141231.nc --hist_files /g/data/fs38/publications/CMIP6/CMIP/CSIRO/ACCESS-ESM1-5/historical/r1i1p1f1/day/pr/gn/v20191115/pr_day_ACCESS-ESM1-5_historical_r1i1p1f1_gn_19500101-19991231.nc /g/data/fs38/publications/CMIP6/CMIP/CSIRO/ACCESS-ESM1-5/historical/r1i1p1f1/day/pr/gn/v20191115/pr_day_ACCESS-ESM1-5_historical_r1i1p1f1_gn_20000101-20141231.nc --ref_files /g/data/fs38/publications/CMIP6/ScenarioMIP/CSIRO/ACCESS-ESM1-5/ssp370/r1i1p1f1/day/pr/gn/v20191115/pr_day_ACCESS-ESM1-5_ssp370_r1i1p1f1_gn_20150101-20641231.nc /g/data/fs38/publications/CMIP6/ScenarioMIP/CSIRO/ACCESS-ESM1-5/ssp370/r1i1p1f1/day/pr/gn/v20191115/pr_day_ACCESS-ESM1-5_ssp370_r1i1p1f1_gn_20650101-21001231.nc --hist_time_bounds 1995-01-01 2014-12-31 --ref_time_bounds 2056-01-01 2085-12-31 --scaling multiplicative --nquantiles 100 --input_hist_units "kg m-2 s-1" --input_ref_units "kg m-2 s-1" --output_units "mm day-1" --verbose --ssr
```

See the [software environment instructions](https://github.com/climate-innovation-hub/qqscale/tree/master#software-environment) for details on the python environment.

See the [performance notes](https://github.com/climate-innovation-hub/qqscale/tree/master#performance)
for details on the expected time and memory requirements for this training step.

## Step 2: Adjustment

The `adjust.py` command line program can be used to apply
the adjustment factors to observations.
You can run `python adjust.py -h` at the command line to view the positional arguments
and options/flags associated with the program.

The positional arguments for this program are the target model files
(i.e. the data that needs to be bias corrected):
```
/g/data/xv83/agcd-csiro/precip/daily/precip-total_AGCD-CSIRO_r005_19000101-20220405_daily_space-chunked.zarr
```
followed by the variable:
```
precip
```
adjustment factor file:
```
/g/data/wp00/data/QQ-CMIP6/ACCESS-ESM1-5/historical/r1i1p1f1/day/pr/v20191115/pr-qdm-multiplicative-monthly-q100-adjustment-factors_ACCESS-ESM1-5_ssp370_r1i1p1f1_gn_20560101-20851231_wrt_19950101-20141231.nc
```
and name of the output file
(in this case following the CIH
[file naming convenions](https://github.com/climate-innovation-hub/.github/blob/main/drs-qq-cmip6.md)):
```
/g/data/wp00/data/QQ-CMIP6/ACCESS-ESM1-5/ssp370/r1i1p1f1/day/pr/v20191115/pr_day_ACCESS-ESM1-5_ssp370_r1i1p1f1_AUS-r005_20560101-20851231_qdm-multiplicative-monthly-q100-nearest_AGCD-19900101-20191231_historical-19950101-20141231.nc
```

There are a number of options/flags that are also required to complete this task:
- `--spatial_grid input`: The flag specifies whether to output data on the adjustment factor (`af`) or input data (`input`) grid. We want data on the input AGCD grid.
- `--interp nearest`: The method for interpolating between adjustment factors (see [method_qdm.md](method_qdm.md) for an explanation of why we prefer nearest neighbour).
- `--input_units "mm day-1"`, `--output_units "mm day-1"`: Specify input and desired output units and the code will convert units if required.
- `--adjustment_tbounds 1990-01-01 2019-12-31`: Time bounds for the data to be adjusted.
- `--ssr`: Apply Singularity Stochasitc Removal (for precipitation data only; see [method_qdm.md](method_qdm.md) for details).
- `--ref_time`: Apply the time axis from the reference (future) data to the output data.
- `--verbose`: As the program runs it will print progess updates to the screen.

Putting all these positional and options/flags together:
```
python adjust.py /g/data/xv83/agcd-csiro/precip/daily/precip-total_AGCD-CSIRO_r005_19000101-20220405_daily_space-chunked.zarr precip /g/data/wp00/data/QQ-CMIP6/ACCESS-ESM1-5/historical/r1i1p1f1/day/pr/v20191115/pr-qdm-multiplicative-monthly-q100-adjustment-factors_ACCESS-ESM1-5_ssp370_r1i1p1f1_gn_20560101-20851231_wrt_19950101-20141231.nc /g/data/wp00/data/QQ-CMIP6/ACCESS-ESM1-5/ssp370/r1i1p1f1/day/pr/v20191115/pr_day_ACCESS-ESM1-5_ssp370_r1i1p1f1_AUS-r005_20560101-20851231_qdm-multiplicative-monthly-q100-nearest_AGCD-19900101-20191231_historical-19950101-20141231.nc --adjustment_tbounds 1990-01-01 2019-12-31 --input_units "mm day-1" --output_units "mm day-1" --spatial_grid input --interp nearest --verbose --ssr --ref_time
```
See the [software environment instructions](https://github.com/climate-innovation-hub/qqscale/tree/master#software-environment) for details on the python environment.

See the [performance notes](https://github.com/climate-innovation-hub/qqscale/tree/master#performance)
for details on the expected time and memory requirements for this adjustment step.

## Step 3: Visualise (Optional)

It can be useful to visualise the quantile delta mapping process to understand what
modifications have been made to the original data.
A template visualisation notebook is available at:  
https://github.com/climate-innovation-hub/qq-workflows/blob/main/validation.ipynb

The [papermill](https://papermill.readthedocs.io) tool can be used to insert
the various parameters used in the training and adjustment steps into the template notebook
and run it.
For instance,
the example workflow described about can be visualised by running the following at the
command line:

```
papermill -p adjustment_file /g/data/wp00/data/QQ-CMIP6/ACCESS-ESM1-5/historical/r1i1p1f1/day/pr/v20191115/pr-qdm-multiplicative-monthly-q100-adjustment-factors_ACCESS-ESM1-5_ssp370_r1i1p1f1_gn_20560101-20851231_wrt_19950101-20141231.nc -p qq_file /g/data/wp00/data/QQ-CMIP6/ACCESS-ESM1-5/ssp370/r1i1p1f1/day/pr/v20191115/pr_day_ACCESS-ESM1-5_ssp370_r1i1p1f1_AUS-r005_20560101-20851231_qdm-multiplicative-monthly-q100-nearest_AGCD-19900101-20191231_historical-19950101-20141231.nc -r hist_files "/g/data/fs38/publications/CMIP6/CMIP/CSIRO/ACCESS-ESM1-5/historical/r1i1p1f1/day/pr/gn/v20191115/pr_day_ACCESS-ESM1-5_historical_r1i1p1f1_gn_19500101-19991231.nc /g/data/fs38/publications/CMIP6/CMIP/CSIRO/ACCESS-ESM1-5/historical/r1i1p1f1/day/pr/gn/v20191115/pr_day_ACCESS-ESM1-5_historical_r1i1p1f1_gn_20000101-20141231.nc" -r ref_files "/g/data/fs38/publications/CMIP6/ScenarioMIP/CSIRO/ACCESS-ESM1-5/ssp370/r1i1p1f1/day/pr/gn/v20191115/pr_day_ACCESS-ESM1-5_ssp370_r1i1p1f1_gn_20150101-20641231.nc /g/data/fs38/publications/CMIP6/ScenarioMIP/CSIRO/ACCESS-ESM1-5/ssp370/r1i1p1f1/day/pr/gn/v20191115/pr_day_ACCESS-ESM1-5_ssp370_r1i1p1f1_gn_20650101-21001231.nc" -r target_files "/g/data/xv83/agcd-csiro/precip/daily/precip-total_AGCD-CSIRO_r005_19000101-20220405_daily_space-chunked.zarr" -r hist_time_bounds "1995-01-01 2014-12-31" -r ref_time_bounds "2056-01-01 2085-12-31" -r target_time_bounds "1990-01-01 2019-12-31" -p hist_units "kg m-2 s-1" -p ref_units "kg m-2 s-1" -p target_units "mm day-1" -p output_units "mm day-1" -p hist_var pr -p ref_var pr -p target_var precip -p scaling multiplicative validation.ipynb /g/data/wp00/data/QQ-CMIP6/ACCESS-ESM1-5/ssp370/r1i1p1f1/day/pr/v20191115/pr_day_ACCESS-ESM1-5_ssp370_r1i1p1f1_AUS-r005_20560101-20851231_qdm-multiplicative-monthly-q100-nearest_AGCD-19900101-20191231_historical-19950101-20141231.ipynb
```

The result is a new notebook called: 
```
/g/data/wp00/data/QQ-CMIP6/ACCESS-ESM1-5/ssp370/r1i1p1f1/day/pr/v20191115/pr_day_ACCESS-ESM1-5_ssp370_r1i1p1f1_AUS-r005_20560101-20851231_qdm-multiplicative-monthly-q100-nearest_AGCD-19900101-20191231_historical-19950101-20141231.ipynb
```

You can view an example of what such a notebook looks like
[here](https://github.com/climate-innovation-hub/qq-workflows/tree/main/cih).

Feel free to open an issue at the qq-workflows repository
if you'd like help creating a configuration file to use make for your workflow.
