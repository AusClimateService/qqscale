# Quantile Delta Mapping (QDM)

## Overview

One of the most widely used methods for producing climate projection data is the so-called "delta change" approach.
Rather than use the data from a model simulation of the future climate directly,
the delta change approach calculates the relative change between a future and historical modelled time period.
That relative change is then applied to observed data from the same historical time period
in order to produce an "application ready" time series for the future period.

While the simplest application of the delta change approach is to apply the mean model change to the observed data,
a popular alternative is to calculate and apply the delta changes on a quantile by quantile basis.
For instance, if an observed historical temperature of $25^{\circ}$ Celsius corresponds to the 0.5 quantile (i.e. the median) in the observed data,
the difference between the median value in the future and historical model data
is added to that observed historical temperature in order to obtain the projected future temperature.

This method is known as Quantile Delta Mapping (QDM; [Cannon et al 2015](https://doi.org/10.1175/JCLI-D-14-00754.1))
and is expressed mathematically as follows:

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


## Methodological decisions

There are a number of choices to make when applying QDM: 
- *Parametric or non-parametric*:
  It is generally accepted that non-parametric quantile mapping is best,
  so QDM is usually applied without fitting a parametric distribution to the data first.
  Our qqscale software takes a non-parametric / empirical approach.
- *Downscaling (when and how)*:
  TODO
- *Qunatiles (number and interpolation)*:
  Our qqscale software allows the user to specify
  the number of quantiles to calculate and
  what interpolation method to use to determine the adjustment factor
  for target data points that fall between two quantiles.
  The software default is 100 quantiles and nearest neighbour interpolation.
  We've found that linear and cubic interpolation (the other options)
  is much more computationally expensive and produces very similar results to nearest neighbour.
- *Time grouping*:
  It is common to bias correct individual seasons or months separately
  to avoid conflating different times of the year
  (e.g. spring and autumn temperatures often occupy the same annual quantile space
  but may be biased in different ways)... TODO
