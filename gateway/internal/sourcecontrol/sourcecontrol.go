package sourcecontrol

import (
	"fmt"
	"net"
	"time"

	smartpb "github.com/cbysousa/distributed-systems/internal/proto"
	"github.com/cbysousa/distributed-systems/internal/state"
	"github.com/cbysousa/distributed-systems/internal/tcpmessage"
	"google.golang.org/protobuf/proto"
)

type Result struct {
	Success bool
	Message string
	Status  string
}

func SendCommand(source state.Source, request *smartpb.SendCommandRequest) (Result, error) {
	if request == nil || request.Lamppost == nil || request.Lamppost.Command == nil {
		return Result{}, fmt.Errorf("missing lamppost command")
	}

	cfg := DefaultConfig()
	conn, err := net.DialTimeout(
		"tcp",
		source.Address,
		time.Duration(cfg.ConnectTimeoutSeconds)*time.Second,
	)
	if err != nil {
		return Result{}, err
	}
	defer conn.Close()

	deadline := time.Now().Add(time.Duration(cfg.RequestTimeoutSeconds) * time.Second)
	if err := conn.SetDeadline(deadline); err != nil {
		return Result{}, err
	}

	return sendLamppostCommand(conn, request.Lamppost)
}

func sendLamppostCommand(conn net.Conn, command *smartpb.LamppostCommand) (Result, error) {
	data, err := proto.Marshal(command)
	if err != nil {
		return Result{}, err
	}

	if err := tcpmessage.Write(conn, data); err != nil {
		return Result{}, err
	}

	responseData, err := tcpmessage.Read(conn)
	if err != nil {
		return Result{}, err
	}

	response := &smartpb.LamppostResponse{}
	if err := proto.Unmarshal(responseData, response); err != nil {
		return Result{}, err
	}

	return Result{
		Success: response.Success,
		Message: response.Message,
		Status:  lamppostStatus(command, response),
	}, nil
}

func lamppostStatus(command *smartpb.LamppostCommand, response *smartpb.LamppostResponse) string {
	if !response.Success {
		return ""
	}

	switch command.Command.(type) {
	case *smartpb.LamppostCommand_TurnOn:
		return state.StatusActive
	case *smartpb.LamppostCommand_TurnOff, *smartpb.LamppostCommand_SimulateFailure:
		return state.StatusOffline
	}

	if response.Status != "" {
		return state.NormalizeStatus(response.Status)
	}

	if response.Active {
		return state.StatusActive
	}

	return state.StatusOffline
}
