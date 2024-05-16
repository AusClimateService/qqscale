"""Command line program for applying QQ-scaling adjustment factors."""

import yaml
import logging
import argparse
from datetime import datetime
from contextlib import suppress

import numpy as np
import xarray as xr
import xclim as xc
from xclim import sdba
import dask.diagnostics

import utils


def amend_attributes(ds, input_var, input_attrs, metadata_file):
    """Amend file attributes.

    Parameters
    ----------
    ds : xarray Dataset
        Dataset to be amended
    input_var : str
        Variable in ds
    input_attrs : dict
        Global attributes from the original input data file
    metadata_file : str
        Path to YAML file with user defined attributes

    Notes
    -----
    The metadata_file can specify global attributes to keep
    (all input file global attributes are removed by default)
    and to create/overwrite.

    It can also specify variable attributes to remove
    (all input variable attributes are kept by default)
    or create/overwrite.

    An example metadata YAML file looks like:

    rename:
      - precip : pr
    global_keep:
      - domain
      - domain_id
    global_overwrite:
      - product: bias-adjusted-output
      - project_id: CORDEX-Adjust
    var_remove:
      - pr:
        - frequency
        - length_scale_for_analysis
    var_overwrite:
      - pr:
        - long_name: "precipitation rate"
    """

    with open(metadata_file, 'r') as reader:
        metadata_dict = yaml.load(reader, Loader=yaml.BaseLoader)

    valid_keys = ['rename', 'global_keep', 'global_overwrite', 'var_remove', 'var_overwrite']
    for key in metadata_dict.keys():
        if key not in valid_keys:
            raise KeyError(f"Invalid metadata key: {key}")

    # Variable attributes
    if 'rename' in metadata_dict:
        for old_var, new_var in metadata_dict['rename'].items():
            with suppress(ValueError):
                ds = ds.rename({old_var: new_var})

    if 'var_remove' in metadata_dict:
        for var, attr_list in metadata_dict['var_remove'].items():
             for attr in attr_list:
                 with suppress(KeyError):
                     del ds[var].attrs[attr]
    if 'var_overwrite' in metadata_dict:
        for var, attr_dict in metadata_dict['var_overwrite'].items():
            for attr, value in attr_dict.items():
                with suppress(KeyError):
                    ds[var].attrs[attr] = value

    # Global attributes
    if 'global_keep' in metadata_dict:
        for attr in metadata_dict['global_keep']:
            with suppress(KeyError):
                ds.attrs[attr] = input_attrs[attr]
    if 'global_overwrite' in metadata_dict:
        for attr, value in metadata_dict['global_overwrite'].items():
            ds.attrs[attr] = value 
            if value == 'ecdfm':
                with suppress(KeyError):
                    ds[input_var].attrs['long_name'] = 'Bias-Adjusted ' + ds[input_var].attrs['long_name']
    ds.attrs['creation_date'] = datetime.now().isoformat()

    return ds


def adjust(
    ds,
    var,
    ds_adjust,
    spatial_grid='input',
    interp='nearest',
    ssr=False,
    max_af=None,
    ref_time=False,
    valid_min=None,
    valid_max=None,
    output_tslice=None,
    outfile_attrs=None,
):
    """Apply qq-scale adjustment factors.

    Parameters
    ----------
    ds : xarray Dataset
        Data to be adjusted
    var : str
        Variable to be adjusted (i.e. in ds)
    ds_adjust : xarray Dataset
        Adjustment factors calculated using train.train
    spatial_grid : {'input', 'af'}, default 'input'
        Spatial grid for output data (choices are input data or adjustment factor grid)
    interp : {'nearest', 'linear', 'cubic'}, default 'nearest'
        Method for interpolation of adjustment factors
    ssr : bool, default False
        Perform singularity stochastic removal
    max_af : float, optional
        Maximum limit for adjustment factors
    ref_time : bool, default False
        Adjust the output time axis so it matches the reference data
    valid_min : float, optional
        Minimum valid value (input and output data is clipped to this value)
    valid_max : float, optional
        Maximum valid value (input and output data is clipped to this value)
    output_tslice : list, optional
        Return a time slice of the adjusted data
        Format: ['YYYY-MM-DD', 'YYYY-MM-DD']
    outfile_attrs : str, optional
        Apply file attributes defined for bias adjusted CORDEX simulations for a given obs dataset
        
    Returns
    -------
    xarray Dataset    
    """

    ds_adjust = ds_adjust[['af', 'hist_q']]
    af_units = ds_adjust['hist_q'].attrs['units']
    infile_units = ds[var].attrs['units']    
    assert infile_units == af_units, \
        f"input file units {infile_units} differ from adjustment factor units {af_units}"

    dims = ds[var].dims
    on_spatial_grid = ('lat' in dims) and ('lon' in dims)
    if on_spatial_grid:
        if len(ds_adjust['lat']) != len(ds['lat']):
            if spatial_grid == 'input':
                logging.info('Regridding adjustment factors to input data grid')
                ds_adjust = utils.regrid(ds_adjust, ds)
            elif spatial_grid == 'af':
                logging.info('Regridding input data to adjustment factor grid')
                ds = utils.regrid(ds, ds_adjust, variable=var)
        assert len(ds_adjust['lat']) == len(ds['lat'])
        assert len(ds_adjust['lon']) == len(ds['lon'])

    qm = sdba.QuantileDeltaMapping.from_dataset(ds_adjust)
    hist_q_shape = qm.ds['hist_q'].shape
    hist_q_chunksizes = qm.ds['hist_q'].chunksizes
    af_shape = qm.ds['af'].shape
    af_chunksizes = qm.ds['af'].chunksizes
    logging.info(f'hist_q array size: {hist_q_shape}')
    logging.info(f'hist_q chunk size: {hist_q_chunksizes}')
    logging.info(f'af array size: {af_shape}')
    logging.info(f'af chunk size: {af_chunksizes}')

    if ssr:
        da = utils.apply_ssr(ds[var])
    else:
        da = ds[var]

    if max_af:
        ds_adjust['af'] = ds_adjust['af'].where(ds_adjust['af'] < max_af, max_af)

    qq = qm.adjust(da, extrapolation='constant', interp=interp)
    qq = qq.rename(var)
    if on_spatial_grid:
        qq['lat'] = ds['lat']
        qq['lon'] = ds['lon']
        qq = qq.transpose('lat', 'lon', ...)
    qq = qq.transpose('time', ...) 

    if ssr:
        qq = utils.reverse_ssr(qq)
        
    if (valid_min is not None) or (valid_max is not None):
        qq = qq.clip(min=valid_min, max=valid_max, keep_attrs=True) 

    qq = qq.to_dataset()    
    if ref_time:
        new_start_date = ds_adjust.attrs['reference_period_start'] 
        time_adjustment = np.datetime64(new_start_date) - qq['time'][0]
        qq['time'] = qq['time'] + time_adjustment

    if output_tslice:
        start_date, end_date = output_tslice
        qq = qq.sel({'time': slice(start_date, end_date)})

    qq.attrs['xclim'] = qq[var].attrs['history']
    del qq[var].attrs['history']
    del qq[var].attrs['bias_adjustment']
    with suppress(KeyError):
        del qq[var].attrs['cell_methods']
    if outfile_attrs:
        qq = amend_attributes(qq, var, ds.attrs, outfile_attrs)

    return qq


def main(args):
    """Run the program."""

    dask.diagnostics.ProgressBar().register()
    ds = utils.read_data(
        args.infiles,
        args.var,
        rename_var=args.rename_var,
        time_bounds=args.adjustment_tbounds,
        input_units=args.input_units,
        output_units=args.output_units,
        use_cftime=False,
        valid_min=args.valid_min,
        valid_max=args.valid_max,
    )
    var = args.rename_var if args.rename_var else args.var

    ds_adjust = xr.open_dataset(args.adjustment_file)

    qq = adjust(
        ds,
        var,
        ds_adjust,
        spatial_grid=args.spatial_grid,
        interp=args.interp,
        ssr=args.ssr,
        max_af=args.max_af,
        ref_time=args.ref_time,
        valid_min=args.valid_min,
        valid_max=args.valid_max,
        output_tslice=args.output_tslice,
        outfile_attrs=args.outfile_attrs,
    )
    infile_logs = {}
    if 'history' in ds_adjust.attrs:
        infile_logs[args.adjustment_file] = ds_adjust.attrs['history']
    if args.keep_history and ('history' in ds.attrs):
        infile_logs[args.infiles[0]] = ds.attrs['history']
    qq.attrs['history'] = utils.get_new_log(infile_logs=infile_logs)

    encoding = {}
    outfile_vars = list(qq.coords) + list(qq.keys())
    for outfile_var in outfile_vars:
        encoding[outfile_var] = {'_FillValue': None}
    if args.compress:
        encoding[var]['least_significant_digit'] = 2
        encoding[var]['zlib'] = True
    if args.output_time_units:
        encoding['time']['units'] = args.output_time_units.replace('_', ' ')
    qq.to_netcdf(args.outfile, encoding=encoding)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        argument_default=argparse.SUPPRESS,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
                          
    parser.add_argument("infiles", type=str, nargs='*', help="input data (to be adjusted)")           
    parser.add_argument("var", type=str, help="variable to process")
    parser.add_argument("adjustment_file", type=str, help="adjustment factor file")
    parser.add_argument("outfile", type=str, help="output file")

    parser.add_argument("--rename_var", type=str, default=None, help='rename var to value of rename_var')
    parser.add_argument("--input_units", type=str, default=None, help="input data units")
    parser.add_argument("--output_units", type=str, default=None, help="output data units")
    parser.add_argument(
        "--adjustment_tbounds",
        type=str,
        nargs=2,
        metavar=('START_DATE', 'END_DATE'),
        default=None,
        help="time bounds over which to calculate quantiles for adjustments [use YYYY-MM-DD format]"
    )
    parser.add_argument(
        "--output_tslice",
        type=str,
        nargs=2,
        metavar=('START_DATE', 'END_DATE'),
        default=None,
        help="return a time slice of the adjusted data [use YYYY-MM-DD format]"
    )
    parser.add_argument(
        "--ref_time",
        action="store_true",
        default=False,
        help='Shift output time axis to match reference dataset',
    )
    parser.add_argument(
        "--spatial_grid",
        type=str,
        choices=('input', 'af'),
        default='input',
        help="Spatial grid for output data (input data or adjustment factor grid)",
    )
    parser.add_argument(
        "--interp",
        type=str,
        choices=('nearest', 'linear', 'cubic'),
        default='nearest',
        help="Method for interpolation of adjustment factors",
    )
    parser.add_argument(
        "--max_af",
        type=float,
        default=None,
        help="Maximum limit for adjustment factors",
    )
    parser.add_argument(
        "--ssr",
        action="store_true",
        default=False,
        help='Perform Singularity Stochastic Removal',
    )
    parser.add_argument(
        "--valid_min",
        type=float,
        default=None,
        help="Minimum valid value",
    )
    parser.add_argument(
        "--valid_max",
        type=float,
        default=None,
        help="Maximum valid value",
    )
    parser.add_argument(
        "--output_time_units",
        type=str,
        default=None,
        help="""Time units for output file (e.g. 'days_since_1950-01-01')""",
    )
    parser.add_argument(
        "--outfile_attrs",
        type=str,
        default=None,
        help='YAML file with outfile attributes',
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help='Set logging level to INFO',
    )
    parser.add_argument(
        "--compress",
        action="store_true",
        default=False,
        help="compress the output data file"
    )
    parser.add_argument(
        "--keep_history",
        action="store_true",
        default=False,
        help="append to the history attribute of the input files"
    )
    args = parser.parse_args()
    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level)
    with dask.diagnostics.ResourceProfiler() as rprof:
        main(args)
    utils.profiling_stats(rprof)
