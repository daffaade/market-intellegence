package handler

import (
	"encoding/json"
	"errors"
	"net/http"
	"strings"

	"be/internal/delivery/http/dto"
	"be/internal/domain"
	"be/internal/usecase"
)

type ConsumerHandler struct {
	consumerUsecase *usecase.ConsumerBehaviorUsecase
}

func NewConsumerHandler(u *usecase.ConsumerBehaviorUsecase) *ConsumerHandler {
	return &ConsumerHandler{consumerUsecase: u}
}

// Analyze handles POST /api/v1/consumer-behavior/analyze
func (h *ConsumerHandler) Analyze(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		dto.RenderError(w, http.StatusMethodNotAllowed, "method not allowed")
		return
	}

	var req domain.ConsumerBehaviorRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		dto.RenderError(w, http.StatusBadRequest, "invalid request body: "+err.Error())
		return
	}

	report, err := h.consumerUsecase.Analyze(r.Context(), req)
	if err != nil {
		if errors.Is(err, domain.ErrEmptyKeyword) {
			dto.RenderError(w, http.StatusBadRequest, err.Error())
			return
		}
		dto.RenderError(w, http.StatusInternalServerError, err.Error())
		return
	}

	dto.RenderSuccess(w, http.StatusOK, report)
}

// AnalyzeQuery handles GET /api/v1/consumer-behavior/analyze
func (h *ConsumerHandler) AnalyzeQuery(w http.ResponseWriter, r *http.Request) {
	keyword := strings.TrimSpace(r.URL.Query().Get("keyword"))
	industry := strings.TrimSpace(r.URL.Query().Get("industry"))

	if keyword == "" {
		dto.RenderError(w, http.StatusBadRequest, "query parameter 'keyword' is required")
		return
	}

	req := domain.ConsumerBehaviorRequest{
		Keyword:  keyword,
		Industry: industry,
	}

	report, err := h.consumerUsecase.Analyze(r.Context(), req)
	if err != nil {
		dto.RenderError(w, http.StatusInternalServerError, err.Error())
		return
	}

	dto.RenderSuccess(w, http.StatusOK, report)
}
