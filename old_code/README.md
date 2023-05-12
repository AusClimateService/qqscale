## QQ-scaling at CSIRO

This directory contains previous versions of qq-scaling code used at CSIRO.
Here's the relevant history:

1. Kim and Craig developed an original version of the quantile scaling code for the NRM project.
   It implemented a decile scaling approach with individual percentiles included for the top 90th up and bottom less than 10th percentiles.
   This was used to create the application ready rainfall data that is available through Climate Change in Australia.
   It used a combination of shell scripting, ferret, cdo and fortran code.
   Overall it worked well, but the authors identified some things where the performance wasn’t quite as good as they'd hoped for (e.g. seasonal average change).
   The code for this original version isn't inlcuded in this repository.

2. Marcus and Craig developed a completely new fortran code version for the VCP19 (DELWP) project work (see `fortran/`).
   This had some subtle changes in the approach to see their “hunch” about why it behaved in a certain way could be improved.
   It added completely individual percentile binning (100 of them)
   with interpolation for change values depending on where the individual daily values fell in-between percentile bins.
   This improved the average seasonal change performance as predicted.

3. The Climate Innovation Hub came into being and Raktima and Vassili started writing a python version (see `python/`).
   It implements the same improved method as the previous fortran method that Marcus and Craig developed. 

These methods are documented on the [CCiA website](https://www.climatechangeinaustralia.gov.au/en/obtain-data/application-ready-data/scaling-methods/)
and also in a [CAWCR Technical Report](http://www.bom.gov.au/research/publications/cawcrreports/CTR_034.pdf).

A Climate Innovation Hub technical report describes the methodology used in the Python version as follows:

> Firstly, for each of the model simulated baseline and future periods,
> for each month of the year,
> all daily data are ranked from highest to lowest,
> and then divided equally into 100 bins or “quantiles”.
> The first quantile contains the first 1% of data values,
> the second quantile contains the next 1% of data values and so forth.
> A change factor is then calculated as the difference between the mean of the historical and future data for each quantile. 
>
> Then, the equivalent quantiles are calculated using relevant observed (AGCD v1 or ERA5) data
> (for each month under consideration) over the historical baseline period,
> and each daily value is assigned to a quantile.
> Then, the change factor for a given quantile is applied to the corresponding observed daily value
> for that quantile to produce a future daily value.
> For example, if the change factor for the 70th quantile of daily precipitation is +10%,
> and the observed daily precipitation value for the 70th quantile is 50mm,
> then the future daily value becomes 55mm.
> Since change factors can vary between month,
> the seasonal variability in simulated future climate changes is incorporated into the QQ-scaled data. 
>
> Finally, some adjustments are applied to the QQ-scaled data
> to ensure consistency with the GCM-simulated changes in average climate conditions
> and to ensure that values are physically plausible.
> Firstly, the QQ scaled data are adjusted so that the change in monthly mean
> between observations and QQ-scaled data matches the model simulated change in monthly mean.
> For example, if QQ scaling produces a mean change of +15% for a given month,
> but the climate model simulates a mean change of +18%,
> then all daily values are adjusted upward by an extra 3%.
> Finally, for solar radiation and relative humidity a ‘cap’ or upper limit to the data
> is introduced at this stage to ensure that solar radiation does not exceed the maximum possible
> (i.e., clear-sky solar radiation) and that relative humidity does not exceed 100%. 

The only thing this description doesn't mention is the interpolation of change values
depending on where the individual daily values fell in-between percentile bins.
