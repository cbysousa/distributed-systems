package tcpmessage

import (
	"encoding/binary"
	"fmt"
	"io"
	"net"
)

const maxMessageSize = 10 * 1024 * 1024

func Read(conn net.Conn) ([]byte, error) {
	header := make([]byte, 4)
	if _, err := io.ReadFull(conn, header); err != nil {
		return nil, err
	}

	messageSize := binary.BigEndian.Uint32(header)
	if messageSize > maxMessageSize {
		return nil, fmt.Errorf("message too large: %d bytes", messageSize)
	}

	message := make([]byte, messageSize)
	if _, err := io.ReadFull(conn, message); err != nil {
		return nil, err
	}

	return message, nil
}

func Write(conn net.Conn, data []byte) error {
	if len(data) > maxMessageSize {
		return fmt.Errorf("message too large: %d bytes", len(data))
	}

	header := make([]byte, 4)
	binary.BigEndian.PutUint32(header, uint32(len(data)))

	if err := writeAll(conn, header); err != nil {
		return err
	}

	return writeAll(conn, data)
}

func writeAll(conn net.Conn, data []byte) error {
	for len(data) > 0 {
		n, err := conn.Write(data)
		if err != nil {
			return err
		}

		data = data[n:]
	}

	return nil
}
