package llm

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	"be/internal/domain"
	"be/internal/platform/config"
)

type Client struct {
	provider   string
	model      string
	apiKey     string
	httpClient *http.Client
}

func NewClient(cfg *config.Config) *Client {
	return &Client{
		provider: cfg.AIProvider,
		model:    cfg.AIModel,
		apiKey:   cfg.AIApiKey,
		httpClient: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

func (c *Client) GenerateSummary(ctx context.Context, snapshot *domain.IntelligenceSnapshot) (string, error) {
	if c.provider == "gemini" && c.apiKey != "" {
		summary, err := c.callGemini(ctx, snapshot)
		if err == nil && summary != "" {
			return summary, nil
		}
	} else if c.provider == "groq" && c.apiKey != "" {
		summary, err := c.callGroq(ctx, snapshot)
		if err == nil && summary != "" {
			return summary, nil
		}
	}

	// Default / Fallback: Rule-Based Fact-Grounded Synthesizer
	return c.synthesizeRuleBasedSummary(snapshot), nil
}

// callGemini executes a prompt against the Google Gemini generateContent REST API
func (c *Client) callGemini(ctx context.Context, snapshot *domain.IntelligenceSnapshot) (string, error) {
	url := fmt.Sprintf("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=%s", c.model, c.apiKey)

	prompt := c.buildFactPrompt(snapshot)
	payload := map[string]interface{}{
		"contents": []map[string]interface{}{
			{
				"parts": []map[string]string{
					{"text": prompt},
				},
			},
		},
		"generationConfig": map[string]interface{}{
			"temperature":     0.2, // Low temperature to prevent hallucination
			"maxOutputTokens": 300,
		},
	}

	body, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewBuffer(body))
	if err != nil {
		return "", err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("gemini api returned status: %d", resp.StatusCode)
	}

	var result struct {
		Candidates []struct {
			Content struct {
				Parts []struct {
					Text string `json:"text"`
				} `json:"parts"`
			} `json:"content"`
		} `json:"candidates"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", err
	}

	if len(result.Candidates) > 0 && len(result.Candidates[0].Content.Parts) > 0 {
		return strings.TrimSpace(result.Candidates[0].Content.Parts[0].Text), nil
	}
	return "", fmt.Errorf("empty gemini response")
}

// callGroq calls the Groq OpenAI-compatible Chat Completions API
func (c *Client) callGroq(ctx context.Context, snapshot *domain.IntelligenceSnapshot) (string, error) {
	url := "https://api.groq.com/openai/v1/chat/completions"

	prompt := c.buildFactPrompt(snapshot)
	payload := map[string]interface{}{
		"model": c.model,
		"messages": []map[string]string{
			{"role": "system", "content": "Anda adalah analis riset pasar modal Indonesia yang objektif dan bebas halusinasi. Hanya rangkum bukti data yang diberikan. Dilarang memberikan rekomendasi Beli atau Jual."},
			{"role": "user", "content": prompt},
		},
		"temperature": 0.2,
		"max_tokens":  300,
	}

	body, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewBuffer(body))
	if err != nil {
		return "", err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+c.apiKey)

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("groq api returned status: %d", resp.StatusCode)
	}

	var result struct {
		Choices []struct {
			Message struct {
				Content string `json:"content"`
			} `json:"message"`
		} `json:"choices"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", err
	}

	if len(result.Choices) > 0 {
		return strings.TrimSpace(result.Choices[0].Message.Content), nil
	}
	return "", fmt.Errorf("empty groq response")
}

func (c *Client) buildFactPrompt(snapshot *domain.IntelligenceSnapshot) string {
	var sb strings.Builder
	sb.WriteString(fmt.Sprintf("Tolong buat ringkasan analisis riset pasar (2 paragraf singkat) untuk emiten %s berdasarkan fakta berikut:\n", snapshot.Symbol))
	sb.WriteString(fmt.Sprintf("- Skor Peluang: %.1f / 100\n", snapshot.OpportunityScore))
	sb.WriteString(fmt.Sprintf("- Level Risiko: %s (Skor Risiko: %.1f)\n", snapshot.RiskLevel, snapshot.RiskScore))
	sb.WriteString(fmt.Sprintf("- Arah Sentimen Analisis: %s (Keyakinan: %s)\n", snapshot.Direction, snapshot.Confidence))

	if len(snapshot.PositiveFactors) > 0 {
		sb.WriteString("Faktor Positif:\n")
		for _, f := range snapshot.PositiveFactors {
			sb.WriteString(fmt.Sprintf("  * %s\n", f))
		}
	}
	if len(snapshot.NegativeFactors) > 0 {
		sb.WriteString("Faktor Risiko:\n")
		for _, f := range snapshot.NegativeFactors {
			sb.WriteString(fmt.Sprintf("  * %s\n", f))
		}
	}
	if len(snapshot.Evidence) > 0 {
		sb.WriteString("Bukti Metrik:\n")
		for _, e := range snapshot.Evidence {
			sb.WriteString(fmt.Sprintf("  * %s: Emiten %s vs Median Industri %s (Posisi: %s)\n", e.Metric, e.CompanyValue, e.PeerMedian, e.Position))
		}
	}
	sb.WriteString("\nAturan ketat: Gunakan bahasa Indonesia profesional. Jangan mengarang angka baru. Dilarang menyarankan 'Beli', 'Jual', atau 'Koleksi'.")
	return sb.String()
}

func (c *Client) synthesizeRuleBasedSummary(s *domain.IntelligenceSnapshot) string {
	positives := strings.Join(s.PositiveFactors, ", ")
	if positives == "" {
		positives = "stabilitas indikator operasional"
	}
	negatives := strings.Join(s.NegativeFactors, ", ")
	if negatives == "" {
		negatives = "faktor volatilitas pasar umum"
	}

	var divNote string
	if s.DivergenceDetected {
		divNote = "Sistem juga mendeteksi adanya divergensi fundamental, di mana pergerakan harga atau valuasi memperlihatkan anomali relatif terhadap arah akumulasi data."
	}

	return fmt.Sprintf(
		"Berdasarkan engine intelijen pasar, emiten %s saat ini memperlihatkan sinyal %s dengan Skor Peluang %.1f/100 (Keyakinan %s) dan tingkat risiko %s. Pendorong utama sinyal positif mencakup %s. %s Di sisi kehati-hatian, pelaku riset perlu memantau %s.",
		s.Symbol, s.Direction, s.OpportunityScore, s.Confidence, s.RiskLevel, positives, divNote, negatives,
	)
}
