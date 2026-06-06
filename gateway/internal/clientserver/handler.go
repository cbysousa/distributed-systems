package clientserver

import (
	smartpb "github.com/cbysousa/distributed-systems/internal/proto"
	"github.com/cbysousa/distributed-systems/internal/sourcecontrol"
	"github.com/cbysousa/distributed-systems/internal/state"
)

func handleRequest(request *smartpb.ClientRequest, gatewayState *state.GatewayState) *smartpb.ClientResponse {
	switch req := request.Request.(type) {
	case *smartpb.ClientRequest_ListSources:
		return handleListSources(req.ListSources, gatewayState)
	case *smartpb.ClientRequest_ListReadings:
		return handleListReadings(req.ListReadings, gatewayState)
	case *smartpb.ClientRequest_SendCommand:
		return handleSendCommand(req.SendCommand, gatewayState)
	default:
		return errorResponse("unknown request")
	}
}

func handleListSources(_ *smartpb.ListSourcesRequest, gatewayState *state.GatewayState) *smartpb.ClientResponse {
	sources := gatewayState.ListSources()
	protoSources := make([]*smartpb.SourceInfo, 0, len(sources))

	for _, source := range sources {
		protoSources = append(protoSources, sourceToProto(source))
	}

	return &smartpb.ClientResponse{
		Success: true,
		Message: "sources listed successfully",
		Response: &smartpb.ClientResponse_ListSources{
			ListSources: &smartpb.ListSourcesResponse{
				Sources: protoSources,
			},
		},
	}
}

func handleListReadings(request *smartpb.ListReadingsRequest, gatewayState *state.GatewayState) *smartpb.ClientResponse {
	var readings []state.Reading
	if request.Metric == "" {
		readings = gatewayState.ListReadings()
	} else {
		readings = gatewayState.ListReadingsByMetric(request.Metric)
	}

	protoReadings := make([]*smartpb.ReadingInfo, 0, len(readings))
	for _, reading := range readings {
		protoReadings = append(protoReadings, readingToProto(reading))
	}

	return &smartpb.ClientResponse{
		Success: true,
		Message: "readings listed successfully",
		Response: &smartpb.ClientResponse_ListReadings{
			ListReadings: &smartpb.ListReadingsResponse{
				Readings: protoReadings,
			},
		},
	}
}

func errorResponse(message string) *smartpb.ClientResponse {
	return &smartpb.ClientResponse{
		Success: false,
		Message: message,
	}
}

func handleSendCommand(request *smartpb.SendCommandRequest, gatewayState *state.GatewayState) *smartpb.ClientResponse {
	if request == nil || request.Lamppost == nil || request.Lamppost.Command == nil {
		return sendCommandResponse(false, "missing lamppost command", "")
	}

	source, exists := gatewayState.GetSource(request.SourceName)
	if !exists {
		return sendCommandResponse(false, "source not found", "")
	}

	if !source.Controllable {
		return sendCommandResponse(false, "source is not controllable", source.Status)
	}

	result, err := sourcecontrol.SendCommand(source, request)
	if err != nil {
		gatewayState.UpdateStatus(source.Name, state.StatusOffline)
		return sendCommandResponse(false, err.Error(), state.StatusOffline)
	}

	if result.Status != "" {
		gatewayState.UpdateStatus(source.Name, result.Status)
	}

	return sendCommandResponse(result.Success, result.Message, result.Status)
}

func sendCommandResponse(success bool, message string, sourceStatus string) *smartpb.ClientResponse {
	return &smartpb.ClientResponse{
		Success: success,
		Message: message,
		Response: &smartpb.ClientResponse_SendCommand{
			SendCommand: &smartpb.SendCommandResponse{
				Success:      success,
				Message:      message,
				SourceStatus: sourceStatus,
			},
		},
	}
}
