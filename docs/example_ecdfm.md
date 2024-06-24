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

> **Shortcut**
>
> You'll see in steps 1-2 below that there are lots of
> positional arguments and program options/flags to remember,
> which means it can be easy to forget something or make an error.
>
> If you don't already have a process for managing complicated workflows like this,
> using a build tool like Make can be helpful.
> The Make-based workflow at https://github.com/AusClimateService/qq-workflows/tree/main/acs
> have been built to coordinate the bias correction workflow described above.
>

The following example describes how to process the 2050-2079 window using the
equidistant CDF matching (EDCDFm) bias correction method
(see [method_ecdfm.md](method_ecdfm.md) for details)
for a given variable (tasmin),
regional climate model (BOM-BARPA-R), and
parent global climate model (CMCC-CMCC-ESM2).


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
/g/data/py18/BARPA/output/CMIP6/DD/AUS-15/BOM/CMCC-ESM2/historical/r1i1p1f1/BARPA-R/v1-r1/day/tasmin/v20231001/tasmin_AUS-15_CMCC-ESM2_historical_r1i1p1f1_BOM_BARPA-R_v1-r1_day_198[5,6,7,8,9]*.nc
/g/data/py18/BARPA/output/CMIP6/DD/AUS-15/BOM/CMCC-ESM2/historical/r1i1p1f1/BARPA-R/v1-r1/day/tasmin/v20231001/tasmin_AUS-15_CMCC-ESM2_historical_r1i1p1f1_BOM_BARPA-R_v1-r1_day_199*.nc
/g/data/py18/BARPA/output/CMIP6/DD/AUS-15/BOM/CMCC-ESM2/historical/r1i1p1f1/BARPA-R/v1-r1/day/tasmin/v20231001/tasmin_AUS-15_CMCC-ESM2_historical_r1i1p1f1_BOM_BARPA-R_v1-r1_day_2*.nc
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
- `--ssr`: If we were processing precipitation data we would use this flag to apply Singularity Stochasitc Removal (see [method_ecdfm.md](method_ecdfm.md) for details).
- `--verbose`: As the program runs it will print progess updates to the screen.

Putting these options together with the positional arguments (the historical variable, reference variable and output adjustment factor file name) looks as follows:

```
python train.py tasmin tmin tasmin-ecdfm-additive-monthly-q100-adjustment-factors_AGCD_AUS-05i_CMCC-ESM2_historical_r1i1p1f1_BARPA-R_v1_day_19850101-20141231.nc --hist_files /g/data/py18/BARPA/output/CMIP6/DD/AUS-15/BOM/CMCC-ESM2/historical/r1i1p1f1/BARPA-R/v1-r1/day/tasmin/v20231001/tasmin_AUS-15_CMCC-ESM2_historical_r1i1p1f1_BOM_BARPA-R_v1-r1_day_198[5,6,7,8,9]*.nc /g/data/py18/BARPA/output/CMIP6/DD/AUS-15/BOM/CMCC-ESM2/historical/r1i1p1f1/BARPA-R/v1-r1/day/tasmin/v20231001/tasmin_AUS-15_CMCC-ESM2_historical_r1i1p1f1_BOM_BARPA-R_v1-r1_day_199*.nc /g/data/py18/BARPA/output/CMIP6/DD/AUS-15/BOM/CMCC-ESM2/historical/r1i1p1f1/BARPA-R/v1-r1/day/tasmin/v20231001/tasmin_AUS-15_CMCC-ESM2_historical_r1i1p1f1_BOM_BARPA-R_v1-r1_day_2*.nc --ref_files /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_198[5,6,7,8,9]*.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_199*.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_200*.nc /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_201[0,1,2,3,4]*.nc --hist_time_bounds 1985-01-01 2014-12-31 --ref_time_bounds 1985-01-01 2014-12-31 --scaling additive --nquantiles 100 --time_grouping monthly --input_hist_units K --input_ref_units C --output_units C --verbose 
```

See the [software environment instructions](https://github.com/AusClimateService/qqscale/tree/master#software-environment) for details on the python environment.


## Step 2: Adjustment

The `adjust.py` command line program can be used to bias correct model data using
the adjustment factors calculated in the previous step.
You can run `python adjust.py -h` at the command line to view the positional arguments
and options/flags associated with the program.

The positional arguments for this program are the target model files
(i.e. the data that needs to be bias corrected):
```
/g/data/py18/BARPA/output/CMIP6/DD/AUS-15/BOM/CMCC-ESM2/ssp370/r1i1p1f1/BARPA-R/v1-r1/day/tasmin/v20231001/tasmin_AUS-15_CMCC-ESM2_ssp370_r1i1p1f1_BOM_BARPA-R_v1-r1_day_20[5,6,7]*.nc
```
followed by the variable:
```
tasmin
```
adjustment factor file:
```
tasmin-ecdfm-additive-monthly-q100-adjustment-factors_AGCD_AUS-05i_CMCC-ESM2_historical_r1i1p1f1_BARPA-R_v1_day_19850101-20141231.nc
```
and name of the output bias corrected data file
(in this case following the ACS Data and Code Group
[file naming convenions](https://github.com/AusClimateService/data-code-group/blob/main/data_standards.md#cordex-cmip6)):
```
tasmin_AUS-05i_CMCC-ESM2_ssp370_r1i1p1f1_BARPA-R_v1_day_20600101-20691231-from-20500101-20791231_ecdfm-additive-monthly-q100-nearest-AGCD-19850101-20141231.nc
```

There are a number of options/flags that are also required to complete this task:
- `--spatial_grid af`: The flag specifies whether to output data on the adjustment factor (`af`) or input data (`input`) grid. We want data on the adjustment grid (AUS-05i) because that's the observational (as opposed to model) grid.
- `--interp nearest`: The method for interpolating between adjustment factors (see [method_ecdfm.md](method_ecdfm.md) for an explanation of why we prefer nearest neighbour).
- `--input_units K`, `--output_units C`: Specify input and desired output units and the code will convert units if required.
- `--adjustment_tbounds 2050-01-01 2079-12-31`: Time bounds to perform the bias correction over (i.e. for if your input files span a longer time period than required).
- `--output_tslice 2060-01-01 2069-12-31`: Time bounds of the bias corrected data segment to keep (for our 30-year sliding window analysis we're just keeping the central 10 years)
- `--verbose`: As the program runs it will print progess updates to the screen.

As for the training step, if we were processing precipitation data we would also use the `--ssr` flag to apply Singularity Stochasitc Removal (see [method_ecdfm.md](method_ecdfm.md) for details).

Putting all these positional and options/flags together:
```
python adjust.py /g/data/py18/BARPA/output/CMIP6/DD/AUS-15/BOM/CMCC-ESM2/ssp370/r1i1p1f1/BARPA-R/v1-r1/day/tasmin/v20231001/tasmin_AUS-15_CMCC-ESM2_ssp370_r1i1p1f1_BOM_BARPA-R_v1-r1_day_20[5,6,7]*.nc tasmin tasmin-ecdfm-additive-monthly-q100-adjustment-factors_AGCD_AUS-05i_CMCC-CMCC-ESM2_historical_r1i1p1f1_BOM-BARPA-R_v1_day_19850101-20141231.nc tasmin_AUS-05i_CMCC-ESM2_ssp370_r1i1p1f1_BARPA-R_v1_day_20500101-20791231-from-20500101-20791231_ecdfm-additive-monthly-q100-nearest-AGCD-19850101-20141231.nc --adjustment_tbounds 2050-01-01 2079-12-31 --output_tslice 2060-01-01 2069-12-31 --input_units K --output_units C --spatial_grid af --interp nearest --verbose
```
See the [software environment instructions](https://github.com/AusClimateService/qqscale/tree/master#software-environment) for details on the python environment.

Feel free to open an issue at the [qq-workflows repository](https://github.com/AusClimateService/qq-workflows)
if you'd like help creating a configuration file to use make for your workflow.
