## Developer notes

### xclim implementation

The command line programs in this repository use the
[bias adjustment and downscaling](https://xclim.readthedocs.io/en/stable/sdba.html) functionality in xclim. 

A typical Quantile Delta Change (QDC) workflow using xclim
starts by calculating the adjustment factors for each quantile:

```python
from xclim import sdba

QDC = sdba.QuantileDeltaMapping.train(
    da_sim, da_hist, nquantiles=100, group="time.month", kind="+"
)
```

The `group` determines the timescale for the adjustment factors
(see [grouping](https://xclim.readthedocs.io/en/stable/notebooks/sdba.html#Grouping) for options)
and the `kind` can be additive (`+`) or multiplicative (`*`).
In this case adjustment factors for each month are calculated by
taking the difference between the quantiles from a future experiment (`da_sim`)
and an historical experiment (`da_hist`).

The resulting xarray Dataset (`QDC.ds`) contains the adjustment factors (`af`).
It can be useful to plot these adjustment factors to understand the climate signal
between the two experiments.

The next step is to apply the adjustment factors to a dataset of interest.

```python
da = QDC.adjust(da_ref, interp="nearest") 
```

For each value in the observational dataset (`da_ref`),
a corresponding quantile is calculated
(e.g. a 20C day might be the 0.6 quantile)
and then xclim looks up the nearest (`interp="nearest"`) adjustment factor to that quantile in `af`
and applies it to that observational value.
It is also possible to use linear or cubic interpolation (e.g. `interp="linear"`)
instead of just picking the nearest adjustment factor,
although often it makes very little difference to the end result.
(See [Wang and Chen (2013)](https://doi.org/10.1002/asl2.454) for an explanation of why
non-parametric methods like linear and cubic interpolation are preferred to
fitting a parametric distribution.)

#### Interpolation

According to the [documentation](https://xclim.readthedocs.io/en/stable/sdba.html#bias-adjustment-and-downscaling-algorithms),
the interpolation is done between quantiles (i.e. if a data value falls between two quantiles)
and also between adjustment factors to avoid discontinuities.
With respect to the latter, the adjustment factor interpolation is performed by
[`xclim.sdba.utils.interp_on_quantiles`](https://github.com/Ouranosinc/xclim/blob/master/xclim/sdba/utils.py#L363),
which in the two dimensional case (e.g. with `time.month` grouping) uses
[`scipy.interpolate.griddata`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.griddata.html)
to smooth out the two dimensional (quantile, month) `af` field. 
From playing around with the different interpolation options,
it appears that the two dimensional interpolation is cyclic
(e.g. January values are aware of nearby December values).

