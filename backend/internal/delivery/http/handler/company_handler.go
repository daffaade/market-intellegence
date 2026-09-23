package handler

import (
	"errors"
	"net/http"

	"be/internal/delivery/http/dto"
	"be/internal/domain"
	"be/internal/usecase"
)

type CompanyHandler struct {
	companyUsecase *usecase.CompanyUsecase
}

func NewCompanyHandler(u *usecase.CompanyUsecase) *CompanyHandler {
	return &CompanyHandler{companyUsecase: u}
}

func (h *CompanyHandler) ListCompanies(w http.ResponseWriter, r *http.Request) {
	companies, err := h.companyUsecase.ListCompanies(r.Context())
	if err != nil {
		dto.RenderError(w, http.StatusInternalServerError, err.Error())
		return
	}
	dto.RenderSuccess(w, http.StatusOK, companies)
}

func (h *CompanyHandler) GetCompany(w http.ResponseWriter, r *http.Request) {
	symbol := r.PathValue("symbol")
	if symbol == "" {
		dto.RenderError(w, http.StatusBadRequest, "symbol is required")
		return
	}

	comp, err := h.companyUsecase.GetCompany(r.Context(), symbol)
	if err != nil {
		if errors.Is(err, domain.ErrCompanyNotFound) {
			dto.RenderError(w, http.StatusNotFound, "company not found")
			return
		}
		dto.RenderError(w, http.StatusInternalServerError, err.Error())
		return
	}

	dto.RenderSuccess(w, http.StatusOK, comp)
}
