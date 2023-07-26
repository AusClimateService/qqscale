# Worked example: ACS

The Australian Climate Service (ACS) intends to bias correct daily CORDEX data
(i.e. dynamically downscaled CMIP6 global climate model data)
from the historical and ssp370 experiments
in 30-year windows using 1985-2014 as a reference period.

Combining the historical and ssp370 experiments,
the daily CORDEX data spans the period 1960-2100.
To avoid abrupt changes in the bias corrected data from one 30-year analysis window to the next,
we keep/archive only the central decade from each window and increment the window 10 years at a time.
For instance,
when we process the 2050-2079 window we only keep
the central decacde (2060-2069)
and then move on and process the 2060-2089 window
(keeping 2070-2079).

The following example describes how to process the 2050-2079 window using the
equidistant CDF matching (EDCDFm) bias correction method for a given
variable (tasmin),
regional climate model (BOM-BARPA-R), and
parent global climate model (CMCC-CMCC-ESM2).

> **Shortcut**
>
> You'll see in steps 1-2 below that there are lots of
> positional arguments and program options/flags to remember,
> which means it can be easy to forget something or make an error.
>
> If you don't already have a process for managing complicated workflows like this,
> using a build tool like Make can be helpful.
> The Makefile and ACS configuation file at https://github.com/climate-innovation-hub/qq-workflows
> have been built to coordinate the bias correction workflow described below.
>
> To run steps 1-2 below,
> you could simply clone the qq-workflows repo and run the following at the command line:
> ```
> git clone git@github.com:climate-innovation-hub/qq-workflows.git
> cd qq-workflows
> make adjust CONFIG=acs/config_acs.mk VAR=tasmin RCM_NAME=BOM-BARPA-R GCM_NAME=CMCC-CMCC-ESM2 TARGET_START=2050 TARGET_END=2079 OUTPUT_START=2060 OUTPUT_END=2069
> ```

> **Full timeseries** 
> 
> The `bias_correct_timeseries.sh` shell script in the qq-workflows repo
> runs the `make` command for sequential 30-year windows in 10-year increments
> from 1960 to 2100.
> 
> For example, in this case we would run the following to process
> the entire 1960-2100 timeseries:
> ```
> bash bias_correct_timeseries.sh tasmin BOM-BARPA-R CMCC-CMCC-ESM2
> ```


## Step 1: Training

The `train.py` command line program can be used to compare historical model data with reference observational data
in order to produce the bias correction "adjustment factors" needed for the adjustment step.
You can run `python train.py -h` at the command line to view the positional arguments
and options/flags associated with the program.
To give an example,
the options/flags for the ACS bias correction task described above would be as follows...

The `--hist_files` flag is used to specify the historical model data files
(in this case for the 1985-2014 reference period):
```
--hist_files
/g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_198[5,6,7,8,9]*.nc
/g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_199*.nc
/g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_2*.nc
```

The `--ref_files` flag is used to specify the reference observational data files:

```
--ref_files
/g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_198[5,6,7,8,9]*.nc
/g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_199*.nc
/g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_200*.nc
/g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_201[0,1,2,3,4]*.nc
```

There are a number of other flags that are also required to complete this task:
- `--scaling additive`: Additive scaling is typically used for temperature (and `multiplicative` for rainfall).
- `--time_grouping monthly`: We like to use monthly time grouping (see [method_ecdfm.md](method_ecdfm.md) for an explanation).
- `--nquantiles 100`: We like to use 100 quantiles.
- `--input_hist_units K`, `--input_ref_units C`, `--output_units C`: Specify input and desired output units and the code will convert units if required.

There are also some flags that aren't necessarily needed in this case but can be useful:
- `--hist_time_bounds 1985-01-01 2014-12-31`: Time bounds for historical period (i.e. for if your input files span a longer time period than required).
- `--ref_time_bounds 1985-01-01 2014-12-31`: Time bounds for reference period (i.e. for if your input files span a longer time period than required).
- `--verbose`: As the program runs it will print progess updates to the screen.

Putting these options together with the positional arguments (the historical variable, reference variable and output adjustment factor file name) looks as follows:

```
python train.py tasmin tmin /g/data/ia39/australian-climate-service/test-data/CORDEX-CMIP6-ECDFm/output/AUS-05i/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin-ecdfm-additive-monthly-q100-adjustment-factors_AGCD_AUS-05i_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_19850101-20141231.nc --hist_files /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_198[5,6,7,8,9]*.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_199*.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_2*.nc --ref_files /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_198[5,6,7,8,9]*.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_199*.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_200*.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_201[0,1,2,3,4]*.nc --hist_time_bounds 1985-01-01 2014-12-31 --ref_time_bounds 1985-01-01 2014-12-31 --scaling additive --nquantiles 100 --time_grouping monthly --input_hist_units K --input_ref_units C --output_units C --verbose 
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
/g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_20[5,6,7]*.nc
```
followed by the variable:
```
tasmin
```
adjustment factor file:
```
/g/data/ia39/australian-climate-service/test-data/CORDEX-CMIP6-ECDFm/output/AUS-05i/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin-ecdfm-additive-monthly-q100-adjustment-factors_AGCD_AUS-05i_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_19850101-20141231.nc
```
and name of the output bias corrected data file
(in this case following the ACS Data and Code Group
[file naming convenions](https://github.com/AusClimateService/data-code-group/blob/main/data_standards.md#cordex-cmip6)):
```
/g/data/ia39/australian-climate-service/test-data/CORDEX-CMIP6-ECDFm/output/AUS-05i/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-05i_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_20600101-20691231-from-20500101-20791231_ecdfm-additive-monthly-q100-nearest-AGCD-19850101-20141231.nc
```

There are a number of options/flags that are also required to complete this task:
- `--spatial_grid af`: The flag specifies whether to output data on the adjustment factor (`af`) or input data (`input`) grid. We want data on the adjustment grid (AUS-05i) because that's the observational (as opposed to model) grid.
- `--interp nearest`: The method for interpolating between adjustment factors (see [method_ecdfm.md](method_ecdfm.md) for an explanation of why we prefer nearest neighbour).
- `--input_units K`, `--output_units C`: Specify input and desired output units and the code will convert units if required.
- `--adjustment_tbounds 2050-01-01 2079-12-31`: Time bounds to perform the bias correction over (i.e. for if your input files span a longer time period than required).
- `--output_tslice 2060-01-01 2069-12-31`: Time bounds of the bias corrected data segment to keep (for our 30-year sliding window analysis we're just keeping the central 10 years)
- `--verbose`: As the program runs it will print progess updates to the screen.

Putting all these positional and options/flags together:
```
python adjust.py /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_20[5,6,7]*.nc tasmin /g/data/ia39/australian-climate-service/test-data/CORDEX-CMIP6-ECDFm/output/AUS-05i/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin-ecdfm-additive-monthly-q100-adjustment-factors_AGCD_AUS-05i_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_19850101-20141231.nc /g/data/ia39/australian-climate-service/test-data/CORDEX-CMIP6-ECDFm/output/AUS-05i/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-05i_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_20500101-20791231-from-20500101-20791231_ecdfm-additive-monthly-q100-nearest-AGCD-19850101-20141231.nc --adjustment_tbounds 2050-01-01 2079-12-31 --output_tslice 2060-01-01 2069-12-310. --input_units K --output_units C --spatial_grid af --interp nearest --verbose
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
papermill -p adjustment_file /g/data/ia39/australian-climate-service/test-data/CORDEX-CMIP6-ECDFm/output/AUS-05i/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin-ecdfm-additive-monthly-q100-adjustment-factors_AGCD_AUS-05i_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_19850101-20141231.nc -p qq_file /g/data/ia39/australian-climate-service/test-data/CORDEX-CMIP6-ECDFm/output/AUS-05i/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-05i_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_20500101-20791231-from-20500101-20791231_ecdfm-additive-monthly-q100-nearest-AGCD-19850101-20141231.nc -r hist_files "/g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_198501-198512.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_198601-198612.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_198701-198712.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_198801-198812.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_198901-198912.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_199001-199012.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_199101-199112.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_199201-199212.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_199301-199312.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_199401-199412.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_199501-199512.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_199601-199612.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_199701-199712.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_199801-199812.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_199901-199912.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_200001-200012.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_200101-200112.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_200201-200212.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_200301-200312.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_200401-200412.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_200501-200512.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_200601-200612.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_200701-200712.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_200801-200812.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_200901-200912.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_201001-201012.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_201101-201112.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_201201-201212.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_201301-201312.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/historical/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_201401-201412.nc" -r ref_files "/g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_19850101-19851231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_19860101-19861231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_19870101-19871231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_19880101-19881231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_19890101-19891231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_19900101-19901231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_19910101-19911231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_19920101-19921231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_19930101-19931231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_19940101-19941231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_19950101-19951231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_19960101-19961231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_19970101-19971231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_19980101-19981231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_19990101-19991231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_20000101-20001231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_20010101-20011231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_20020101-20021231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_20030101-20031231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_20040101-20041231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_20050101-20051231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_20060101-20061231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_20070101-20071231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_20080101-20081231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_20090101-20091231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_20100101-20101231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_20110101-20111231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_20120101-20121231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_20130101-20131231_daily.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_20140101-20141231_daily.nc" -r target_files "/g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_205001-205012.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_205101-205112.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_205201-205212.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_205301-205312.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_205401-205412.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_205501-205512.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_205601-205612.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_205701-205712.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_205801-205812.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_205901-205912.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_206001-206012.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_206101-206112.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_206201-206212.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_206301-206312.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_206401-206412.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_206501-206512.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_206601-206612.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_206701-206712.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_206801-206812.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_206901-206912.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_207001-207012.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_207101-207112.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_207201-207212.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_207301-207312.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_207401-207412.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_207501-207512.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_207601-207612.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_207701-207712.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_207801-207812.nc /g/data/ia39/australian-climate-service/release/CORDEX-CMIP6/output/AUS-15/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-15_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_207901-207912.nc " -r hist_time_bounds "1985-01-01 2014-12-31" -r ref_time_bounds "1985-01-01 2014-12-31" -r target_time_bounds "2050-01-01 2079-12-31" -p hist_units K -p ref_units C -p target_units K -p output_units C -p hist_var tasmin -p ref_var tmin -p target_var tasmin -p scaling additive validation.ipynb /g/data/ia39/australian-climate-service/test-data/CORDEX-CMIP6-ECDFm/output/AUS-05i/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-05i_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_20600101-20691231-from-20500101-20791231_ecdfm-additive-monthly-q100-nearest-AGCD-19850101-20141231.ipynb
```

The result is a new notebook called: 
```
/g/data/ia39/australian-climate-service/test-data/CORDEX-CMIP6-ECDFm/output/AUS-05i/BOM/CMCC-CMCC-ESM2/ssp370/r1i1p1f1/BOM-BARPA-R/v1/day/tasmin/tasmin_AUS-05i_CMCC-CMCC-ESM2_ssp370_r1i1p1f1_BOM-BARPA-R_v1_day_20600101-20691231-from-20500101-20791231_ecdfm-additive-monthly-q100-nearest-AGCD-19850101-20141231.ipynb
```

You can view an example of what such a notebook looks like
[here](https://github.com/climate-innovation-hub/qq-workflows/tree/main/acs).

Feel free to open an issue at the qq-workflows repository
if you'd like help creating a configuration file to use make for your workflow.
