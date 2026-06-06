package clientserver

import (
	smartpb "github.com/cbysousa/distributed-systems/internal/proto"
	"github.com/cbysousa/distributed-systems/internal/state"
)

func sourceToProto(source state.Source) *smartpb.SourceInfo {
	return &smartpb.SourceInfo{
		Name:           source.Name,
		SourceType:     source.Type,
		Address:        source.Address,
		Ip:             source.IP,
		Port:           int32(source.Port),
		Controllable:   source.Controllable,
		Status:         source.Status,
		LastSeenUnixMs: source.LastSeen.UnixMilli(),
	}
}

func readingToProto(reading state.Reading) *smartpb.ReadingInfo {
	return &smartpb.ReadingInfo{
		SourceName:      reading.SourceName,
		SourceType:      reading.SourceType,
		Metric:          reading.Metric,
		Value:           reading.Value,
		Unit:            reading.Unit,
		TimestampUnixMs: reading.Timestamp.UnixMilli(),
	}
}
