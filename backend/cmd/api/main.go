package main

import (
	"context"
	"errors"
	nethttp "net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	sqlc "be/db/sqlc"
	"be/internal/adapter/llm"
	"be/internal/adapter/python_engine"
	deliveryhttp "be/internal/delivery/http"
	"be/internal/delivery/http/handler"
	"be/internal/domain"
	"be/internal/platform/config"
	"be/internal/platform/logger"
	"be/internal/repository/memory"
	"be/internal/repository/postgres"
	"be/internal/usecase"
)

func main() {
	// 1. Load Configurations
	cfg, err := config.LoadConfig()
	if err != nil {
		nethttp.HandleFunc("/", func(w nethttp.ResponseWriter, r *nethttp.Request) {
			nethttp.Error(w, "config error: "+err.Error(), nethttp.StatusInternalServerError)
		})
		_ = nethttp.ListenAndServe(":8080", nil)
		return
	}

	// 2. Initialize Structured Logger
	log := logger.InitLogger(cfg.LogLevel)
	log.Info("starting market intelligence api service",
		"port", cfg.Port,
		"ai_provider", cfg.AIProvider,
		"ai_model", cfg.AIModel,
		"mock_sectors", cfg.MockSectors,
	)

	// 3. Database Connection / Fallback Setup
	var companyRepo domain.CompanyRepository
	var snapshotRepo domain.SnapshotRepository
	var analyticsRepo domain.AnalyticsRepository

	// Always instantiate MemoryRepository for analytics data & fallback
	memRepo := memory.NewMemoryRepository()
	analyticsRepo = memRepo

	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	pool, err := postgres.NewPool(ctx, cfg.DatabaseURL)
	cancel()

	if err != nil {
		log.Warn("postgresql unavailable, activating in-memory repository fallback (zero-setup mode)", "error", err.Error())
		companyRepo = memRepo
		snapshotRepo = memRepo
	} else {
		defer pool.Close()
		log.Info("connected successfully to postgresql pool")
		queries := sqlc.New(pool)
		companyRepo = postgres.NewCompanyRepository(queries)
		snapshotRepo = postgres.NewSnapshotRepository(queries)
	}

	// 4. Initialize Adapters
	pyClient := python_engine.NewClient(cfg.PythonEngineURL)
	aiClient := llm.NewClient(cfg)

	// 5. Initialize Usecases
	companyUsecase := usecase.NewCompanyUsecase(companyRepo)
	intelUsecase := usecase.NewIntelligenceUsecase(snapshotRepo, companyRepo, pyClient, aiClient, cfg)
	scannerUsecase := usecase.NewScannerUsecase(intelUsecase, companyRepo)
	analyticsUsecase := usecase.NewAnalyticsUsecase(analyticsRepo)

	// 6. Initialize Delivery HTTP Handlers & Router
	handlers := deliveryhttp.Handlers{
		Health:       handler.NewHealthHandler(cfg),
		Company:      handler.NewCompanyHandler(companyUsecase),
		Intelligence: handler.NewIntelligenceHandler(intelUsecase),
		Scanner:      handler.NewScannerHandler(scannerUsecase),
		Analytics:    handler.NewAnalyticsHandler(analyticsUsecase),
	}

	router := deliveryhttp.NewRouter(handlers, log)

	server := &nethttp.Server{
		Addr:              ":" + cfg.Port,
		Handler:           router,
		ReadHeaderTimeout: 10 * time.Second,
		IdleTimeout:       60 * time.Second,
	}

	// 7. Start Server in a Goroutine
	serverErrChan := make(chan error, 1)
	go func() {
		log.Info("http server listening", "addr", server.Addr)
		if err := server.ListenAndServe(); err != nil && !errors.Is(err, nethttp.ErrServerClosed) {
			serverErrChan <- err
		}
	}()

	// 8. Graceful Shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, os.Interrupt, syscall.SIGTERM)

	select {
	case err := <-serverErrChan:
		log.Error("server fatal error", "error", err)
		os.Exit(1)
	case sig := <-quit:
		log.Info("shutdown signal received", "signal", sig.String())
	}

	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer shutdownCancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		log.Error("failed to gracefully shutdown server", "error", err)
	} else {
		log.Info("server exited cleanly")
	}
}
