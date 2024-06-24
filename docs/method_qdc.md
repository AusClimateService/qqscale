# Quantile Delta Change (QDC)

## Overview

One of the most widely used methods for producing climate projection data is the so-called "delta change" approach.
Rather than use the data from a model simulation of the future climate directly,
the delta change approach calculates the relative change between a future and historical modelled time period.
That relative change is then applied to observed data from the same historical time period
in order to produce an "application ready" time series for the future period.

While the simplest application of the delta change approach is to apply the mean model change to the observed data,
a popular alternative is to calculate and apply the delta changes on a quantile by quantile basis
(i.e. to adjust the variance of the distribution as opposed to just the mean).
For instance, if an observed historical temperature of $25^{\circ}$ Celsius corresponds to the 0.5 quantile (i.e. the median) in the observed data,
the difference between the median value in the future and historical model data
is added to that observed historical temperature in order to obtain the projected future temperature.

This *quantile delta change* (QDC) approach
([Olsson et al 2009](https://doi.org/10.1016/j.atmosres.2009.01.015);
[Willems & Vrac 2011](https://doi.org/10.1016/j.jhydrol.2011.02.030))
is expressed mathematically as follows:

$$x_{o,p} = x_{o,h} + F_{m,p}^{-1}(F_{o,h}(x_{o,h})) - F_{m,h}^{-1}(F_{o,h}(x_{o,h}))$$

where $F$ is the CDF of either the observations ($o$) or model ($m$) for an historic ($h$) or future/projection period ($p$).
That means $F_{m,p}^{-1}$ and $F_{m,h}^{-1}$ are the quantile functions (inverse CDF)
corresponding to the future and historical model simulations respectively.
Returning to our observed median value of $25^{\circ}$ (i.e. $x_{o,h} = 25$),
the corresponding CDF would return a value of 0.5 (i.e. $F_{o,h}(25) = 0.5$).
The difference between the future ( $F_{m,p}^{-1}(0.5)$ ) and historical model ( $F_{m,h}^{-1}(0.5)$ )
median values would then be added to the observed value of $25^{\circ}$ to get the projected future temperature.

For variables like precipitation, multiplicative as opposed to additive mapping is preferred
to avoid the possibility of producing future values less than zero:

$$x_{o,p} = x_{o,h} \times (F_{m,p}^{-1}(F_{o,h}(x_{o,h})) \div F_{m,h}^{-1}(F_{o,h}(x_{o,h})))$$

In the Climate Change in Australia project,
the quantile delta change approach
(referred to as [quantile-quantile scaling](https://www.climatechangeinaustralia.gov.au/en/obtain-data/application-ready-data/scaling-methods/)
in that project)
was used to produce application ready climate data.


## Methodological decisions

There are a number of choices to make when implementing QDC: 
- *Parametric or non-parametric*:
  It is generally accepted that non-parametric quantile mapping is best,
  so QDC is usually applied without fitting a parametric distribution to the data first.
  Our qqscale software takes a non-parametric / empirical approach.
- *Downscaling (when and how)*:
  Model data is usually on a coarser spatial grid than observations.
  Some authors downscale the model data first (e.g. via simple spatial interpolation or statistical downscaling)
  and then perform QDC.
  Others upscale the observations, perform QDC on the model grid and then downscale the result.
  Our qqscale software takes the most computationally efficient approach,
  which is to calculate the quantile changes on the model grid,
  downscale those change factors using bilinear interpolation
  and then apply them to the observations.
- *Time grouping*:
  It is common to apply quantile mapping methods to individual seasons or months separately
  to avoid conflating different times of the year
  (e.g. spring and autumn temperatures often occupy the same annual quantile space
  but may change in different ways between an historical and future simulation).
  When processing temperature data (or indeed any additive application of QDC)
  we commonly use monthly time grouping (i.e. process each month separately).
  We've found that something like a 30-day running window is far more computationally expensive
  and produces similar results to monthly grouping.
  When processing precipitation data (a multiplicative application of QDC)
  we've found (see [simple](https://github.com/AusClimateService/qq-workflows/blob/main/qdm-vs-ecdfm/seasonal_cycle_simple.ipynb)
  and [more complex](https://github.com/climate-innovation-hub/qq-workflows/blob/main/qdm-vs-ecdfm/seasonal_cycle.ipynb) notebooks)
  that in many locations the model bias in the timing of the seasonal cycle
  means that monthly time grouping dramatically modifies the climate trend in the data
  (i.e. the mean change between the future data produced by QDC and the observations
  is much different than the mean change between the future and historical model simulations).
  As such, we don't apply any time grouping when applying QDC to precipitation data.
- *Qunatiles*:
  Our qqscale software allows the user to specify
  the number of quantiles to calculate.
  We've found that it's best to have approximately 10 data values between each quanite.
  If you're processing 30 years of daily data,
  that means 100 quantiles if the time grouping is monthly
  or 1000 quantiles if no time grouping is applied. 
- *Adjustment factor smoothing*:
  By default, the delta change applied to each observational data point is the closest value from the array of adjustment factors.
  For example, it might be a 12 (months) by 100 (quantiles) array of adjustment factors.
  Linear or cubic interpolation / smoothing of the adjustment factors can be optionally applied along the time (e.g. month) axis.
  For example, the adjustment factor for a observational data point from 29 July that corresponds to the 0.651 quantile
  could be a linear combination of the adjustment factors for the nearest quantile (0.65) from both July and August.
  We've found that linear and cubic interpolation along the time axis produce slighty better results
  than no smoothing at all but can be more computationally expensive.
- *Singularity stochastic removal* ([Vrac et al 2016](https://doi.org/10.1002/2015JD024511))
  is used to avoid divide by zero errors in the analysis of precipitation data.
  All near-zero values (i.e. values less than a very small positive threshold value)
  are set to a small random non-zero value prior to data processing,
  and then after QDC has been applied
  any values less than the threshold are set to zero.
   
