package http

import (
	"log/slog"
	"net/http"

	"be/internal/delivery/http/handler"
	"be/internal/delivery/http/middleware"
)

type Handlers struct {
	Health       *handler.HealthHandler
	Company      *handler.CompanyHandler
	Intelligence *handler.IntelligenceHandler
	Scanner      *handler.ScannerHandler
}

func NewRouter(handlers Handlers, logger *slog.Logger) http.Handler {
	mux := http.NewServeMux()

	// Health check
	mux.HandleFunc("GET /api/v1/health", handlers.Health.Health)

	// Market Overview & Scanner
	mux.HandleFunc("GET /api/v1/market/overview", handlers.Scanner.GetMarketOverview)
	mux.HandleFunc("POST /api/v1/screener", handlers.Scanner.Screen)

	// Companies
	mux.HandleFunc("GET /api/v1/companies", handlers.Company.ListCompanies)
	mux.HandleFunc("GET /api/v1/companies/{symbol}", handlers.Company.GetCompany)

	// Company Intelligence & Signatures
	mux.HandleFunc("GET /api/v1/companies/{symbol}/intelligence", handlers.Intelligence.GetCompanyIntelligence)
	mux.HandleFunc("GET /api/v1/companies/{symbol}/anomalies", handlers.Intelligence.GetCompanyAnomalies)
	mux.HandleFunc("GET /api/v1/companies/{symbol}/peers", handlers.Intelligence.GetCompanyPeers)

	// Apply Middlewares: CORS -> Logger -> Mux
	var rootHandler http.Handler = mux
	rootHandler = middleware.Logger(logger, rootHandler)
	rootHandler = middleware.CORS(rootHandler)

	return rootHandler
}
