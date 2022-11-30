"""A collection of standard file and dimension attributes."""

lat_dim = {
    "standard_name": "latitude",
    "long_name" : "Latitude",
    "units": "degrees_north",
    "axis": "Y",
}
    
lon_dim = {
    "standard_name": "longitude",
    "long_name" : "Longitude",
    "units": "degrees_east",
    "axis": "X",
}

time_dim = {
    "standard_name": "time",
    "long_name" : "time",
    "units": "days",
    "Calendar":"standard"
    "axis:" "T",
}

data_month_dim = {
    "standard_name": "time",
    "long_name" : "time",
    "units": "days",
    "cell methods":"mean",
}

global_atts = {
#    "author:"
#    "version:"
#    "Owner:"
#    "funding source:"
#    "License:"
#    "UUID:"
#    "Citation data:"
#    "Citation paper:"
#    "Creation date:"
#    "Peer review:"
#    "Repository URL:"
#    "Author organisation:"
#    "author_organisation_email:"
#    "Description:"
    "Conventions": "CF-1.7",
    "title": "Quantile-Quantile scaling",
    "institution": "CSIRO",
    "contact": "raktima.dey@csiro.au",
}
 