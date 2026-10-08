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
