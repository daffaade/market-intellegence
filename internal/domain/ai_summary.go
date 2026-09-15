package domain

type AISummary struct {
	Symbol     string   `json:"symbol"`
	Summary    string   `json:"summary"`
	Highlights []string `json:"highlights,omitempty"`
	Disclaimer string   `json:"disclaimer"`
}
