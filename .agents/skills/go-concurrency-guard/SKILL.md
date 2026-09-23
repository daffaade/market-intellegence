---
name: go-concurrency-guard
description: Use when writing, reviewing, or debugging concurrent Go code, goroutines, channels, sync primitives, worker pools, background tasks, or context cancellation
---

# Go Concurrency Guard

## Overview
Writing concurrent Go code requires strict lifecycle control, synchronization correctness, and memory safety. A single uncoordinated goroutine can leak memory, block forever, or corrupt shared memory states.

```
       +---------------------------------------------+
       |           The Cardinal Rule                 |
       |  NEVER start a goroutine without knowing    |
       |  EXACTLY how and when it will terminate.    |
       +---------------------------------------------+
```

---

## Concurrency Invariants

1. **Context First**: Always pass `ctx context.Context` as the first argument to concurrent jobs and check `<-ctx.Done()` in loops.
2. **Deterministic Teardown**: Every goroutine must terminate gracefully when parent context cancels or worker shutdown signal is received.
3. **No Bare Goroutines in HTTP Handlers**: Never launch unmanaged `go func()` inside an HTTP handler without tracking or detached background worker context.
4. **Channel Ownership**: The sender creates and closes the channel; receivers NEVER close channels.
5. **Always Run `-race`**: All tests with concurrency must pass `go test -race ./...`.

---

## Safe Concurrency Patterns

### 1. Parallel Task Execution with `errgroup` (Recommended)
Use `golang.org/x/sync/errgroup` for fan-out / fan-in with context propagation and fast-fail error handling.

```go
package analysis

import (
	"context"
	"fmt"

	"golang.org/x/sync/errgroup"
)

func (e *Engine) FetchMarketData(ctx context.Context, symbols []string) ([]MarketData, error) {
	g, gCtx := errgroup.WithContext(ctx)
	// Limit concurrency to prevent socket exhaustion
	g.SetLimit(10)

	results := make([]MarketData, len(symbols))

	for i, sym := range symbols {
		i, sym := i, sym // capture loop variable
		g.Go(func() error {
			data, err := e.client.GetQuote(gCtx, sym)
			if err != nil {
				return fmt.Errorf("fetch quote %s failed: %w", sym, err)
			}
			results[i] = data
			return nil
		})
	}

	if err := g.Wait(); err != nil {
		return nil, err
	}
	return results, nil
}
```

---

### 2. Graceful Background Worker with Ticker
Always stop `time.NewTicker` to prevent timer resource leaks.

```go
func RunPeriodicIntelligenceSync(ctx context.Context, interval time.Duration, runJob func(context.Context)) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop() // Essential: prevents ticker leak

	for {
		select {
		case <-ctx.Done():
			// Context canceled, exit cleanly
			return
		case <-ticker.C:
			// Execute task with child timeout
			jobCtx, cancel := context.WithTimeout(ctx, 30*time.Second)
			runJob(jobCtx)
			cancel()
		}
	}
}
```

---

### 3. Worker Pool with Graceful Drain

```go
type Job struct {
	Symbol string
	Result chan<- SignalResult
}

func Worker(ctx context.Context, id int, jobs <-chan Job, wg *sync.WaitGroup) {
	defer wg.Done()
	for {
		select {
		case <-ctx.Done():
			return
		case job, ok := <-jobs:
			if !ok {
				// Channel closed, drain complete
				return
			}
			res := computeSignal(job.Symbol)
			select {
			case job.Result <- res:
			case <-ctx.Done():
				return
			}
		}
	}
}
```

---

### 4. Shared State Protection with Mutex / RWMutex
- Use `sync.RWMutex` when reads far outnumber writes.
- Always use `defer mu.Unlock()` immediately after `mu.Lock()`.
- Never perform I/O, network calls, or channel operations while holding a lock.

```go
type SafeCache struct {
	mu    sync.RWMutex
	items map[string]CachedSignal
}

func (c *SafeCache) Get(key string) (CachedSignal, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	val, ok := c.items[key]
	return val, ok
}

func (c *SafeCache) Set(key string, val CachedSignal) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.items[key] = val
}
```

---

## Concurrency Pitfalls & Rationalization Table

| Anti-Pattern | Root Cause | Fix |
|---|---|---|
| `go doSomething(r.Context())` inside HTTP handler | When HTTP request finishes, `r.Context()` is canceled immediately, killing the async task | Use detached context with independent worker pool or `context.WithoutCancel(r.Context())` |
| Writing to unbuffered channel with no reader | Sender blocks forever, causing goroutine leak | Ensure buffer size or select on `<-ctx.Done()` |
| Calling `time.Tick(d)` in loop/function | `time.Tick` can NEVER be stopped or garbage collected | Use `ticker := time.NewTicker(d)` with `defer ticker.Stop()` |
| Closing a channel from multiple goroutines | Causes `panic: close of closed channel` | Close ONLY from a single designated producer goroutine or use `sync.Once` |
| Calling network I/O inside `mu.Lock()` | Holds lock during slow I/O, starving all other goroutines | Fetch I/O outside lock, acquire lock only to update memory state |

---

## Red Flags - STOP and Fix Immediately

- [ ] A `go func()` with no `context.Context` or `quit` channel.
- [ ] Goroutine writing to a channel without a `select` covering `ctx.Done()`.
- [ ] Mutex locked without an immediate `defer mu.Unlock()`.
- [ ] `sync.WaitGroup.Add()` called *inside* the goroutine instead of *before* starting it.
- [ ] Iterating slice in loop and passing loop pointer to goroutine without local re-binding.

---

## Verification
Run tests with race detection:
```bash
go test -race -v -count=1 ./...
```
