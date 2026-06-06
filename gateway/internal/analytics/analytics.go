package analytics

import (
	"fmt"
	"math"
	"time"

	"github.com/cbysousa/distributed-systems/internal/state"
)

type Operation string

const (
	OperationAVG    Operation = "AVG"
	OperationSTDDEV Operation = "STDDEV"
	OperationMIN    Operation = "MIN"
	OperationMAX    Operation = "MAX"
)

type Query struct {
	Metric        string
	Operation     Operation
	WindowSeconds int64
}

type Result struct {
	Metric        string
	Operation     Operation
	Value         float64
	SampleCount   int
	WindowSeconds int64
}

func Run(readings []state.Reading, query Query) (Result, error) {
	values := filterValues(readings, query)
	if len(values) == 0 {
		return Result{}, fmt.Errorf("no readings found for metric %s", query.Metric)
	}

	value, err := calculate(values, query.Operation)
	if err != nil {
		return Result{}, err
	}

	return Result{
		Metric:        query.Metric,
		Operation:     query.Operation,
		Value:         value,
		SampleCount:   len(values),
		WindowSeconds: query.WindowSeconds,
	}, nil
}

func filterValues(readings []state.Reading, query Query) []float64 {
	values := make([]float64, 0)
	cutoff := time.Time{}

	if query.WindowSeconds > 0 {
		cutoff = time.Now().Add(-time.Duration(query.WindowSeconds) * time.Second)
	}

	for _, reading := range readings {
		if reading.Metric != query.Metric {
			continue
		}

		if !cutoff.IsZero() && reading.Timestamp.Before(cutoff) {
			continue
		}

		values = append(values, reading.Value)
	}

	return values
}

func calculate(values []float64, operation Operation) (float64, error) {
	switch operation {
	case OperationAVG:
		return average(values), nil
	case OperationSTDDEV:
		return standardDeviation(values), nil
	case OperationMIN:
		return min(values), nil
	case OperationMAX:
		return max(values), nil
	default:
		return 0, fmt.Errorf("unknown aggregate operation %s", operation)
	}
}

func average(values []float64) float64 {
	sum := 0.0
	for _, value := range values {
		sum += value
	}

	return sum / float64(len(values))
}

func standardDeviation(values []float64) float64 {
	avg := average(values)
	sum := 0.0

	for _, value := range values {
		diff := value - avg
		sum += diff * diff
	}

	return math.Sqrt(sum / float64(len(values)))
}

func min(values []float64) float64 {
	result := values[0]
	for _, value := range values[1:] {
		if value < result {
			result = value
		}
	}

	return result
}

func max(values []float64) float64 {
	result := values[0]
	for _, value := range values[1:] {
		if value > result {
			result = value
		}
	}

	return result
}
