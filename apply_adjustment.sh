# Break down QQ-scaling adjustment into longitude chunks
#
# Usage: $ bash apply_adjustment.sh {variable} {adjustment_file} {output_file} {time_start} {time_end} {n_chunks} {obs_files}

variable=$1
shift
adjustment_file=$1
shift
output_file=$1
shift
time_start=$1
shift
time_end=$1
shift
n_chunks=$1
shift
obs_files=$@

if [ "${variable}" == "tmax" ]; then
        units="--obs_units C --adjustment_units C --output_units C"
fi

for chunk_index in $(seq 1 ${n_chunks}); do 
	echo "chunk ${chunk_index} of ${n_chunks}"
        chunk_label=$(printf "%.2d" "$chunk_index")
        tempfile=`echo ${output_file} | sed s:.nc:_lon-chunk-${chunk_label}.nc:`
        command="python apply_adjustment.py ${obs_files} ${variable} ${adjustment_file} ${tempfile} --lon_chunking ${chunk_index} ${n_chunks} --time_bounds ${time_start} ${time_end} ${units}"
        echo ${command}
        ${command}
done
