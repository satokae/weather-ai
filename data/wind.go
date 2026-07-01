package data

import (
	"math"
)

//go:generate stringer -type=Direction -trimprefix=Dir
type Direction int

const (
	DirN Direction = iota
	DirNNE
	DirNE
	DirENE
	DirE
	DirESE
	DirSE
	DirSSE
	DirS
	DirSSW
	DirSW
	DirWSW
	DirW
	DirWNW
	DirNW
	DirNNW
	DirCalm
	DirUnknown
)

func ParseWindDirection(s string) Direction {
	switch s {
	case "北":
		return DirN
	case "北北東":
		return DirNNE
	case "北東":
		return DirNE
	case "東北東":
		return DirENE
	case "東":
		return DirE
	case "東南東":
		return DirESE
	case "南東":
		return DirSE
	case "南南東":
		return DirSSE
	case "南":
		return DirS
	case "南南西":
		return DirSSW
	case "南西":
		return DirSW
	case "西南西":
		return DirWSW
	case "西":
		return DirW
	case "西北西":
		return DirWNW
	case "北西":
		return DirNW
	case "北北西":
		return DirNNW
	case "静穏":
		return DirCalm
	default:
		return DirUnknown
	}
}

func (d Direction) Angle() (float64, bool) {
	if DirCalm <= d {
		return 0, false
	}

	return float64(d) * 22.5, true
}

func (d Direction) WindComplex(windSpeed float64) complex128 {
	angle, ok := d.Angle()
	if !ok {
		return 0
	}

	rad := angle * math.Pi / 180.0

	x := windSpeed * math.Sin(rad)
	y := windSpeed * math.Cos(rad)

	return complex(x, y)
}
