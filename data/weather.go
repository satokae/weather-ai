package data

//go:generate stringer -type=Weather -trimprefix=Weather
type Weather int

const (
	WeatherSunny Weather = iota
	WeatherCloudy
	WeatherRainy
	WeatherOther
)

func ParseWeather(i int) Weather {
	switch i {
	case 2:
		return WeatherSunny
	case 4:
		return WeatherCloudy
	case 10:
		return WeatherRainy
	default:
		return WeatherOther
	}
}
