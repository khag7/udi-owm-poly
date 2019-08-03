## Configuration

The OpenWeatherMap node server has the following user configuration
parameters:

- APIkey   : Your API ID, needed to authorize connection to the OpenWeatherMap API.

- Units    : 'metric' or 'imperial' request data in this units format.

- Location : 
    - by zip code (zip=xxxxxxx[,country code])
    - by city name (q=city name[,country code])
    - by city id (id=city id)
    - by coordinates (lat=xx&lon=xxx)

- Elevation : Height above sea level, in meters, for the location specified above. 

- Plant Type : Crop coefficent for evapotranspiration calculation. Default is 0.23

