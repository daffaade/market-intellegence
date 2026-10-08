package handler

import (
	"errors"
	"net/http"
	"strings"

	"be/internal/delivery/http/dto"
	"be/internal/domain"
	"be/internal/usecase"
)

type AnalyticsHandler struct {
	analyticsUsecase *usecase.AnalyticsUsecase
}

func NewAnalyticsHandler(u *usecase.AnalyticsUsecase) *AnalyticsHandler {
	return &AnalyticsHandler{analyticsUsecase: u}
}

func (h *AnalyticsHandler) GetFundamentals(w http.ResponseWriter, r *http.Request) {
	symbol := strings.ToUpper(strings.TrimSpace(r.PathValue("symbol")))
	if symbol == "" {
		dto.RenderError(w, http.StatusBadRequest, "symbol is required")
		return
	}

	fundamentals, err := h.analyticsUsecase.GetFundamentals(r.Context(), symbol)
	if err != nil {
		if errors.Is(err, domain.ErrCompanyNotFound) {
			dto.RenderError(w, http.StatusNotFound, "company fundamentals not found")
			return
		}
		if errors.Is(err, domain.ErrFundamentalsUnavailable) {
			dto.RenderError(w, http.StatusServiceUnavailable, "fundamentals are temporarily unavailable")
			return
		}
		dto.RenderError(w, http.StatusInternalServerError, err.Error())
		return
	}

	dto.RenderSuccess(w, http.StatusOK, fundamentals)
}

func (h *AnalyticsHandler) GetMarketGrowthTimeline(w http.ResponseWriter, r *http.Request) {
	timeline, err := h.analyticsUsecase.GetMarketGrowthTimeline(r.Context())
	if err != nil {
		dto.RenderError(w, http.StatusInternalServerError, err.Error())
		return
	}
	dto.RenderSuccess(w, http.StatusOK, timeline)
}

func (h *AnalyticsHandler) GetPipelineTelemetry(w http.ResponseWriter, r *http.Request) {
	telemetry, err := h.analyticsUsecase.GetPipelineTelemetry(r.Context())
	if err != nil {
		dto.RenderError(w, http.StatusInternalServerError, err.Error())
		return
	}
	dto.RenderSuccess(w, http.StatusOK, telemetry)
}

func (h *AnalyticsHandler) GetMacroIndicators(w http.ResponseWriter, r *http.Request) {
	indicators, err := h.analyticsUsecase.GetMacroIndicators(r.Context())
	if err != nil {
		dto.RenderError(w, http.StatusInternalServerError, err.Error())
		return
	}
	dto.RenderSuccess(w, http.StatusOK, indicators)
}

func (h *AnalyticsHandler) GetDisasterRisks(w http.ResponseWriter, r *http.Request) {
	risks, err := h.analyticsUsecase.GetDisasterRisks(r.Context())
	if err != nil {
		dto.RenderError(w, http.StatusInternalServerError, err.Error())
		return
	}
	dto.RenderSuccess(w, http.StatusOK, risks)
}

func (h *AnalyticsHandler) GetPortfolioPositions(w http.ResponseWriter, r *http.Request) {
	positions, err := h.analyticsUsecase.GetPortfolioPositions(r.Context())
	if err != nil {
		dto.RenderError(w, http.StatusInternalServerError, err.Error())
		return
	}
	dto.RenderSuccess(w, http.StatusOK, positions)
}
