package sourcecontrol

type Config struct {
	ConnectTimeoutSeconds int
	RequestTimeoutSeconds int
}

func DefaultConfig() Config {
	return Config{
		ConnectTimeoutSeconds: 3,
		RequestTimeoutSeconds: 5,
	}
}
