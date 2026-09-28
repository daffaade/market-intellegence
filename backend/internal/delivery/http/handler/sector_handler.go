package handler

import (
	"encoding/json"
	"errors"
	"net/http"

	"be/internal/domain"
	"be/internal/usecase"
)

type SectorHandler struct {
	sectorUsecase usecase.SectorUsecase
}

func NewSectorHandler(sectorUsecase usecase.SectorUsecase) *SectorHandler {
	return &SectorHandler{sectorUsecase: sectorUsecase}
}

func (h *SectorHandler) GetSector(w http.ResponseWriter, r *http.Request) {
	sectorName := r.PathValue("sector")
	sec, err := h.sectorUsecase.GetSectorIntelligence(r.Context(), sectorName)
	if err != nil {
		if errors.Is(err, domain.ErrInvalidSector) || errors.Is(err, domain.ErrSectorNotFound) {
			renderError(w, http.StatusNotFound, err.Error())
			return
		}
		renderError(w, http.StatusInternalServerError, err.Error())
		return
	}

	renderJSON(w, http.StatusOK, sec)
}

func (h *SectorHandler) ListSectors(w http.ResponseWriter, r *http.Request) {
	sectors, err := h.sectorUsecase.ListSectors(r.Context())
	if err != nil {
		renderError(w, http.StatusInternalServerError, err.Error())
		return
	}

	renderJSON(w, http.StatusOK, map[string]any{
		"sectors": sectors,
		"count":   len(sectors),
	})
}

func renderJSON(w http.ResponseWriter, statusCode int, data any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	_ = json.NewEncoder(w).Encode(data)
}

func renderError(w http.ResponseWriter, statusCode int, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	_ = json.NewEncoder(w).Encode(map[string]any{
		"error":  message,
		"status": statusCode,
	})
}
