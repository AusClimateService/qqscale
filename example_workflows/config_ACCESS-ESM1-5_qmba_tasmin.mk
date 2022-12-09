# Quantile mapping bias adjustmen (for projections): tasmin

HIST_VAR=tasmin
REF_VAR=tmin
TARGET_VAR=tasmin
HIST_UNITS=K
REF_UNITS=C
TARGET_UNITS=K
OUTPUT_UNITS=C
OUTPUT_GRID=adjustment

MAPPING=qm
SCALING=additive
GROUPING=monthly
MODEL=ACCESS-ESM1-5
OBS_DATASET=AGCD
EXPERIMENT=ssp370
RUN=r1i1p1f1
HIST_START=1995
HIST_END=2014
REF_START=1995
REF_END=2014
TARGET_START=2035
TARGET_END=2064
# (Hobart)
EXAMPLE_LAT = -42.9
EXAMPLE_LON = 147.3
EXAMPLE_MONTH = 5


HIST_FILES := /g/data/fs38/publications/CMIP6/CMIP/CSIRO/ACCESS-ESM1-5/historical/r1i1p1f1/day/tasmin/gn/latest/tasmin_day_ACCESS-ESM1-5_historical_r1i1p1f1_gn_19500101-19991231.nc /g/data/fs38/publications/CMIP6/CMIP/CSIRO/ACCESS-ESM1-5/historical/r1i1p1f1/day/tasmin/gn/latest/tasmin_day_ACCESS-ESM1-5_historical_r1i1p1f1_gn_20000101-20141231.nc

TARGET_FILES := /g/data/fs38/publications/CMIP6/ScenarioMIP/CSIRO/ACCESS-ESM1-5/ssp370/r1i1p1f1/day/tasmin/gn/latest/tasmin_day_ACCESS-ESM1-5_ssp370_r1i1p1f1_gn_20150101-20641231.nc

REF_FILES := /g/data/xv83/agcd-csiro/tmin/daily/tmin_AGCD-CSIRO_r005_19100101-20220405_daily_space-chunked.zarr

AF_FILE=${HIST_VAR}-qmba-adjustment-factors-${SCALING}-${GROUPING}_day_${OBS_DATASET}-${MODEL}_historical_${RUN}_${HIST_START}0101-${HIST_END}1231.nc
QQ_BASE=${HIST_VAR}-qmba-${SCALING}-${GROUPING}_day_${OBS_DATASET}-${MODEL}_${EXPERIMENT}_${RUN}_${TARGET_START}0101-${TARGET_END}1231


