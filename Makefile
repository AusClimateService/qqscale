# Workflow for QDM, EDCDFm or EQCDFm
#
#   CONFIG file needs the following variables defined:
#   - Methods details: SCALING, SSR
#   - Paths for files that will be created: AF_PATH, QQ_PATH, VALIDATION_NOTEBOOK 
#   - Directories that need to be created for those files: OUTPUT_REF_DIR, OUTPUT_TARGET_DIR
#   - Variables: HIST_VAR, REF_VAR, TARGET_VAR
#   - Input data: HIST_DATA, REF_DATA, TARGET_DATA
#   - Time bounds: HIST_START, HIST_END, REF_START, REF_END, TARGET_START, TARGET_END
#   - Units: HIST_UNITS, REF_UNITS, TARGET_UNITS, OUTPUT_UNITS
#   - Notebook example parameters: EXAMPLE_LAT, EXAMPLE_LON, EXAMPLE_MONTH
#
#  See config_qdc.mk and config_qmba.mk for examples.

.PHONY: help

include ${CONFIG}

#PYTHON=/g/data/wp00/users/dbi599/miniconda3/envs/cih/bin/python
PYTHON=/g/data/xv83/dbi599/miniconda3/envs/qqscale/bin/python
PAPERMILL=/g/data/xv83/dbi599/miniconda3/envs/qqscale/bin/papermill
CODE_DIR=/g/data/wp00/shared_code/qqscale
TEMPLATE_NOTEBOOK=${CODE_DIR}/validation_${METHOD}.ipynb

## train: Calculate the QQ-scale adjustment factors
train : ${AF_PATH}
${AF_PATH} :
	mkdir -p ${OUTPUT_REF_DIR}
	${PYTHON} ${CODE_DIR}/train.py ${HIST_VAR} ${REF_VAR} $@ --hist_files ${HIST_DATA} --ref_files ${REF_DATA} --hist_time_bounds ${HIST_START}-01-01 ${HIST_END}-12-31 --ref_time_bounds ${REF_START}-01-01 ${REF_END}-12-31 --scaling ${SCALING} --input_hist_units ${HIST_UNITS} --input_ref_units ${REF_UNITS} --output_units ${OUTPUT_UNITS} --verbose

## adjust: Apply adjustment factors to the target data
adjust : ${QQ_PATH}
${QQ_PATH} : ${AF_PATH}
	${PYTHON} ${CODE_DIR}/adjust.py ${TARGET_DATA} ${TARGET_VAR} $< $@ --time_bounds ${TARGET_START}-01-01 ${TARGET_END}-12-31 --input_units ${TARGET_UNITS} --output_units ${OUTPUT_UNITS} --ref_time ${SSR} --verbose

## validation : Create validation notebook
validation : ${VALIDATION_NOTEBOOK}
${VALIDATION_NOTEBOOK} : ${TEMPLATE_NOTEBOOK} ${AF_PATH} ${QQ_PATH}
	${PAPERMILL} -p adjustment_file $(word 2,$^) -p qq_file $(word 3,$^) -r hist_files "${HIST_DATA}" -r ref_files "${REF_DATA}" -r target_files "${TARGET_DATA}" -r hist_time_bounds "${HIST_START}-01-01 ${HIST_END}-12-31" -r ref_time_bounds "${REF_START}-01-01 ${REF_END}-12-31" -r target_time_bounds "${TARGET_START}-01-01 ${TARGET_END}-12-31" -p example_lat ${EXAMPLE_LAT} -p example_lon ${EXAMPLE_LON} -p example_month ${EXAMPLE_MONTH} -p hist_units ${HIST_UNITS} -p ref_units ${REF_UNITS} -p target_units ${TARGET_UNITS} -p output_units ${OUTPUT_UNITS} -p hist_var ${HIST_VAR} -p ref_var ${REF_VAR} -p target_var ${TARGET_VAR} -p scaling ${SCALING} $< $@

## help : show this message
help :
	@echo 'make [target] [-Bn] CONFIG=config_file.mk'
	@echo ''
	@echo 'valid targets:'
	@grep -h -E '^##' ${MAKEFILE_LIST} | sed -e 's/## //g' | column -t -s ':'

