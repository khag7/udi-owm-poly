## Configuration

The OpenWeatherMap node server has the following user configuration
parameters:

- APIkey   : Your API ID, needed to authorize connection to the OpenWeatherMap API.

- Units    : 'metric' or 'imperial' request data in this units format.

- Location : Zip code for location (zip=xxxxxx,us)
  Other options to add later:
    by city name (q=city name[,country])
    by city id (id=city id)
    by coordinates (lat=xx&lon=xxx)

- Elevation : Height above sea level, in meters, for the location specified above. 

- Plant Type : Crop coefficent for evapotranspiration calculation. Default is 0.23

