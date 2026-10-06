package handler

import (
	"encoding/json"
	"errors"
	"net/http"

	"be/internal/delivery/http/dto"
	"be/internal/domain"
	"be/internal/usecase"
)

type PortfolioHandler struct {
	portfolioUsecase *usecase.PortfolioUsecase
}

func NewPortfolioHandler(u *usecase.PortfolioUsecase) *PortfolioHandler {
	return &PortfolioHandler{portfolioUsecase: u}
}

// CalculateRisk handles POST /api/v1/portfolio/risk
func (h *PortfolioHandler) CalculateRisk(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		dto.RenderError(w, http.StatusMethodNotAllowed, "method not allowed")
		return
	}

	var req domain.PortfolioRiskRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		dto.RenderError(w, http.StatusBadRequest, "invalid request body: "+err.Error())
		return
	}

	report, err := h.portfolioUsecase.CalculateRisk(r.Context(), req)
	if err != nil {
		if errors.Is(err, domain.ErrInvalidPortfolio) {
			dto.RenderError(w, http.StatusBadRequest, err.Error())
			return
		}
		dto.RenderError(w, http.StatusInternalServerError, err.Error())
		return
	}

	dto.RenderSuccess(w, http.StatusOK, report)
}
