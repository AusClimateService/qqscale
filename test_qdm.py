"""Test quantile delta mapping"""

import pytest

import numpy as np
import pandas as pd
import xarray as xr

import train
import quantiles
import adjust


@pytest.fixture
def ds_hist():
    """Create an example historical dataset"""
    
    times = pd.date_range("2000-01-01", "2019-12-31", freq="D")
    times = times[(times.month != 2) | (times.day != 29)]
    
    da_hist = xr.DataArray(
        (
            -13 * np.cos(2 * np.pi * np.tile(np.arange(1, 366), 20) / 365)
            + 2 * np.random.random_sample((times.size,))
            + 20
            + 0.1 * np.arange(0, times.size) / 365
        ),  # "warming" of 1C per decade,
        dims=("time",),
        coords={"time": times},
        attrs={"units": "C"},
    )
    ds_hist = da_hist.to_dataset(name='tasmax')
    
    return ds_hist


@pytest.fixture
def ds_ref(ds_hist):
    """Create an example reference dataset.
    
    Perturbs historical data to create reference data.
      (add month number times 10 to historical values > 50th percentile)
    """
    
    da_hist = ds_hist['tasmax']
    monthly_quantiles = da_hist.groupby('time.month').quantile([0.5,], dim='time', keep_attrs=True)
    da_hist_by_month = da_hist.groupby('time.month')
    below_q50 = da_hist_by_month < monthly_quantiles.sel(quantile=0.5)
    ds_ref = ds_hist.copy()
    ds_ref['tasmax'] = da_hist_by_month.where(below_q50)
    ds_ref['tasmax'] = ds_ref['tasmax'].fillna(da_hist + (ds_ref['month'] * 10))
    del ds_ref['month']
    with xr.set_options(keep_attrs=True):
        ds_ref['tasmax'] = ds_ref['tasmax'] + 1
    
    times = pd.date_range("2040-01-01", "2059-12-31", freq="D")
    times = times[(times.month != 2) | (times.day != 29)]
    ds_ref['time'] = times
    
    return ds_ref


@pytest.fixture
def ref_q(ds_ref):
    """Calculate reference dataset quantiles."""
    
    ref_q = quantiles.quantiles(ds_ref, 'tasmax', 100)
    
    return ref_q


@pytest.fixture
def ds_target(ds_hist):
    """Create an example target dataset."""
    
    ds_target = ds_hist.copy()
    
    return ds_target


@pytest.fixture
def ds_adjust(ds_hist, ds_ref):
    """Calculate example adjustment factors."""
    
    ds_adjust = train.train(ds_hist, ds_ref, 'tasmax', 'tasmax', 'additive')

    return ds_adjust


@pytest.fixture
def ds_qq(ds_target, ds_adjust):
    """Calculate example QDM dataset."""
    
    ds_qq = adjust.adjust(
        ds_target,
        'tasmax',
        ds_adjust,
        reverse_ssr=False,
        ref_time=True,
        interp='nearest'
    )
    
    return ds_qq


@pytest.fixture
def qq_q(ds_qq):
    """Calculate example QDM dataset quantiles."""
    
    qq_q = quantiles.quantiles(ds_qq, 'tasmax', 100)
    
    return qq_q
    

def test_training(ds_adjust):
    """Test training step.
    
    Adjustment factors should match the perterbations
    applied by the ds_ref fixture.
    """
    
    actual_result = ds_adjust['af'].values
    expected_result = np.ones([100, 12])
    for month in range(12):
        perturbation = np.ones(50) + ((month + 1) * 10)
        expected_result[50:, month] = perturbation

    assert np.allclose(expected_result, actual_result)
        

@pytest.mark.parametrize("month", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
def test_adjustment(qq_q, ref_q, ds_adjust, month):
    """Test adjustment step.
    
    The quantile changes between ds_hist and ds_ref should match
      the quantile changes between ds_target and ds_q.
    """

    target_quantiles = ds_adjust['hist_q'].sel({'month': month}).values
    qq_quantiles = qq_q['tasmax'].sel({'month': month}).values
    hist_quantiles = ds_adjust['hist_q'].sel({'month': month}).values
    future_quantiles = ref_q['tasmax'].sel({'month': month}).values

    qq_quantile_change = qq_quantiles - target_quantiles
    model_quantile_change = future_quantiles - hist_quantiles

    assert np.allclose(qq_quantile_change, model_quantile_change)    

    

    
