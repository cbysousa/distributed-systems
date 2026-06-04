package readings

import (
	"time"

	smartpb "github.com/cbysousa/distributed-systems/internal/proto"
	"github.com/cbysousa/distributed-systems/internal/state"
)

func packetToReadings(packet *smartpb.ReadingPacket) []state.Reading {
	timestamp := time.Now()
	if packet.TimestampUnixMs > 0 {
		timestamp = time.UnixMilli(packet.TimestampUnixMs)
	}

	switch reading := packet.Reading.(type) {
	case *smartpb.ReadingPacket_Temperature:
		return temperatureToReadings(packet.SourceName, timestamp, reading.Temperature)
	case *smartpb.ReadingPacket_AirQuality:
		return airQualityToReadings(packet.SourceName, timestamp, reading.AirQuality)
	default:
		return nil
	}
}

func temperatureToReadings(sourceName string, timestamp time.Time, reading *smartpb.TemperatureReading) []state.Reading {
	return []state.Reading{
		{
			SourceName: sourceName,
			SourceType: "temperature",
			Metric:     "temperature_celsius",
			Value:      reading.TemperatureCelsius,
			Unit:       "celsius",
			Timestamp:  timestamp,
		},
		{
			SourceName: sourceName,
			SourceType: "temperature",
			Metric:     "humidity_percent",
			Value:      reading.HumidityPercent,
			Unit:       "percent",
			Timestamp:  timestamp,
		},
	}
}

func airQualityToReadings(sourceName string, timestamp time.Time, reading *smartpb.AirQualityReading) []state.Reading {
	return []state.Reading{
		{
			SourceName: sourceName,
			SourceType: "air_quality",
			Metric:     "co2_ppm",
			Value:      reading.Co2Ppm,
			Unit:       "ppm",
			Timestamp:  timestamp,
		},
		{
			SourceName: sourceName,
			SourceType: "air_quality",
			Metric:     "particulate_matter_ug_m3",
			Value:      reading.ParticulateMatterUgM3,
			Unit:       "ug/m3",
			Timestamp:  timestamp,
		},
		{
			SourceName: sourceName,
			SourceType: "air_quality",
			Metric:     "air_quality_index",
			Value:      reading.AirQualityIndex,
			Unit:       "aqi",
			Timestamp:  timestamp,
		},
	}
}
