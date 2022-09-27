.PHONY: help

include ${CONFIG}

EXAMPLE_LAT = -42.9
EXAMPLE_LON = 147.3
# (Hobart)
EXAMPLE_MONTH = 6

PYTHON=/g/data/wp00/users/dbi599/miniconda3/envs/cih/bin/python
CODE_DIR=/g/data/wp00/shared_code/qqscale
QQ_DIR=/g/data/wp00/users/dbi599/test_space
AF_FILE=${QQ_DIR}/${MODEL_VAR}-qqscale-factors-${METHOD}_day_${MODEL}_${EXPERIMENT}_${RUN}_${MODEL_BASE_START}0101-${MODEL_BASE_END}1231_${FUTURE_START}0101-${FUTURE_END}1231.nc
QQ_BASE=${QQ_DIR}/${MODEL_VAR}-qqscaled-${METHOD}_day_${OBS_DATASET}-${MODEL}_${EXPERIMENT}_${RUN}_${FUTURE_START}0101-${FUTURE_END}1231
QQ_FILE=${QQ_BASE}.nc
TEMPLATE_NOTEBOOK=${CODE_DIR}/validation.ipynb
VALIDATION_NOTEBOOK=${QQ_BASE}.ipynb


## adjustment-factors: Calculate the QQ-scale adjustment factors
adjustment-factors : ${AF_FILE}
${AF_FILE} :
	${PYTHON} ${CODE_DIR}/calc_adjustment.py ${MODEL_VAR} $@ --hist_files ${HIST_FILES} --fut_files ${FUTURE_FILES} --hist_time_bounds ${MODEL_BASE_START}-01-01 ${MODEL_BASE_END}-12-31 --fut_time_bounds ${FUTURE_START}-01-01 ${FUTURE_END}-12-31 --method ${METHOD} --input_units ${MODEL_UNITS} --output_units ${OUTPUT_UNITS} --verbose

## qqscale-projections: Calculate QQ-scaled climate projection data
qqscale-projections : ${QQ_FILE}
${QQ_FILE} : ${AF_FILE}
	${PYTHON} ${CODE_DIR}/apply_adjustment.py ${OBS_FILES} ${OBS_VAR} $< $@ --time_bounds ${OBS_BASE_START}-01-01 ${OBS_BASE_END}-12-31 --obs_units ${OBS_UNITS} --adjustment_units ${OUTPUT_UNITS} --output_units ${OUTPUT_UNITS} --verbose

## validation : Create validation plots for QQ-scaled climate projection data
validation : ${VALIDATION_NOTEBOOK}
${VALIDATION_NOTEBOOK} : ${TEMPLATE_NOTEBOOK} ${AF_FILE} ${QQ_FILE}
	papermill -p adjustment_file $(word 2,$^) -p qq_file $(word 3,$^) -r hist_files "${HIST_FILES}" -r fut_files "${FUTURE_FILES}" -r obs_files "${OBS_FILES}" -r hist_time_bounds "${MODEL_BASE_START}-01-01 ${MODEL_BASE_END}-12-31" -r fut_time_bounds "${FUTURE_START}-01-01 ${FUTURE_END}-12-31" -r obs_time_bounds "${OBS_BASE_START}-01-01 ${OBS_BASE_END}-12-31" -p example_lat ${EXAMPLE_LAT} -p example_lon ${EXAMPLE_LON} -p example_month ${EXAMPLE_MONTH} -p cmip_units ${MODEL_UNITS} -p obs_units ${OBS_UNITS} -p qq_units ${OUTPUT_UNITS} -p cmip_var ${MODEL_VAR} -p obs_var ${OBS_VAR} $< $@

## help : show this message
help :
	@echo 'make [target] [-Bnf] CONFIG=config_file.mk'
	@echo ''
	@echo 'valid targets:'
	@grep -h -E '^##' ${MAKEFILE_LIST} | sed -e 's/## //g' | column -t -s ':'

