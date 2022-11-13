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
