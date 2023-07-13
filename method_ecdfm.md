# Equi-distant/ratio CDF matching (ECDFm)

## Overview

The first step in any bias correction prodcedure involves establishing a statistical relationship or transfer function
between model outputs and observations over a reference (i.e. historical/training) time period.
The established transfer function is then applied to the target model data (e.g. future model projections)
in order to produce a "bias corrected" model time series.

Many bias correction procedures are quantile based,
meaning the model data are corrected on a quantile by quantile basis.
In *equidistant cumulative density function matching* (ECDFm; [Li et al, 2010](https://doi.org/10.1029/2009JD012882)),
the transfer function represents the distance (i.e. arithmetic difference)
between the observations and model for each quantile of the training period.
Those differences are then added to the target model data
according to the quantile each target data point represents over the target period.
For instance, if a target temperature of $25^{\circ}$ Celsius corresponds to the 0.5 quantile (i.e. the median) in the target data,
the difference between the median value in the observations and reference model data
is added to the target value in order to obtain the bias adjusted value.
The underlying assumption is that the distance between the model and observed quantiles during the training period
also applies to the target period, hence the name *equidistant*.
The reference to *CDF matching* is clear from the mathematical representation of the method:
$$x_{m-adjust} = x_{m,p} + F_{o,h}^{-1}(F_{m,p}(x_{m,p})) - F_{m,h}^{-1}(F_{m,p}(x_{m,p}))$$

where $F$ is the CDF of either the observations ($o$) or model ($m$) for a historic training period ($h$) or target period ($p$).
That means $F_{o,h}^{-1}$ and $F_{m,h}^{-1}$ are the quantile functions (inverse CDF) corresponding to the observations and model respectively.
Returning to our target median value of $25^{\circ}$ (i.e. $x_{m,p} = 25$),
the corresponding CDF would return a value of 0.5 (i.e. $F_{m,p}(25) = 0.5$).
The difference between the observed ( $F_{o,h}^{-1}(0.5)$ ) and reference model ( $F_{m,h}^{-1}(0.5)$ )
median values would then be added to the target value of $25^{\circ}$ to get a bias corrected value.

For variables like precipitation, multiplicative as opposed to additive bias correction is preferred
to avoid the possibility of getting bias corrected values less than zero.
In this case, *equiratio CDF matching* (EQCDFm; [Wang and Chen, 2013](https://doi.org/10.1002/asl2.454))
is used:

$$x_{m-adjust} = x_{m,p} \times (F_{o,h}^{-1}(F_{m,p}(x_{m,p})) \div F_{m,h}^{-1}(F_{m,p}(x_{m,p})))$$

## Methododological decisions

There are a number of choices to make when applying EDCDFm or EQCDFm: 
- *Parametric or non-parametric*:
  It is generally accepted that non-parametric quantile mapping is best for bias correction,
  so ECDFm is usually applied without fitting a parametric distribution to the data first.
  Our qqscale software takes a non-parametric / empirical approach.
- *Downscaling (when and how)*:
  Model data is usually on a coarser spatial grid than observations.
  Some authors downscale the model data first
  (via simple spatial interpolation, statistical downscaling or dynamical downscaling)
  and then perform bias correction.
  Others upscale the observations,
  perform the bias correction on the model grid
  and then downscale the bias corrected model data.
  Our qqscale software does the former and downscales the model data first using bilinear interpolation.
- *Qunatiles (number and interpolation)*:
  Our qqscale software allows the user to specify
  the number of quantiles to calculate and
  what interpolation method to use to determine the bias correction
  for target data points that fall between two quantiles.
  The software default is 100 quantiles and nearest neighbour interpolation.
  We've found that linear and cubic interpolation (the other options)
  is much more computationally expensive and produces very similar results to nearest neighbour.
- *Time grouping*:
  It is common to bias correct individual seasons or months separately
  to avoid conflating different times of the year
  (e.g. spring and autumn temperatures often occupy the same annual quantile space
  but may be biased in different ways).
  The qqscale software allows the user to specify what type of time grouping to apply.
  We commonly use monthly time grouping for EDCDFm and EQCDFm (i.e. process each month separately).
  We've found that something like a 30-day running window is far more computationally expensive
  and produces similar results to monthly grouping.
