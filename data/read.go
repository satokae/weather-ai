package data

import (
	"encoding/csv"
	"io"
	"log"
	"os"
	"strconv"

	"golang.org/x/text/encoding/japanese"
	"golang.org/x/text/transform"
)

const ignoreLines = 4

func read(path string) []*WeatherRecord {
	file, err := os.Open(path)
	if err != nil {
		log.Fatal(err)
	}
	defer file.Close()

	reader := csv.NewReader(transform.NewReader(file, japanese.ShiftJIS.NewDecoder()))
	reader.FieldsPerRecord = 10

	for i := 0; i < ignoreLines; i++ {
		_, _ = reader.Read()
	}

	output := make([]*WeatherRecord, 0)

	for {
		record, err := reader.Read()

		if err == io.EOF {
			break
		} else if err != nil {
			continue
		}

		year, err := strconv.Atoi(record[0])
		if err != nil {
			continue
		}
		month, err := strconv.Atoi(record[1])
		if err != nil {
			continue
		}
		day, err := strconv.Atoi(record[2])
		if err != nil {
			continue
		}
		hour, err := strconv.Atoi(record[3])
		if err != nil {
			continue
		}
		dewPoint, err := strconv.ParseFloat(record[4], 64)
		if err != nil {
			continue
		}
		weatherCode, err := strconv.Atoi(record[5])
		if err != nil {
			continue
		}
		weather := ParseWeather(weatherCode)
		if weather == WeatherOther {
			continue
		}
		temperature, err := strconv.ParseFloat(record[6], 64)
		if err != nil {
			continue
		}
		windSpeed, err := strconv.ParseFloat(record[7], 64)
		if err != nil {
			continue
		}
		windDirection := ParseWindDirection(record[8])
		if windDirection == DirUnknown {
			continue
		}
		pressure, err := strconv.ParseFloat(record[9], 64)
		if err != nil {
			continue
		}

		output = append(output, &WeatherRecord{
			Year:          year,
			Month:         month,
			Day:           day,
			Hour:          hour,
			DewPoint:      dewPoint,
			WeatherCode:   weatherCode,
			Temperature:   temperature,
			WindSpeed:     windSpeed,
			WindDirection: windDirection,
			Pressure:      pressure,
		})
	}

	return output
}
