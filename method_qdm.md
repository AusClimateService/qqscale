# Quantile Delta Mapping (QDM)

## Overview

The most simple approach used for producing "application ready data" is the delta change approach... TODO

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
