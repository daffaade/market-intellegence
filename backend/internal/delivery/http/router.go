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
	Analytics    *handler.AnalyticsHandler
	Sector       *handler.SectorHandler
}

func NewRouter(handlers Handlers, logger *slog.Logger) http.Handler {
	mux := http.NewServeMux()

	// Health check
	mux.HandleFunc("GET /api/v1/health", handlers.Health.Health)

	// Market Overview, Scanner & Growth Timeline
	mux.HandleFunc("GET /api/v1/market/overview", handlers.Scanner.GetMarketOverview)
	mux.HandleFunc("GET /api/v1/market/growth-timeline", handlers.Analytics.GetMarketGrowthTimeline)
	mux.HandleFunc("POST /api/v1/screener", handlers.Scanner.Screen)

	// Sectors Intelligence
	if handlers.Sector != nil {
		mux.HandleFunc("GET /api/v1/sectors", handlers.Sector.ListSectors)
		mux.HandleFunc("GET /api/v1/sectors/{sector}", handlers.Sector.GetSector)
	}

	// Companies & Fundamentals
	mux.HandleFunc("GET /api/v1/companies", handlers.Company.ListCompanies)
	mux.HandleFunc("GET /api/v1/companies/{symbol}", handlers.Company.GetCompany)
	mux.HandleFunc("GET /api/v1/companies/{symbol}/fundamentals", handlers.Analytics.GetFundamentals)

	// Company Intelligence & Signatures
	mux.HandleFunc("GET /api/v1/companies/{symbol}/intelligence", handlers.Intelligence.GetCompanyIntelligence)
	mux.HandleFunc("GET /api/v1/companies/{symbol}/anomalies", handlers.Intelligence.GetCompanyAnomalies)
	mux.HandleFunc("GET /api/v1/companies/{symbol}/peers", handlers.Intelligence.GetCompanyPeers)

	// Pipeline Telemetry & Macro Indicators
	mux.HandleFunc("GET /api/v1/pipeline/telemetry", handlers.Analytics.GetPipelineTelemetry)
	mux.HandleFunc("GET /api/v1/macro/indicators", handlers.Analytics.GetMacroIndicators)
	mux.HandleFunc("GET /api/v1/macro/disaster-risks", handlers.Analytics.GetDisasterRisks)
	mux.HandleFunc("GET /api/v1/portfolio/positions", handlers.Analytics.GetPortfolioPositions)

	// Apply Middlewares: CORS -> Logger -> Mux
	var rootHandler http.Handler = mux
	rootHandler = middleware.Logger(logger, rootHandler)
	rootHandler = middleware.CORS(rootHandler)

	return rootHandler
}
