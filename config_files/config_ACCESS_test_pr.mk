HIST_VAR=pr
REF_VAR=pr
TARGET_VAR=precip
HIST_UNITS="kg m-2 s-1"
REF_UNITS="kg m-2 s-1"
TARGET_UNITS="mm d-1"
OUTPUT_UNITS="mm d-1"

ADAPT_THRESHOLD=0.5mm
ADAPT_OPT=--adapt_freq "0.5 mm d-1"

METHOD=multiplicative
MODEL=ACCESS-ESM1-5
OBS_DATASET=AGCD
EXPERIMENT=ssp370
RUN=r1i1p1f1
HIST_START=1995
HIST_END=2014
REF_START=2035
REF_END=2064
TARGET_START=1990
TARGET_END=2019

HIST_FILES := /g/data/fs38/publications/CMIP6/CMIP/CSIRO/ACCESS-ESM1-5/historical/r1i1p1f1/day/pr/gn/latest/pr_day_ACCESS-ESM1-5_historical_r1i1p1f1_gn_19500101-19991231.nc /g/data/fs38/publications/CMIP6/CMIP/CSIRO/ACCESS-ESM1-5/historical/r1i1p1f1/day/pr/gn/latest/pr_day_ACCESS-ESM1-5_historical_r1i1p1f1_gn_20000101-20141231.nc

REF_FILES := /g/data/fs38/publications/CMIP6/ScenarioMIP/CSIRO/ACCESS-ESM1-5/ssp370/r1i1p1f1/day/pr/gn/latest/pr_day_ACCESS-ESM1-5_ssp370_r1i1p1f1_gn_20150101-20641231.nc /g/data/fs38/publications/CMIP6/ScenarioMIP/CSIRO/ACCESS-ESM1-5/ssp370/r1i1p1f1/day/pr/gn/latest/pr_day_ACCESS-ESM1-5_ssp370_r1i1p1f1_gn_20650101-21001231.nc

TARGET_FILES := /g/data/xv83/agcd-csiro/precip/daily/precip-total_AGCD-CSIRO_r005_19000101-20220405_daily_space-chunked.zarr

AF_FILE=${HIST_VAR}-qqscale-factors-${METHOD}_day_${MODEL}_historical-${EXPERIMENT}_${RUN}_${HIST_START}0101-${HIST_END}1231_${REF_START}0101-${REF_END}1231_freq-adapt-${ADAPT_THRESHOLD}.nc
QQ_BASE=${HIST_VAR}-qqscaled-${METHOD}_day_${OBS_DATASET}-${MODEL}_${EXPERIMENT}_${RUN}_${REF_START}0101-${REF_END}1231_freq-adapt


