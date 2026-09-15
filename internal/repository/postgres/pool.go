package postgres

import (
	"context"
	"fmt"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

// NewPoolConfig parses the DSN and applies production-grade connection pool settings
// per sqlc-pgx-expert standards: MaxConns=25, MinConns=5, MaxConnLifetime=1h, MaxConnIdleTime=30m.
func NewPoolConfig(dsn string) (*pgxpool.Config, error) {
	config, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		return nil, fmt.Errorf("failed to parse dsn: %w", err)
	}

	config.MaxConns = 25
	config.MinConns = 5
	config.MaxConnLifetime = 1 * time.Hour
	config.MaxConnIdleTime = 30 * time.Minute

	return config, nil
}

// NewPool initializes and validates a pgxpool.Pool instance with standard pool configuration.
func NewPool(ctx context.Context, dsn string) (*pgxpool.Pool, error) {
	config, err := NewPoolConfig(dsn)
	if err != nil {
		return nil, err
	}

	pool, err := pgxpool.NewWithConfig(ctx, config)
	if err != nil {
		return nil, fmt.Errorf("failed to create connection pool: %w", err)
	}

	if err := pool.Ping(ctx); err != nil {
		pool.Close()
		return nil, fmt.Errorf("failed to ping db: %w", err)
	}

	return pool, nil
}
