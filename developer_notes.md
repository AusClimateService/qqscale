## Developer notes

The command line programs in this repository use the
[bias adjustment and downscaling](https://xclim.readthedocs.io/en/stable/sdba.html) functionality in xclim. 

### Typical workflow

A typical quantile delta change workflow using xclim
starts by calculating the adjustment factors for each quantile:

```python
from xclim import sdba

QM = sdba.EmpiricalQuantileMapping.train(
    da_ssp, da_hist, nquantiles=100, group="time.month", kind="+"
)
```

The `group` determines the timescale for the adjustment factors
(see [grouping](https://xclim.readthedocs.io/en/stable/notebooks/sdba.html#Grouping) for options)
and the `kind` can be additive or multiplicative.
In this case adjustment factors for each month are calculated by
taking the difference between the quantiles from a future experiment (`da_ssp`)
and an historical experiment (`da_hist`).

The resulting xarray Dataset (`QM.ds`) contains two variables:
adjustment factor (`af`) and historical quantiles (`hist_q`).

The next step is to apply the adjustment factors to a dataset of interest.

```python
da_qq = QM.adjust(da_obs, extrapolation="constant", interp="nearest") 
```

For each value in the observational dataset (`da_obs`),
xclim looks up the nearest (`interp="nearest"`) quantile in `hist_q`,
finds the adjustment factor corresponding to that quantile value in `af`,
and then applies it to that observational value.
If the value lies beyond the range of values in `hist_q`,
then the adjustment factor for the first or last quantile is used
(i.e. `extrapolation="constant"`).
It is also possible to use linear or cubic interpolation (e.g. `interp="linear"`)
instead of just picking the nearest adjustment factor.

This quantile delta change approach is described by 
[Cannon et al (2015)](https://doi.org/10.1175/JCLI-D-14-00754.1)
and [Boe et al (2007)](https://doi.org/10.1002/joc.1602) has a nice schematic (Figure 2).

> **More complex methods**
>
> [Cannon et al (2015)](https://doi.org/10.1175/JCLI-D-14-00754.1) also define
> Detrended Quantile Mapping (DQM) and Quantile Delta Mapping (QDM),
> both of which build upon the traditional methods.
> See [`xclim.sdba.DetrendedQuantileMapping` and `xclim.sdba.adjustment.QuantileDeltaMapping`.


### Our workflow

The main difference between the typical xclim workflow and the
[method used at CSIRO](old_code/README.md) is that quantile changes
are mapped directly from model derived adjustment factors to observations.
In other words, an adjustment factor is selected for a particular observed value
based on the nearest (or interpolated surrounding) observed quantile,
not the nearest historical model quantile (i.e. not `hist_q`).

To achieve the CSIRO method,
you can calculate the observed quantiles using `calc_quantiles.py`
and then pass those quantiles to `apply_adjustment.py` using the `--reference_quantile_file` option.
The `apply_adjustment` script then replaces `hist_q` with
the observed quantiles before performing the adjustment.
