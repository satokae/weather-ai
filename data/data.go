package data

import "path/filepath"

var (
	Data2023 = read(filepath.Join("data", "2023.csv"))
	Data2024 = read(filepath.Join("data", "2024.csv"))
	Data2025 = read(filepath.Join("data", "2025.csv"))
)

type WeatherRecord struct {
	Year          int
	Month         int
	Day           int
	Hour          int
	DewPoint      float64
	WeatherCode   int
	Temperature   float64
	WindSpeed     float64
	WindDirection Direction
	Pressure      float64
}

func (w *WeatherRecord) WindComplex() complex128 {
	return w.WindDirection.WindComplex(w.WindSpeed)
}
