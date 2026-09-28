package handler

import (
	"net/http"
	"time"

	"be/internal/delivery/http/dto"
	"be/internal/platform/config"
)

type HealthHandler struct {
	cfg *config.Config
}

func NewHealthHandler(cfg *config.Config) *HealthHandler {
	return &HealthHandler{cfg: cfg}
}

func (h *HealthHandler) Health(w http.ResponseWriter, r *http.Request) {
	healthData := map[string]interface{}{
		"status":      "ok",
		"timestamp":   time.Now().Format(time.RFC3339),
		"ai_provider": h.cfg.AIProvider,
		"ai_model":    h.cfg.AIModel,
		"mock_mode":   h.cfg.MockSectors,
		"version":     "v1.0.0-hackathon",
	}
	dto.RenderSuccess(w, http.StatusOK, healthData)
}
