"""Command line program for applying QQ-scaling adjustment factors."""
import pdb
import argparse
import time

import numpy as np
import xarray as xr
import xclim as xc
from xclim import sdba
import xesmf as xe
import cmdline_provenance as cmdprov
import dask.diagnostics


dask.diagnostics.ProgressBar().register()


def check_units(da_obs, qm, obs_units, aj_units, output_units):
    """Check units and convert if necessary."""

    if obs_units:
        da_obs.attrs['units'] = obs_units
    if aj_units:
        qm.ds['af'].attrs['units'] = aj_units
        qm.ds['hist_q'].attrs['units'] = aj_units

    if output_units:
        if da_obs.attrs['units'] != output_units:
            da_obs = xc.units.convert_units_to(da_obs, output_units)
        if qm.ds['af'].attrs['units'] != output_units:
            qm.ds['af'] = xc.units.convert_units_to(qm.ds['af'], output_units)
        if qm.ds['hist_q'].attrs['units'] != output_units:
            qm.ds['hist_q'] = xc.units.convert_units_to(qm.ds['hist_q'], output_units)
    
    return da_obs, qm


def main(args):
    """Run the program."""

    timer_start = time.perf_counter()

    ds_obs = xr.open_mfdataset(args.obs_files)
    start_obs, end_obs = args.time_bounds
    ds_obs = ds_obs.sel({'time': slice(start_obs, end_obs)})
    ds_obs = ds_obs.chunk({'time': -1, 'lon': 20})

    ds_adjust = xr.open_dataset(args.adjustment_file)
    qm = sdba.QuantileDeltaMapping.from_dataset(ds_adjust)
    regridder = xe.Regridder(qm.ds, ds_obs, "bilinear")
    qm.ds = regridder(qm.ds)
    qm.ds = qm.ds.compute()

    chunk_num, total_chunks = args.lon_chunking
    lon_chunks = np.array_split(qm.ds['lon'], total_chunks)
    lon_selection = lon_chunks[chunk_num - 1] 
    ds_obs = ds_obs.sel({'lon': lon_selection})
    qm.ds = qm.ds.sel({'lon': lon_selection}) 
    da_obs = ds_obs[args.variable]

    da_obs, qm = check_units(
        da_obs,
        qm,
        args.obs_units,
        args.adjustment_units,
        args.output_units
    )
    qq_obs = qm.adjust(
        da_obs,
        extrapolation="constant",
        interp="linear"
    )
    
    qq_obs = qq_obs.rename(args.variable)
    qq_obs = qq_obs.transpose('time', 'lat', 'lon')
    new_start_date = ds_adjust.attrs['future_period_start'] 
    time_adjustment = np.datetime64(new_start_date) - qq_obs['time'][0]
    qq_obs['time'] = qq_obs['time'] + time_adjustment

    qq_obs.attrs['history'] = cmdprov.new_log(
        infile_logs={args.adjustment_file: ds_adjust.attrs['history']},
    )
    qq_obs.to_netcdf(args.output_file)

    timer_end = time.perf_counter()
    total_time = (timer_end - timer_start) / 60.0
    print(f'Adjustment duration = {total_time:0.4f} minutes')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        argument_default=argparse.SUPPRESS,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
                          
    parser.add_argument("obs_files", type=str, nargs='*', help="observation data")           
    parser.add_argument("variable", type=str, help="model variable to process")
    parser.add_argument("adjustment_file", type=str, help="adjustment factor file")
    parser.add_argument("output_file", type=str, help="output file")

    parser.add_argument("--obs_units", type=str, default=None, help="obs data units")
    parser.add_argument("--adjustment_units", type=str, default=None, help="adjustment data units")
    parser.add_argument("--output_units", type=str, default=None, help="output data units")
    parser.add_argument(
        "--lon_chunking",
        type=int,
        nargs=2,
        metavar=('CHUNK_NUMBER', 'TOTAL_CHUNKS'),
        default=(1, 1),
        help="subset data along longitude dimension (chunk numbers start at 1)"
    )
    parser.add_argument(
        "--time_bounds",
        type=str,
        nargs=2,
        metavar=('START_DATE', 'END_DATE'),
        required=True,
        help="observations time bounds in YYYY-MM-DD format"
    )
    args = parser.parse_args()
    main(args)
