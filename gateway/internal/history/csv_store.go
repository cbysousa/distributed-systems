package history

import (
	"encoding/csv"
	"errors"
	"io"
	"os"
	"path/filepath"
	"strconv"
	"sync"
	"time"

	"github.com/cbysousa/distributed-systems/internal/state"
)

const defaultCSVPath = "/app/data/readings.csv"

var csvHeader = []string{
	"timestamp_unix_ms",
	"source_name",
	"source_type",
	"metric",
	"value",
	"unit",
}

type CSVStore struct {
	path  string
	mutex sync.Mutex
}

func DefaultCSVPath() string {
	path := os.Getenv("HISTORY_CSV_PATH")
	if path == "" {
		return defaultCSVPath
	}

	return path
}

func NewCSVStore(path string) (*CSVStore, error) {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return nil, err
	}

	store := &CSVStore{path: path}
	return store, store.ensureHeader()
}

func (s *CSVStore) LoadReadings() ([]state.Reading, error) {
	file, err := os.Open(s.path)
	if errors.Is(err, os.ErrNotExist) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	defer file.Close()

	reader := csv.NewReader(file)
	records, err := reader.ReadAll()
	if err != nil {
		return nil, err
	}

	readings := make([]state.Reading, 0, len(records))
	for index, record := range records {
		if index == 0 && isHeader(record) {
			continue
		}

		reading, err := recordToReading(record)
		if err != nil {
			continue
		}

		readings = append(readings, reading)
	}

	return readings, nil
}

func (s *CSVStore) AppendReadings(readings []state.Reading) error {
	if len(readings) == 0 {
		return nil
	}

	s.mutex.Lock()
	defer s.mutex.Unlock()

	file, err := os.OpenFile(s.path, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		return err
	}
	defer file.Close()

	writer := csv.NewWriter(file)
	for _, reading := range readings {
		if err := writer.Write(readingToRecord(reading)); err != nil {
			return err
		}
	}

	writer.Flush()
	return writer.Error()
}

func (s *CSVStore) ensureHeader() error {
	file, err := os.OpenFile(s.path, os.O_CREATE|os.O_RDWR, 0o644)
	if err != nil {
		return err
	}
	defer file.Close()

	info, err := file.Stat()
	if err != nil {
		return err
	}

	if info.Size() > 0 {
		return nil
	}

	writer := csv.NewWriter(file)
	if err := writer.Write(csvHeader); err != nil {
		return err
	}

	writer.Flush()
	return writer.Error()
}

func recordToReading(record []string) (state.Reading, error) {
	if len(record) != len(csvHeader) {
		return state.Reading{}, io.ErrUnexpectedEOF
	}

	timestampUnixMs, err := strconv.ParseInt(record[0], 10, 64)
	if err != nil {
		return state.Reading{}, err
	}

	value, err := strconv.ParseFloat(record[4], 64)
	if err != nil {
		return state.Reading{}, err
	}

	return state.Reading{
		Timestamp:  time.UnixMilli(timestampUnixMs),
		SourceName: record[1],
		SourceType: record[2],
		Metric:     record[3],
		Value:      value,
		Unit:       record[5],
	}, nil
}

func readingToRecord(reading state.Reading) []string {
	return []string{
		strconv.FormatInt(reading.Timestamp.UnixMilli(), 10),
		reading.SourceName,
		reading.SourceType,
		reading.Metric,
		strconv.FormatFloat(reading.Value, 'f', -1, 64),
		reading.Unit,
	}
}

func isHeader(record []string) bool {
	if len(record) != len(csvHeader) {
		return false
	}

	for index, value := range record {
		if value != csvHeader[index] {
			return false
		}
	}

	return true
}
