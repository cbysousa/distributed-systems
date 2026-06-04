package sourcecontrol

import (
	"fmt"
	"net"

	smartpb "github.com/cbysousa/distributed-systems/internal/proto"
	"github.com/cbysousa/distributed-systems/internal/state"
	"github.com/cbysousa/distributed-systems/internal/tcpmessage"
	"google.golang.org/protobuf/proto"
)

const (
	StatusActive   = "ACTIVE"
	StatusInactive = "INACTIVE"
	StatusFailed   = "FAILED"
)

type Result struct {
	Success bool
	Message string
	Status  string
}

func SendCommand(source state.Source, request *smartpb.SendCommandRequest) (Result, error) {
	if request == nil || request.Command == nil {
		return Result{}, fmt.Errorf("missing source command")
	}

	conn, err := net.Dial("tcp", source.Address)
	if err != nil {
		return Result{}, err
	}
	defer conn.Close()

	switch command := request.Command.(type) {
	case *smartpb.SendCommandRequest_Cam:
		return sendCamCommand(conn, command.Cam)
	case *smartpb.SendCommandRequest_Lamppost:
		return sendLamppostCommand(conn, command.Lamppost)
	case *smartpb.SendCommandRequest_Semaphore:
		return sendSemaphoreCommand(conn, command.Semaphore)
	default:
		return Result{}, fmt.Errorf("unknown source command")
	}
}

func sendCamCommand(conn net.Conn, command *smartpb.CamCommand) (Result, error) {
	if command == nil || command.Command == nil {
		return Result{}, fmt.Errorf("missing cam command")
	}

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

	response := &smartpb.CamResponse{}
	if err := proto.Unmarshal(responseData, response); err != nil {
		return Result{}, err
	}

	return Result{
		Success: response.Success,
		Message: response.Message,
		Status:  camStatus(command, response),
	}, nil
}

func sendLamppostCommand(conn net.Conn, command *smartpb.LamppostCommand) (Result, error) {
	if command == nil || command.Command == nil {
		return Result{}, fmt.Errorf("missing lamppost command")
	}

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

func sendSemaphoreCommand(conn net.Conn, command *smartpb.SemaphoreCommand) (Result, error) {
	if command == nil || command.Command == nil {
		return Result{}, fmt.Errorf("missing semaphore command")
	}

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

	response := &smartpb.SemaphoreResponse{}
	if err := proto.Unmarshal(responseData, response); err != nil {
		return Result{}, err
	}

	return Result{
		Success: response.Success,
		Message: response.Message,
		Status:  semaphoreStatus(command, response),
	}, nil
}

func camStatus(command *smartpb.CamCommand, response *smartpb.CamResponse) string {
	if response.Status != "" {
		return response.Status
	}

	if !response.Success {
		return ""
	}

	if _, failed := command.Command.(*smartpb.CamCommand_SimulateFailure); failed {
		return StatusFailed
	}

	if response.Active {
		return StatusActive
	}

	return StatusInactive
}

func lamppostStatus(command *smartpb.LamppostCommand, response *smartpb.LamppostResponse) string {
	if response.Status != "" {
		return response.Status
	}

	if !response.Success {
		return ""
	}

	if _, failed := command.Command.(*smartpb.LamppostCommand_SimulateFailure); failed {
		return StatusFailed
	}

	if response.Active {
		return StatusActive
	}

	return StatusInactive
}

func semaphoreStatus(command *smartpb.SemaphoreCommand, response *smartpb.SemaphoreResponse) string {
	if response.Status != "" {
		return response.Status
	}

	if !response.Success {
		return ""
	}

	if _, failed := command.Command.(*smartpb.SemaphoreCommand_SimulateFailure); failed {
		return StatusFailed
	}

	return StatusActive
}
