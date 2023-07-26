# Worked example: NPCP

The [NPCP bias correction intercomparison](https://github.com/AusClimateService/npcp)
includes a cross validation task that involves producing bias corrected data
for even years from 1980-2019 (i.e. every second year),
using odd years from 1980-2019 as training data.

The following example describes how to complete this task using the
equidistant CDF matching (EDCDFm) bias correction method for a given
variable (tasmin),
regional climate model (UQ-DES-CCAM-2105), and
parent global climate model (CSIRO-ACCESS-ESM1-5).

> **Shortcut**
>
> You'll see in steps 1-3 below that there are lots of
> positional arguments and program options/flags to remember,
> which means it can be easy to forget something or make an error.
>
> If you don't already have a process for managing complicated workflows like this,
> using a build tool like Make can be helpful.
> The Makefile and NPCP configuation file at https://github.com/climate-innovation-hub/qq-workflows
> have been built to coordinate the bias correction workflow described below.
>
> To run steps 1-3 below,
> you could simply clone the qq-workflows repo and run the following at the command line:
> ```
> git clone git@github.com:climate-innovation-hub/qq-workflows.git
> cd qq-workflows
> make validation CONFIG=npcp/config_npcp.mk VAR=tasmin TASK=xvalidation RCM_NAME=UQ-DES-CCAM-2105 GCM_NAME=CSIRO-ACCESS-ESM1-5
> ```

## Step 1: Training

The `train.py` command line program can be used to compare historical model data with reference observational data
in order to produce the bias correction "adjustment factors" needed for the adjustment step.
You can run `python train.py -h` at the command line to view the positional arguments
and options/flags associated with the program.
To give an example,
the options/flags for the NPCP cross validation task would be as follows...

The `--hist_files` flag is used to specify the historical model data files
(in this case for odd years from 1980-2019):
```
--hist_files
/g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19?[1,3,5,7,9]*.nc
/g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_200[1,3,5,7,9]*.nc
/g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_*_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_201[1,3,5,7,9]*.nc
```

The `--ref_files` flag is used to specify the reference observational data files
(also odd years from 1980-2019):

```
--ref_files
/g/data/ia39/npcp/data/tasmin/observations/AGCD/raw/task-reference/tasmin_NPCP-20i_AGCD_v1-0-1_day_19?[1,3,5,7,9]*.nc 
/g/data/ia39/npcp/data/tasmin/observations/AGCD/raw/task-reference/tasmin_NPCP-20i_AGCD_v1-0-1_day_200[1,3,5,7,9]*.nc
/g/data/ia39/npcp/data/tasmin/observations/AGCD/raw/task-reference/tasmin_NPCP-20i_AGCD_v1-0-1_day_201[1,3,5,7,9]*.nc
```

There are a number of other flags that are also required to complete this task:
- `--scaling additive`: Additive scaling is typically used for temperature (and `multiplicative` for rainfall).
- `--time_grouping monthly`: We like to use monthly time grouping (see [method_ecdfm.md](method_ecdfm.md) for an explanation).
- `--nquantiles 100`: We like to use 100 quantiles.

There are also some flags that aren't necessarily needed in this case but can be useful:
- `--hist_time_bounds 1980-01-01 2019-12-31`: Time bounds for historical period (i.e. for if your input files span a longer time period than required).
- `--ref_time_bounds 1980-01-01 2019-12-31`: Time bounds for reference period (i.e. for if your input files span a longer time period than required).
- `--input_hist_units C`, `--input_ref_units C`, `--output_units C`: Specify input and desired output units and the code will convert units if required.
- `--verbose`: As the program runs it will print progess updates to the screen.

Putting these options together with the positional arguments (the historical variable, reference variable and output adjustment factor file name) looks as follows:

```
python train.py tasmin tasmin /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/ecdfm/task-xvalidation/tasmin-ecdfm-additive-monthly-q100-adjustment-factors_AGCD_NPCP-20i_CSIRO-ACCESS-ESM1-5_ssp370_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19810101-20191231-odd-years.nc --hist_files /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19?[1,3,5,7,9]*.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_200[1,3,5,7,9]*.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_*_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_201[1,3,5,7,9]*.nc --ref_files /g/data/ia39/npcp/data/tasmin/observations/AGCD/raw/task-reference/tasmin_NPCP-20i_AGCD_v1-0-1_day_19?[1,3,5,7,9]*.nc  /g/data/ia39/npcp/data/tasmin/observations/AGCD/raw/task-reference/tasmin_NPCP-20i_AGCD_v1-0-1_day_200[1,3,5,7,9]*.nc /g/data/ia39/npcp/data/tasmin/observations/AGCD/raw/task-reference/tasmin_NPCP-20i_AGCD_v1-0-1_day_201[1,3,5,7,9]*.nc --hist_time_bounds 1980-01-01 2019-12-31 --ref_time_bounds 1980-01-01 2019-12-31 --scaling additive --nquantiles 100 --time_grouping monthly --input_hist_units C --input_ref_units C --output_units C --verbose
```
See the [software environment instructions](https://github.com/climate-innovation-hub/qqscale/tree/master#software-environment) for details on the python environment.

See the [performance notes](https://github.com/climate-innovation-hub/qqscale/tree/master#performance)
for details on the expected time and memory requirements for this training step.

## Step 2: Adjustment

The `adjust.py` command line program can be used to bias correct model data using
the adjustment factors calculated in the previous step.
You can run `python adjust.py -h` at the command line to view the positional arguments
and options/flags associated with the program.

The positional arguments for this program are the target model files
(i.e. the data that needs to be bias corrected):
```
/g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19?[0,2,4,6,8]*.nc
/g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_200[0,2,4,6,8]*.nc
/g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_201[0,2,4,6,8]*.nc
```
followed by the variable:
```
tasmin
```
adjustment factor file:
```
/g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/ecdfm/task-xvalidation/tasmin-ecdfm-additive-monthly-q100-adjustment-factors_AGCD_NPCP-20i_CSIRO-ACCESS-ESM1-5_ssp370_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19810101-20191231-odd-years.nc
```
and name of the output bias corrected data file
(in this case following the file naming convenions of the NPCP project):
```
/g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/ecdfm/task-xvalidation/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_ssp370_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19800101-20181231-even-years_ecdfm-additive-monthly-q100-nearest-AGCD-19810101-20191231-odd-years.nc
```

There are a number of options/flags that are also required to complete this task:
- `--spatial_grid af`: The flag specifies whether to output data on the adjustment factor (`af`) or input data (`input`) grid. In this case both grids are the same, but in general we want data on the adjustment grid because that's the observational (as opposed to model) grid.
- `--interp nearest`: The method for interpolating between adjustment factors (see [method_ecdfm.md](method_ecdfm.md) for an explanation of why we prefer nearest neighbour).

There are also some flags that aren't necessarily needed in this case but can be useful:
- `--adjustment_tbounds 1980-01-01 2019-12-31`: Time bounds to perform the bias correction over (i.e. for if your input files span a longer time period than required).
- `--input_units C`, `--output_units C`: Specify input and desired output units and the code will convert units if required.
- `--verbose`: As the program runs it will print progess updates to the screen.

Putting all these positional and options/flags together:
```
python adjust.py /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19?[0,2,4,6,8]*.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_200[0,2,4,6,8]*.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_201[0,2,4,6,8]*.nc tasmin /g/data/xv83/dbi599/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/ecdfm/task-xvalidation/tasmin-ecdfm-additive-monthly-q100-adjustment-factors_AGCD_NPCP-20i_CSIRO-ACCESS-ESM1-5_ssp370_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19810101-20191231-odd-years.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/ecdfm/task-xvalidation/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_ssp370_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19800101-20181231-even-years_ecdfm-additive-monthly-q100-nearest-AGCD-19810101-20191231-odd-years.nc --adjustment_tbounds 1980-01-01 2018-12-31 --input_units C --output_units C --spatial_grid af  --interp nearest --verbose
```
See the [software environment instructions](https://github.com/climate-innovation-hub/qqscale/tree/master#software-environment) for details on the python environment.

See the [performance notes](https://github.com/climate-innovation-hub/qqscale/tree/master#performance)
for details on the expected time and memory requirements for this adjustment step.

## Step 3: Visualise (Optional)

It can be useful to visualise the bias correction process to understand what
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
papermill -p adjustment_file /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/ecdfm/task-xvalidation/tasmin-ecdfm-additive-monthly-q100-adjustment-factors_AGCD_NPCP-20i_CSIRO-ACCESS-ESM1-5_ssp370_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19810101-20191231-odd-years.nc -p qq_file /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/ecdfm/task-xvalidation/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_ssp370_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19800101-20181231-even-years_ecdfm-additive-monthly-q100-nearest-AGCD-19810101-20191231-odd-years.nc -r hist_files "/g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19810101-19811231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19830101-19831231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19850101-19851231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19870101-19871231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19890101-19891231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19910101-19911231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19930101-19931231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19950101-19951231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19970101-19971231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19990101-19991231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_20010101-20011231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_20030101-20031231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_20050101-20051231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_20070101-20071231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_20090101-20091231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_20110101-20111231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_20130101-20131231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_ssp370_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_20150101-20151231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_ssp370_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_20170101-20171231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_ssp370_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_20190101-20191231.nc" -r ref_files "/g/data/ia39/npcp/data/tasmin/observations/AGCD/raw/task-reference/tasmin_NPCP-20i_AGCD_v1-0-1_day_19810101-19811231.nc /g/data/ia39/npcp/data/tasmin/observations/AGCD/raw/task-reference/tasmin_NPCP-20i_AGCD_v1-0-1_day_19830101-19831231.nc /g/data/ia39/npcp/data/tasmin/observations/AGCD/raw/task-reference/tasmin_NPCP-20i_AGCD_v1-0-1_day_19850101-19851231.nc /g/data/ia39/npcp/data/tasmin/observations/AGCD/raw/task-reference/tasmin_NPCP-20i_AGCD_v1-0-1_day_19870101-19871231.nc /g/data/ia39/npcp/data/tasmin/observations/AGCD/raw/task-reference/tasmin_NPCP-20i_AGCD_v1-0-1_day_19890101-19891231.nc /g/data/ia39/npcp/data/tasmin/observations/AGCD/raw/task-reference/tasmin_NPCP-20i_AGCD_v1-0-1_day_19910101-19911231.nc /g/data/ia39/npcp/data/tasmin/observations/AGCD/raw/task-reference/tasmin_NPCP-20i_AGCD_v1-0-1_day_19930101-19931231.nc /g/data/ia39/npcp/data/tasmin/observations/AGCD/raw/task-reference/tasmin_NPCP-20i_AGCD_v1-0-1_day_19950101-19951231.nc /g/data/ia39/npcp/data/tasmin/observations/AGCD/raw/task-reference/tasmin_NPCP-20i_AGCD_v1-0-1_day_19970101-19971231.nc /g/data/ia39/npcp/data/tasmin/observations/AGCD/raw/task-reference/tasmin_NPCP-20i_AGCD_v1-0-1_day_19990101-19991231.nc /g/data/ia39/npcp/data/tasmin/observations/AGCD/raw/task-reference/tasmin_NPCP-20i_AGCD_v1-0-1_day_20010101-20011231.nc /g/data/ia39/npcp/data/tasmin/observations/AGCD/raw/task-reference/tasmin_NPCP-20i_AGCD_v1-0-1_day_20030101-20031231.nc /g/data/ia39/npcp/data/tasmin/observations/AGCD/raw/task-reference/tasmin_NPCP-20i_AGCD_v1-0-1_day_20050101-20051231.nc /g/data/ia39/npcp/data/tasmin/observations/AGCD/raw/task-reference/tasmin_NPCP-20i_AGCD_v1-0-1_day_20070101-20071231.nc /g/data/ia39/npcp/data/tasmin/observations/AGCD/raw/task-reference/tasmin_NPCP-20i_AGCD_v1-0-1_day_20090101-20091231.nc /g/data/ia39/npcp/data/tasmin/observations/AGCD/raw/task-reference/tasmin_NPCP-20i_AGCD_v1-0-1_day_20110101-20111231.nc /g/data/ia39/npcp/data/tasmin/observations/AGCD/raw/task-reference/tasmin_NPCP-20i_AGCD_v1-0-1_day_20130101-20131231.nc /g/data/ia39/npcp/data/tasmin/observations/AGCD/raw/task-reference/tasmin_NPCP-20i_AGCD_v1-0-1_day_20150101-20151231.nc /g/data/ia39/npcp/data/tasmin/observations/AGCD/raw/task-reference/tasmin_NPCP-20i_AGCD_v1-0-1_day_20170101-20171231.nc /g/data/ia39/npcp/data/tasmin/observations/AGCD/raw/task-reference/tasmin_NPCP-20i_AGCD_v1-0-1_day_20190101-20191231.nc" -r target_files "/g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19800101-19801231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19820101-19821231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19840101-19841231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19860101-19861231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19880101-19881231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19900101-19901231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19920101-19921231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19940101-19941231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19960101-19961231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19980101-19981231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_20000101-20001231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_20020101-20021231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_20040101-20041231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_20060101-20061231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_20080101-20081231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_20100101-20101231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_20120101-20121231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_historical_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_20140101-20141231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_ssp370_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_20160101-20161231.nc /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/raw/task-reference/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_ssp370_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_20180101-20181231.nc" -r hist_time_bounds "1981-01-01 2019-12-31" -r ref_time_bounds "1981-01-01 2019-12-31" -r target_time_bounds "1980-01-01 2018-12-31" -p hist_units C -p ref_units C -p target_units C -p output_units C -p hist_var tasmin -p ref_var tasmin -p target_var tasmin -p scaling additive -p method ecdfm validation.ipynb /g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/ecdfm/task-xvalidation/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_ssp370_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19800101-20181231-even-years_ecdfm-additive-monthly-q100-nearest-AGCD-19810101-20191231-odd-years.ipynb
```

The result is a new notebook called: 
```
/g/data/ia39/npcp/data/tasmin/CSIRO-ACCESS-ESM1-5/UQ-DES-CCAM-2105/ecdfm/task-xvalidation/tasmin_NPCP-20i_CSIRO-ACCESS-ESM1-5_ssp370_r6i1p1f1_UQ-DES-CCAM-2105_v1_day_19800101-20181231-even-years_ecdfm-additive-monthly-q100-nearest-AGCD-19810101-20191231-odd-years.ipynb`
```

You can view an example of what such a notebook looks like
[here](https://github.com/climate-innovation-hub/qq-workflows/tree/main/npcp).

Feel free to open an issue at the qq-workflows repository
if you'd like help creating a configuration file to use make for your workflow.
