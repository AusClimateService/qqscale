# Post-processing and analysis of QDC data

.PHONY: help

include ${CONFIG}

#PYTHON=/g/data/wp00/users/dbi599/miniconda3/envs/cih/bin/python
PYTHON=/g/data/xv83/dbi599/miniconda3/envs/qqscale/bin/python
PAPERMILL=/g/data/xv83/dbi599/miniconda3/envs/qqscale/bin/papermill
CODE_DIR=/g/data/wp00/shared_code/qqscale

## cih-metadata: Apply CIH metadata to the QQ-scaled projection data
cih-metadata : ${QQ_PATH}
${QQ_PATH} :
	${PYTHON} /g/data/wp00/shared_code/attribute-editing/define_attributes.py $@ qqscale-cmip6 /g/data/wp00/shared_code/attribute-editing/global_attributes.yml --del_var_attrs analysis_time analysis_version_number cell_methods frequency length_scale_for_analysis source history bias_adjustment number_of_stations_reporting --del_coord_attrs bounds --keep_attrs history xclim_version > metadata_fix.sh
	bash metadata_fix.sh
	rm metadata_fix.sh

## match-mean : Modify QQ-scaled data so mean change matches GCM
match-mean : ${QQ_MEAN_MATCH_PATH}
${QQ_MEAN_MATCH_PATH} : ${QQ_PATH}
	${PYTHON} ${CODE_DIR}/match_mean_change.py $< ${TARGET_VAR} $@ --output_units ${OUTPUT_UNITS} --hist_files ${HIST_FILES_ORIG} --hist_var ${HIST_VAR} --input_hist_units ${HIST_UNITS_ORIG} --ref_files ${REF_FILES_ORIG} --ref_var ${REF_VAR} --input_ref_units ${REF_UNITS_ORIG} --target_files ${TARGET_FILES_ORIG} --input_target_units ${TARGET_UNITS_ORIG} --hist_time_bounds ${HIST_START}-01-01 ${HIST_END}-12-31 --ref_time_bounds ${REF_START}-01-01 ${REF_END}-12-31 --target_time_bounds ${TARGET_START}-01-01 ${TARGET_END}-12-31 --scaling ${SCALING} --timescale ${MEAN_MATCH_TIMESCALE} --verbose

## help : show this message
help :
	@echo 'make [target] -f qdc-post-processing.mk [-Bn] CONFIG=config_file.mk'
	@echo ''
	@echo 'valid targets:'
	@grep -h -E '^##' ${MAKEFILE_LIST} | sed -e 's/## //g' | column -t -s ':'

