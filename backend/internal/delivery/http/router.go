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
	Portfolio    *handler.PortfolioHandler
	MarketData   *handler.MarketDataHandler
}

func NewRouter(handlers Handlers, logger *slog.Logger) http.Handler {
	mux := http.NewServeMux()

	// Health check
	mux.HandleFunc("GET /api/v1/health", handlers.Health.Health)

	// Market Overview, Scanner & Growth Timeline
	mux.HandleFunc("GET /api/v1/market/overview", handlers.Scanner.GetMarketOverview)
	mux.HandleFunc("POST /api/v1/screener", handlers.Scanner.Screen)

	// Portfolio Risk
	if handlers.Portfolio != nil {
		mux.HandleFunc("POST /api/v1/portfolio/risk", handlers.Portfolio.CalculateRisk)
	}

	// Companies & Fundamentals
	mux.HandleFunc("GET /api/v1/companies", handlers.Company.ListCompanies)
	mux.HandleFunc("GET /api/v1/companies/{symbol}", handlers.Company.GetCompany)
	mux.HandleFunc("GET /api/v1/companies/{symbol}/fundamentals", handlers.Analytics.GetFundamentals)

	// Company Intelligence & Signatures
	mux.HandleFunc("GET /api/v1/companies/{symbol}/intelligence", handlers.Intelligence.GetCompanyIntelligence)
	mux.HandleFunc("GET /api/v1/companies/{symbol}/anomalies", handlers.Intelligence.GetCompanyAnomalies)
	mux.HandleFunc("GET /api/v1/companies/{symbol}/peers", handlers.Intelligence.GetCompanyPeers)

	// Live market series (yfinance via the engine)
	if handlers.MarketData != nil {
		mux.HandleFunc("GET /api/v1/market/performance", handlers.MarketData.GetPerformance)
		mux.HandleFunc("GET /api/v1/macro/snapshot", handlers.MarketData.GetMacroSnapshot)
		mux.HandleFunc("GET /api/v1/companies/{symbol}/events", handlers.MarketData.GetCorporateEvents)
		mux.HandleFunc("GET /api/v1/companies/{symbol}/macro-sensitivity", handlers.MarketData.GetMacroSensitivity)
		mux.HandleFunc("GET /api/v1/pipeline/sources", handlers.MarketData.GetPipelineSources)
		mux.HandleFunc("GET /api/v1/sectors", handlers.MarketData.GetSectors)
		mux.HandleFunc("GET /api/v1/consumer-behavior/analyze", handlers.MarketData.GetConsumerBehavior)
	}

	// Apply Middlewares: CORS -> Logger -> Mux
	var rootHandler http.Handler = mux
	rootHandler = middleware.Logger(logger, rootHandler)
	rootHandler = middleware.CORS(rootHandler)

	return rootHandler
}
