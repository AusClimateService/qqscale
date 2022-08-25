.PHONY: help

include ${CONFIG}

PYTHON=/g/data/wp00/users/dbi599/miniconda3/envs/cih/bin/python
CODE_DIR=/g/data/wp00/shared_code/qqscale
QQ_DIR=/g/data/wp00/users/dbi599/test_space
AF_FILE=${QQ_DIR}/${MODEL_VAR}-qqscale-factors-${METHOD}_day_${MODEL}_${EXPERIMENT}_${RUN}_${MODEL_BASE_START}0101-${MODEL_BASE_END}1231_${FUTURE_START}0101-${FUTURE_END}1231.nc
QQ_FILE=${QQ_DIR}/${MODEL_VAR}-qqscaled-${METHOD}_day_${OBS_DATASET}-${MODEL}_${EXPERIMENT}_${RUN}_${FUTURE_START}0101-${FUTURE_END}1231.nc

## adjustment-factors: Calculate the QQ-scale adjustment factors
adjustment-factors : ${AF_FILE}
${AF_FILE} :
	${PYTHON} ${CODE_DIR}/calc_adjustment.py ${MODEL_VAR} $@ --hist_files ${HIST_FILES} --fut_files ${FUTURE_FILES} --hist_time_bounds ${MODEL_BASE_START}-01-01 ${MODEL_BASE_END}-12-31 --fut_time_bounds ${FUTURE_START}-01-01 ${FUTURE_END}-12-31 --method ${METHOD} --input_units ${MODEL_UNITS} --output_units ${OUTPUT_UNITS} --verbose

## qqscale-projections: Calculate QQ-scaled climate projection data
qqscale-projections : ${QQ_FILE}
${QQ_FILE} : ${AF_FILE}
	${PYTHON} ${CODE_DIR}/apply_adjustment.py ${OBS_FILES} ${OBS_VAR} $< $@ --time_bounds ${OBS_BASE_START}-01-01 ${OBS_BASE_END}-12-31 --obs_units ${OBS_UNITS} --adjustment_units ${OUTPUT_UNITS} --output_units ${OUTPUT_UNITS} --verbose

#bash apply_adjustment.sh tmax /g/data/wp00/dbi599/tasmax-qqscale-factors_day_ACCESS1-3_rcp45_r1i1p1_19860101-20051231_20210101-20401231.nc /g/data/wp00/dbi599/tasmax_day_AGCD-ACCESS1-3_rcp45_r1i1p1_20210101-20401231.nc 1986-01-01 2005-12-31 15 /g/data/zv2/agcd/v1/tmax/mean/r005/01day/agcd_v1_tmax_mean_r005_daily_198[6,7,8,9]*.nc /g/data/zv2/agcd/v1/tmax/mean/r005/01day/agcd_v1_tmax_mean_r005_daily_199*.nc /g/data/zv2/agcd/v1/tmax/mean/r005/01day/agcd_v1_tmax_mean_r005_daily_200[0,1,2,3,4,5]*.nc

## help : show this message
help :
	@echo 'make [target] [-Bnf] CONFIG=config_file.mk'
	@echo ''
	@echo 'valid targets:'
	@grep -h -E '^##' ${MAKEFILE_LIST} | sed -e 's/## //g' | column -t -s ':'

