# Workflow for applying singularity stochastic removal to precipitation data files 

.PHONY: help

include ${CONFIG}

#PYTHON=/g/data/wp00/users/dbi599/miniconda3/envs/cih/bin/python
PYTHON=/g/data/xv83/dbi599/miniconda3/envs/qqscale/bin/python
CODE_DIR=/g/data/wp00/shared_code/qqscale


## ssr-hist: Apply Singularity Stochastic Removal to historical data
ssr-hist : ${HIST_DATA}
${HIST_DATA} : 
	${PYTHON} ${CODE_DIR}/apply_ssr.py ${HIST_FILES_ORIG} ${HIST_VAR} $@ --time_bounds ${HIST_START}-01-01 ${HIST_END}-12-31 --input_units ${HIST_UNITS} --output_units ${OUTPUT_UNITS}

## ssr-ref: Apply Singularity Stochastic Removal to reference data
ssr-ref : ${REF_DATA}
${REF_DATA} : 
	${PYTHON} ${CODE_DIR}/apply_ssr.py ${REF_FILES_ORIG} ${REF_VAR} $@ --time_bounds ${REF_START}-01-01 ${REF_END}-12-31 --input_units ${REF_UNITS} --output_units ${OUTPUT_UNITS}

## ssr-target: Apply Singularity Stochastic Removal to target data
ssr-target : ${TARGET_DATA}
${TARGET_DATA} : 
	${PYTHON} ${CODE_DIR}/apply_ssr.py ${TARGET_FILES_ORIG} ${TARGET_VAR} $@ --time_bounds ${TARGET_START}-01-01 ${TARGET_END}-12-31 --input_units ${TARGET_UNITS} --output_units ${OUTPUT_UNITS}

## all : Apply Singularity Stochastic Removal to historical, reference and target data
all : ${HIST_DATA} ${REF_DATA} ${TARGET_DATA}

## help : show this message
help :
	@echo 'make [target] -f ssr.mk [-Bn] CONFIG=config_file.mk'
	@echo ''
	@echo 'valid targets:'
	@grep -h -E '^##' ${MAKEFILE_LIST} | sed -e 's/## //g' | column -t -s ':'

