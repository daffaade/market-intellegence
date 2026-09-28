package handler

import (
	"errors"
	"net/http"
	"strings"

	"be/internal/delivery/http/dto"
	"be/internal/domain"
	"be/internal/usecase"
)

type IntelligenceHandler struct {
	intelUsecase *usecase.IntelligenceUsecase
}

func NewIntelligenceHandler(u *usecase.IntelligenceUsecase) *IntelligenceHandler {
	return &IntelligenceHandler{intelUsecase: u}
}

func (h *IntelligenceHandler) GetCompanyIntelligence(w http.ResponseWriter, r *http.Request) {
	symbol := strings.ToUpper(strings.TrimSpace(r.PathValue("symbol")))
	if symbol == "" {
		dto.RenderError(w, http.StatusBadRequest, "symbol is required")
		return
	}

	snap, err := h.intelUsecase.GetCompanyIntelligence(r.Context(), symbol)
	if err != nil {
		if errors.Is(err, domain.ErrInvalidSymbol) {
			dto.RenderError(w, http.StatusBadRequest, "invalid symbol")
			return
		}
		dto.RenderError(w, http.StatusInternalServerError, err.Error())
		return
	}

	dto.RenderSuccess(w, http.StatusOK, snap)
}

func (h *IntelligenceHandler) GetCompanyAnomalies(w http.ResponseWriter, r *http.Request) {
	symbol := strings.ToUpper(strings.TrimSpace(r.PathValue("symbol")))
	if symbol == "" {
		dto.RenderError(w, http.StatusBadRequest, "symbol is required")
		return
	}

	snap, err := h.intelUsecase.GetCompanyIntelligence(r.Context(), symbol)
	if err != nil {
		dto.RenderError(w, http.StatusInternalServerError, err.Error())
		return
	}

	anomalyData := map[string]interface{}{
		"symbol":              snap.Symbol,
		"is_anomaly":          snap.IsAnomaly,
		"anomaly_score":       snap.AnomalyScore,
		"divergence_detected": snap.DivergenceDetected,
		"supporting_factors":  snap.SupportingFactors,
		"evidence":            snap.Evidence,
	}

	dto.RenderSuccess(w, http.StatusOK, anomalyData)
}

func (h *IntelligenceHandler) GetCompanyPeers(w http.ResponseWriter, r *http.Request) {
	symbol := strings.ToUpper(strings.TrimSpace(r.PathValue("symbol")))
	if symbol == "" {
		dto.RenderError(w, http.StatusBadRequest, "symbol is required")
		return
	}

	snap, err := h.intelUsecase.GetCompanyIntelligence(r.Context(), symbol)
	if err != nil {
		dto.RenderError(w, http.StatusInternalServerError, err.Error())
		return
	}

	peerData := map[string]interface{}{
		"symbol":          snap.Symbol,
		"peer_comparison": snap.PeerComparison,
		"evidence":        snap.Evidence,
	}

	dto.RenderSuccess(w, http.StatusOK, peerData)
}
