######## Code requirements ########
#
# CDO - Climate Data Operators:  https://code.mpimet.mpg.de/projects/cdo
#
# NCO - NetCDF Operators: http://nco.sourceforge.net/
#
# qqscale - https://bitbucket.csiro.au/scm/ccam/qqscale.git
#    Dependencies:
#       netcdf development libraries (libnetcdf-devel)
#       Intel fortran compiler
#
###################################


######## HPC Queue Oprions ########
#PBS -N qqscale
#PBS -q copyq 
#PBS -l walltime=12:00:00,mem=32G,ncpus=8

######## SETUP ########
WORKING_DIR=/scratch/${PROJECT}/${USER}/qqscale

VARIABLE=tasmax     # tasmax only
MODEL=ACCESS1-0     # ACCESS1-0/ACCESS1-3
EXPERIMENT=rcp85    # rcp26/rcp45/rcp85
MODE=addqq          # addqq/mulqq

# Set based on model data period
hyear=2000
fyear=2030

OBS_DIR=${WORKING_DIR}/obs
MODEL_DIR=${WORKING_DIR}/model
TMP_DIR=${WORKING_DIR}/tmp

OMP_NUM_THREADS=8

mkdir -p $WORKING_DIR $OBS_DIR $MODEL_DIR $TMP_DIR
cd $WORKING_DIR

# Load required code/libraries (Gadi specific)
module load cdo/1.9.8
module load nco/4.9.2
module load intel-compiler/2020.3.304 intel-mkl/2020.3.304
module load netcdf/4.7.4

# Retrive and compile scaling code
# TODO move to public CCS repo and version/tag?
git clone https://bitbucket.csiro.au/scm/ccam/qqscale.git
cd qqscale && make

######## Source Data ########

# AGCD - Australian Gridded Climate Data (Maximum Temperature)
# https://geonetwork.nci.org.au/geonetwork/srv/eng/catalog.search#/metadata/f6475_9317_5747_6204
# Availible on Gadi at /g/data/zv2 or via https://dapds00.nci.org.au/thredds/catalog/zv2/agcd/v1/catalog.html
cd $OBS_DIR
for num in `seq 1981 2010`; do 
    wget -nd -nc https://dapds00.nci.org.au/thredds/fileServer/zv2/agcd/v1/tmax/mean/r005/01day/agcd_v1_tmax_mean_r005_daily_${num}.nc
done

# Prepare observed data (merge and rename)
# AGCD does not use OBS4MIP or CMIP ontology/conventions
OBS_DATA=${OBS_DIR}/${VARIABLE}_day_AGCD_v1_19750101-20101231.nc
cdo -L -O chname,tmax,${VARIABLE} -mergetime ${OBS_DIR}/agcd_v1_tmax_mean_r005_daily_* ${OBS_DATA} &

# Modelled Climate Data (${MODEL} historical and RCP8.5 Maximum Temperature)
# https://geonetwork.nci.org.au/geonetwork/srv/eng/catalog.search#/metadata/f7710_6537_7396_4995
# Availivle on Gadi at /g/data/rr3 or https://dapds00.nci.org.au/thredds/catalog/rr3/CMIP5/output1/CSIRO-BOM/${MODEL}/catalog.html
# Note only the Australian models are availible externaly from NCI and must be sourced from the ESGF or relevant institute
# All CMIP5/6 models can be found on Gadi in projects oi10,fs38,al33,rr3 or for convenience /g/data/r87/DRSv3
cd $MODEL_DIR
wget -nd -nc https://dapds00.nci.org.au/thredds/fileServer/rr3/CMIP5/output1/CSIRO-BOM/${MODEL}/historical/day/atmos/day/r1i1p1/v20131108/${VARIABLE}/${VARIABLE}_day_${MODEL}_historical_r1i1p1_19750101-19991231.nc
wget -nd -nc https://dapds00.nci.org.au/thredds/fileServer/rr3/CMIP5/output1/CSIRO-BOM/${MODEL}/historical/day/atmos/day/r1i1p1/v20131108/${VARIABLE}/${VARIABLE}_day_${MODEL}_historical_r1i1p1_20000101-20051231.nc
wget -nd -nc https://dapds00.nci.org.au/thredds/fileServer/rr3/CMIP5/output1/CSIRO-BOM/${MODEL}/${EXPERIMENT}/day/atmos/day/r1i1p1/v20131108/${VARIABLE}/${VARIABLE}_day_${MODEL}_${EXPERIMENT}_r1i1p1_20060101-20301231.nc
wget -nd -nc https://dapds00.nci.org.au/thredds/fileServer/rr3/CMIP5/output1/CSIRO-BOM/${MODEL}/${EXPERIMENT}/day/atmos/day/r1i1p1/v20131108/${VARIABLE}/${VARIABLE}_day_${MODEL}_${EXPERIMENT}_r1i1p1_20310101-20551231.nc

# Prepare historical modelled data
MODEL_HIST_DATA=${MODEL_DIR}/${VARIABLE}_day_${MODEL}_historical_r1i1p1_19750101-20051231.nc
cdo -L -O mergetime ${MODEL_DIR}/${VARIABLE}_day_${MODEL}_historical_r1i1p1_19750101-19991231.nc \
  ${MODEL_DIR}/${VARIABLE}_day_${MODEL}_historical_r1i1p1_20000101-20051231.nc \
  ${MODEL_HIST_DATA} &

# Prepare 2030
MODEL_FUTURE_DATA=${MODEL_DIR}/${VARIABLE}_day_${MODEL}_${EXPERIMENT}_r1i1p1_20210101-20401231.nc
cdo -L -O seldate,20210101,20401231 -mergetime \
    ${MODEL_DIR}/${VARIABLE}_day_${MODEL}_${EXPERIMENT}_r1i1p1_20060101-20301231.nc \
    ${MODEL_DIR}/${VARIABLE}_day_${MODEL}_${EXPERIMENT}_r1i1p1_20310101-20551231.nc \
    ${MODEL_FUTURE_DATA}

wait

######## Calculate Scaled Data "Application Ready" ########
# Using CORDEX bias adjusted data structure (except rcm model name is bias adjustment method)
# <activity>/<product>/<Domain>/<Institution>/<GCMModelName>/<CMIP5ExperimentName>/<CMIP5EnsembleMember>/<RCMModelName>/<RCMVersionID>/<Frequency>/<VariableName>.
# TODO: Should we use CMIP directory strucuture instead (and do they have a bias adjust structure)?

CORDEX_DIR=CORDEX-Adjust/bias-adjusted-output/AUS-5/CSIRO/CSIRO-BOM-${MODEL}/${EXPERIMENT}/r1i1p1/CSIRO-QQS-AGCD1-1981-2010/v1/day/${VARIABLE}
CORDEX_FILE=${VARIABLE}_AUS_${MODEL}_${EXPERIMENT}_r1i1p1_CSIRO-QQS-AGCD1-1981-2010_v1_day
mkdir -p ${WORKING_DIR}/${CORDEX_DIR}
cd $WORKING_DIR

for MONTH in 01 02 03 04 05 06 07 08 09 10 11 12; do

  
  cdo -selmon,$MONTH ${OBS_DATA} ${OBS_DATA}-${MONTH}.nc &
  cdo -selmon,$MONTH ${MODEL_HIST_DATA} ${MODEL_HIST_DATA}-${MONTH}.nc &
  cdo -selmon,$MONTH ${MODEL_FUTURE_DATA} ${MODEL_FUTURE_DATA}-${MONTH}.nc
  wait

  # Historic percentile data
  ${WORKING_DIR}/qqscale/qqscale -m calcqq -v ${VARIABLE} -i ${MODEL_HIST_DATA}-${MONTH}.nc -o ${MODEL_HIST_DATA}-${MONTH}-percentile.nc
  # Future percentile data
  ${WORKING_DIR}/qqscale/qqscale -m calcqq -v ${VARIABLE} -i ${MODEL_FUTURE_DATA}-${MONTH}.nc -o ${MODEL_FUTURE_DATA}-${MONTH}-percentile.nc

  #TODO: Calculate percentile of observational data so it can be cached/reused

  # Created percentiled scaled future data
  ${WORKING_DIR}/qqscale/qqscale -m $MODE -v $VARIABLE \
    -i ${OBS_DATA}-${MONTH}.nc \
    -a ${MODEL_HIST_DATA}-${MONTH}-percentile.nc \
    -b ${MODEL_FUTURE_DATA}-${MONTH}-percentile.nc \
    -o ${TMP_DIR}/mon-scaled-${MONTH}_${CORDEX_FILE}.nc


  cdo -splityear ${TMP_DIR}/mon-scaled-${MONTH}_${CORDEX_FILE}.nc ${TMP_DIR}/yearmon-scaled-${MONTH}_${CORDEX_FILE}.

  for fileyear in `ls ${TMP_DIR}/yearmon-scaled-${MONTH}_*.nc`; do
    YEAR=`echo $fileyear | cut -d. -f2`
    mv $fileyear ${TMP_DIR}/yearmon-scaled_${CORDEX_FILE}_${YEAR}${MONTH}.nc
  done

done

cdo mergetime ${TMP_DIR}/yearmon-scaled_${CORDEX_FILE}_??????.nc ${TMP_DIR}/${CORDEX_FILE}.nc

# Adjust time axis
cdo setreftime,"$hyear-01-01","00:00:00" ${TMP_DIR}/${CORDEX_FILE}.nc ${WORKING_DIR}/${CORDEX_DIR}/${CORDEX_FILE}-20200101-20401231.nc
ncatted -O -a units,time,o,c,"days since $fyear-01-01 00:00:00" ${WORKING_DIR}/${CORDEX_DIR}/${CORDEX_FILE}-20200101-20401231.nc

# Cleanup
rm ${TMP_DIR}/mon-scaled-*.nc
rm ${TMP_DIR}/yearmon-scaled-*.nc
rm ${TMP_DIR}/${CORDEX_FILE}.nc
