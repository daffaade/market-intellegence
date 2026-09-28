package handler

import (
	"encoding/json"
	"net/http"

	"be/internal/delivery/http/dto"
	"be/internal/usecase"
)

type ScannerHandler struct {
	scannerUsecase *usecase.ScannerUsecase
}

func NewScannerHandler(u *usecase.ScannerUsecase) *ScannerHandler {
	return &ScannerHandler{scannerUsecase: u}
}

func (h *ScannerHandler) GetMarketOverview(w http.ResponseWriter, r *http.Request) {
	overview, err := h.scannerUsecase.GetMarketOverview(r.Context())
	if err != nil {
		dto.RenderError(w, http.StatusInternalServerError, err.Error())
		return
	}
	dto.RenderSuccess(w, http.StatusOK, overview)
}

func (h *ScannerHandler) Screen(w http.ResponseWriter, r *http.Request) {
	var filter usecase.ScreenerFilter
	if r.Body != nil && r.ContentLength > 0 {
		if err := json.NewDecoder(r.Body).Decode(&filter); err != nil {
			dto.RenderError(w, http.StatusBadRequest, "invalid json body: "+err.Error())
			return
		}
	}

	results, err := h.scannerUsecase.Screen(r.Context(), filter)
	if err != nil {
		dto.RenderError(w, http.StatusInternalServerError, err.Error())
		return
	}
	dto.RenderSuccess(w, http.StatusOK, results)
}
