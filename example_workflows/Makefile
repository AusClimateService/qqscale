.PHONY: help

include ${CONFIG}

#PYTHON=/g/data/wp00/users/dbi599/miniconda3/envs/cih/bin/python
PYTHON=/g/data/xv83/dbi599/miniconda3/envs/qqscale/bin/python
CODE_DIR=/g/data/wp00/shared_code/qqscale
QQ_DIR=/g/data/wp00/users/dbi599/test_space
AF_PATH=${QQ_DIR}/${AF_FILE}
QQ_PATH=${QQ_DIR}/${QQ_BASE}.nc
VALIDATION_NOTEBOOK=${CODE_DIR}/example_validation/${QQ_BASE}.ipynb
TEMPLATE_NOTEBOOK=${CODE_DIR}/example_validation/validation.ipynb


## adjustment-factors: Calculate the QQ-scale adjustment factors
adjustment-factors : ${AF_PATH}
${AF_PATH} :
	${PYTHON} ${CODE_DIR}/calc_adjustment.py ${HIST_VAR} ${REF_VAR} $@ --hist_files ${HIST_FILES} --ref_files ${REF_FILES} --hist_time_bounds ${HIST_START}-01-01 ${HIST_END}-12-31 --ref_time_bounds ${REF_START}-01-01 ${REF_END}-12-31 --method ${METHOD} --input_hist_units ${HIST_UNITS} --input_ref_units ${REF_UNITS} --output_units ${OUTPUT_UNITS} --grouping ${GROUPING} --verbose

## qqscale-projections: Calculate QQ-scaled climate projection data
qqscale-projections : ${QQ_PATH}
${QQ_PATH} : ${TARGET_SSR_PATH} ${AF_PATH}
	${PYTHON} ${CODE_DIR}/apply_adjustment.py ${TARGET_FILES} ${TARGET_VAR} $< ${OUTPUT_GRID} $@ --time_bounds ${TARGET_START}-01-01 ${TARGET_END}-12-31 --input_units ${TARGET_UNITS} --output_units ${OUTPUT_UNITS} --ref_time --verbose 

## validation : Create validation plots for QQ-scaled climate projection data
validation : ${VALIDATION_NOTEBOOK}
${VALIDATION_NOTEBOOK} : ${TEMPLATE_NOTEBOOK} ${AF_PATH} ${QQ_PATH}
	papermill -p adjustment_file $(word 2,$^) -p qq_file $(word 3,$^) -r hist_files "${HIST_FILES}" -r ref_files "${REF_FILES}" -r target_files "${TARGET_FILES}" -r hist_time_bounds "${HIST_START}-01-01 ${HIST_END}-12-31" -r ref_time_bounds "${REF_START}-01-01 ${REF_END}-12-31" -r target_time_bounds "${TARGET_START}-01-01 ${TARGET_END}-12-31" -p example_lat ${EXAMPLE_LAT} -p example_lon ${EXAMPLE_LON} -p example_month ${EXAMPLE_MONTH} -p hist_units ${HIST_UNITS} -p ref_units ${REF_UNITS} -p target_units ${TARGET_UNITS} -p output_units ${OUTPUT_UNITS} -p hist_var ${HIST_VAR} -p ref_var ${REF_VAR} -p target_var ${TARGET_VAR} $< $@

## help : show this message
help :
	@echo 'make [target] [-Bn] CONFIG=config_file.mk'
	@echo ''
	@echo 'valid targets:'
	@grep -h -E '^##' ${MAKEFILE_LIST} | sed -e 's/## //g' | column -t -s ':'

