.PHONY: help

include ${CONFIG}

## (Hobart)
#EXAMPLE_LAT = -42.9
#EXAMPLE_LON = 147.3

# (Alice Springs)
EXAMPLE_LAT = -23.7
EXAMPLE_LON = 133.88

EXAMPLE_MONTH = 6

#PYTHON=/g/data/wp00/users/dbi599/miniconda3/envs/cih/bin/python
PYTHON=/g/data/xv83/dbi599/miniconda3/envs/qqscale/bin/python
CODE_DIR=/g/data/wp00/shared_code/qqscale
QQ_DIR=/g/data/wp00/users/dbi599/test_space
AF_PATH=${QQ_DIR}/${AF_FILE}
QQ_PATH=${QQ_DIR}/${QQ_BASE}.nc
VALIDATION_NOTEBOOK=${CODE_DIR}/${QQ_BASE}.ipynb
TEMPLATE_NOTEBOOK=${CODE_DIR}/validation.ipynb



## adjustment-factors: Calculate the QQ-scale adjustment factors
adjustment-factors : ${AF_PATH}
${AF_PATH} :
	${PYTHON} ${CODE_DIR}/calc_adjustment.py ${MODEL_VAR} ${MODEL_VAR} $@ --hist_files ${HIST_FILES} --ref_files ${FUTURE_FILES} --hist_time_bounds ${MODEL_BASE_START}-01-01 ${MODEL_BASE_END}-12-31 --ref_time_bounds ${FUTURE_START}-01-01 ${FUTURE_END}-12-31 --method ${METHOD} --input_hist_units ${MODEL_UNITS} --input_ref_units ${MODEL_UNITS} --output_units ${OUTPUT_UNITS} ${ADAPT_OPT} --verbose

## qqscale-projections: Calculate QQ-scaled climate projection data
qqscale-projections : ${QQ_PATH}
${QQ_PATH} : ${AF_PATH}
	${PYTHON} ${CODE_DIR}/apply_adjustment.py ${OBS_FILES} ${OBS_VAR} $< $@ --time_bounds ${OBS_BASE_START}-01-01 ${OBS_BASE_END}-12-31 --input_units ${OBS_UNITS} --adjustment_units ${OUTPUT_UNITS} --output_units ${OUTPUT_UNITS} --verbose

## validation : Create validation plots for QQ-scaled climate projection data
validation : ${VALIDATION_NOTEBOOK}
${VALIDATION_NOTEBOOK} : ${TEMPLATE_NOTEBOOK} ${AF_PATH} ${QQ_PATH}
	papermill -p adjustment_file $(word 2,$^) -p qq_file $(word 3,$^) -r hist_files "${HIST_FILES}" -r fut_files "${FUTURE_FILES}" -r obs_files "${OBS_FILES}" -r hist_time_bounds "${MODEL_BASE_START}-01-01 ${MODEL_BASE_END}-12-31" -r fut_time_bounds "${FUTURE_START}-01-01 ${FUTURE_END}-12-31" -r obs_time_bounds "${OBS_BASE_START}-01-01 ${OBS_BASE_END}-12-31" -p example_lat ${EXAMPLE_LAT} -p example_lon ${EXAMPLE_LON} -p example_month ${EXAMPLE_MONTH} -p cmip_units ${MODEL_UNITS} -p obs_units ${OBS_UNITS} -p qq_units ${OUTPUT_UNITS} -p cmip_var ${MODEL_VAR} -p obs_var ${OBS_VAR} $< $@

## help : show this message
help :
	@echo 'make [target] [-Bnf] CONFIG=config_file.mk'
	@echo ''
	@echo 'valid targets:'
	@grep -h -E '^##' ${MAKEFILE_LIST} | sed -e 's/## //g' | column -t -s ':'

