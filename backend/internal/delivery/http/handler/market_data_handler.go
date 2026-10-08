package handler

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"strings"

	"be/internal/delivery/http/dto"
	"be/internal/domain"
	"be/internal/usecase"
)

type MarketDataHandler struct {
	usecase *usecase.MarketDataUsecase
}

func NewMarketDataHandler(u *usecase.MarketDataUsecase) *MarketDataHandler {
	return &MarketDataHandler{usecase: u}
}

func (h *MarketDataHandler) render(w http.ResponseWriter, fetch func() (json.RawMessage, error)) {
	data, err := fetch()
	switch {
	case err == nil:
		dto.RenderSuccess(w, http.StatusOK, data)
	case errors.Is(err, domain.ErrCompanyNotFound):
		dto.RenderError(w, http.StatusNotFound, "company not found")
	case errors.Is(err, domain.ErrUpstreamUnavailable), errors.Is(err, context.DeadlineExceeded):
		dto.RenderError(w, http.StatusServiceUnavailable, "market data is temporarily unavailable")
	default:
		dto.RenderError(w, http.StatusInternalServerError, err.Error())
	}
}

func (h *MarketDataHandler) GetPerformance(w http.ResponseWriter, r *http.Request) {
	h.render(w, func() (json.RawMessage, error) { return h.usecase.GetPerformance(r.Context()) })
}

func (h *MarketDataHandler) GetMacroSnapshot(w http.ResponseWriter, r *http.Request) {
	h.render(w, func() (json.RawMessage, error) { return h.usecase.GetMacroSnapshot(r.Context()) })
}

func (h *MarketDataHandler) GetCorporateEvents(w http.ResponseWriter, r *http.Request) {
	symbol := strings.ToUpper(strings.TrimSpace(r.PathValue("symbol")))
	h.render(w, func() (json.RawMessage, error) { return h.usecase.GetCorporateEvents(r.Context(), symbol) })
}
