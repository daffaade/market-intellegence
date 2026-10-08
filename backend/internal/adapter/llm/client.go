package llm

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"regexp"
	"strings"
	"sync"
	"time"

	"be/internal/domain"
	"be/internal/platform/config"
)

type Client struct {
	// mu serialises LLM calls: snapshot refreshes run several at once and the
	// Gemini free tier rejects bursts with 429.
	mu         sync.Mutex
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
			// Thinking models take several seconds; summaries are generated off the
			// request path (cache refresh), so a generous timeout costs nothing.
			Timeout: 45 * time.Second,
		},
	}
}

func (c *Client) GenerateSummary(ctx context.Context, snapshot *domain.IntelligenceSnapshot) (string, error) {
	var (
		summary string
		err     error
	)
	switch {
	case c.provider == "gemini" && c.apiKey != "":
		summary, err = c.withRetry(ctx, func() (string, error) { return c.callGemini(ctx, snapshot) })
	case c.provider == "groq" && c.apiKey != "":
		summary, err = c.callGroq(ctx, snapshot)
	default:
		return c.synthesizeRuleBasedSummary(snapshot), nil
	}

	if err == nil {
		err = validateSummary(summary, c.buildFactPrompt(snapshot))
	}
	if err != nil {
		slog.Warn("llm summary rejected, using rule-based summary",
			"provider", c.provider, "model", c.model, "symbol", snapshot.Symbol, "error", err.Error())
		return c.synthesizeRuleBasedSummary(snapshot), nil
	}
	return summary, nil
}

var errRateLimited = errors.New("llm provider rate limited")

// withRetry runs one call at a time and retries rate-limit/overload responses
// with growing pauses, as long as the caller's context allows.
func (c *Client) withRetry(ctx context.Context, call func() (string, error)) (string, error) {
	c.mu.Lock()
	defer c.mu.Unlock()
	var err error
	for attempt, wait := 0, 15*time.Second; attempt < 4; attempt, wait = attempt+1, wait*2 {
		var out string
		if out, err = call(); !errors.Is(err, errRateLimited) {
			return out, err
		}
		select {
		case <-ctx.Done():
			return "", err
		case <-time.After(wait):
		}
	}
	return "", err
}

// advicePattern catches direct buy/sell/hold advice, which OJK rules forbid in
// user-facing output. Word boundaries keep "penjualan" (sales) and similar legal.
var advicePattern = regexp.MustCompile(`(?i)\b(beli|jual|koleksi|tahan|buy|sell|hold|akumulasi sekarang|layak dibeli)\b`)

var numberPattern = regexp.MustCompile(`\d+(?:[.,]\d+)*`)

// validateSummary enforces "the system computes, the AI explains": no investment
// advice, and no number that does not appear in the facts we gave the model.
func validateSummary(summary, facts string) error {
	if strings.TrimSpace(summary) == "" {
		return fmt.Errorf("empty summary")
	}
	if m := advicePattern.FindString(summary); m != "" {
		return fmt.Errorf("contains advisory wording %q", m)
	}
	known := map[string]bool{}
	for _, n := range numberPattern.FindAllString(facts, -1) {
		known[normalizeNumber(n)] = true
	}
	for _, n := range numberPattern.FindAllString(summary, -1) {
		norm := normalizeNumber(n)
		if len(strings.TrimLeft(strings.ReplaceAll(norm, ".", ""), "0")) <= 1 {
			continue // single digits ("2 faktor", "H+7" style counts) are not data claims
		}
		if !known[norm] {
			return fmt.Errorf("number %q not present in the facts", n)
		}
	}
	return nil
}

// normalizeNumber maps "57,2" and "57.2" (and "57.20") to the same key.
func normalizeNumber(n string) string {
	n = strings.ReplaceAll(n, ",", ".")
	if strings.Contains(n, ".") {
		n = strings.TrimRight(strings.TrimRight(n, "0"), ".")
	}
	return n
}

const systemInstruction = "Anda analis riset pasar modal Indonesia yang objektif. Tugas Anda hanya menjelaskan fakta yang diberikan sistem, bukan menilai sendiri. " +
	"Aturan: (1) Bahasa Indonesia profesional, 2 paragraf singkat, tanpa judul, tanpa poin, tanpa markdown. " +
	"(2) Hanya pakai angka yang ada di fakta, tulis persis seperti di fakta; jangan menghitung atau membulatkan angka baru. " +
	"(3) Jangan menambah klaim di luar fakta, termasuk reputasi perusahaan, ukuran, sejarah, atau kondisi makro. " +
	"(4) Dilarang memberi saran investasi: jangan gunakan kata beli, jual, tahan, koleksi, atau ajakan bertindak. " +
	"Untuk arus dana tulis 'arus masuk/keluar' atau 'pembelian/penjualan bersih', bukan 'tekanan beli/jual'. " +
	"(5) Jika fakta saling bertentangan atau netral, katakan apa adanya. (6) Jangan menulis disclaimer; sistem menambahkannya sendiri."

// callGemini executes a prompt against the Google Gemini generateContent REST API
func (c *Client) callGemini(ctx context.Context, snapshot *domain.IntelligenceSnapshot) (string, error) {
	url := fmt.Sprintf("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent", c.model)

	payload := map[string]interface{}{
		"systemInstruction": map[string]interface{}{
			"parts": []map[string]string{{"text": systemInstruction}},
		},
		"contents": []map[string]interface{}{
			{"role": "user", "parts": []map[string]string{{"text": c.buildFactPrompt(snapshot)}}},
		},
		"generationConfig": map[string]interface{}{
			"temperature": 0.2, // Low temperature to prevent hallucination
			// Thinking tokens count against this limit; 300 left nothing for the answer.
			"maxOutputTokens": 8192,
			"thinkingConfig":  map[string]interface{}{"thinkingLevel": "low"},
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
	// Header rather than ?key= so the key never appears in error messages or logs.
	req.Header.Set("x-goog-api-key", c.apiKey)

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusTooManyRequests || resp.StatusCode == http.StatusServiceUnavailable {
		body, _ := io.ReadAll(io.LimitReader(resp.Body, 8<<10))
		// A daily quota resets hours later; retrying within this request is pointless.
		if bytes.Contains(body, []byte("PerDay")) {
			return "", fmt.Errorf("gemini daily quota exhausted for %s", c.model)
		}
		return "", fmt.Errorf("%w: gemini status %d", errRateLimited, resp.StatusCode)
	}
	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("gemini api returned status: %d", resp.StatusCode)
	}

	var result struct {
		Candidates []struct {
			FinishReason string `json:"finishReason"`
			Content      struct {
				Parts []struct {
					Text    string `json:"text"`
					Thought bool   `json:"thought"`
				} `json:"parts"`
			} `json:"content"`
		} `json:"candidates"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", err
	}
	if len(result.Candidates) == 0 {
		return "", fmt.Errorf("empty gemini response")
	}
	cand := result.Candidates[0]
	if cand.FinishReason != "" && cand.FinishReason != "STOP" {
		return "", fmt.Errorf("gemini stopped early: %s", cand.FinishReason)
	}
	var sb strings.Builder
	for _, p := range cand.Content.Parts {
		if !p.Thought {
			sb.WriteString(p.Text)
		}
	}
	return strings.TrimSpace(sb.String()), nil
}

// callGroq calls the Groq OpenAI-compatible Chat Completions API
func (c *Client) callGroq(ctx context.Context, snapshot *domain.IntelligenceSnapshot) (string, error) {
	url := "https://api.groq.com/openai/v1/chat/completions"

	prompt := c.buildFactPrompt(snapshot)
	payload := map[string]interface{}{
		"model": c.model,
		"messages": []map[string]string{
			{"role": "system", "content": systemInstruction},
			{"role": "user", "content": prompt},
		},
		"temperature": 0.2,
		"max_tokens":  600,
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
	sb.WriteString(fmt.Sprintf("Fakta hasil perhitungan sistem untuk emiten %s:\n", snapshot.Symbol))
	sb.WriteString(fmt.Sprintf("- Skor Peluang: %.1f / 100\n", snapshot.OpportunityScore))
	sb.WriteString(fmt.Sprintf("- Level Risiko: %s (Skor Risiko: %.1f)\n", snapshot.RiskLevel, snapshot.RiskScore))
	sb.WriteString(fmt.Sprintf("- Arah Sentimen Analisis: %s (Keyakinan: %s)\n", snapshot.Direction, snapshot.Confidence))

	if grouped := groupedEvidence(snapshot.Evidence); grouped != "" {
		sb.WriteString(grouped)
	} else {
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
				sb.WriteString(fmt.Sprintf("  * %s: emiten %s vs pembanding %s (%s)\n", metricLabel(e.Metric), e.CompanyValue, e.PeerMedian, relativeToMedian(e)))
			}
		}
	}
	if snapshot.DivergenceDetected {
		sb.WriteString("Divergensi fundamental terdeteksi: ya\n")
	}
	if snapshot.IsAnomaly {
		sb.WriteString("Anomali pergerakan terdeteksi: ya\n")
	}
	sb.WriteString("\nTulis ringkasan riset 2 paragraf singkat: paragraf pertama tentang sinyal dan pendorongnya, paragraf kedua tentang risiko dan hal yang perlu dipantau. " +
		"Rangkum, jangan mendaftar semua metrik; sebut paling banyak 4 angka terpenting, ditulis persis seperti di fakta. " +
		"Jelaskan mengapa skor peluang dan risiko berada di level tersebut berdasarkan metrik yang mendukung dan menekan.")
	return sb.String()
}

// groupedEvidence lays the scoring factors out by which score they move, so the
// model does not describe e.g. high liquidity (lower risk) as an opportunity driver.
func groupedEvidence(items []domain.EvidenceItem) string {
	sections := []struct {
		category, position, title string
	}{
		{"opportunity", "Supports", "Menaikkan skor peluang"},
		{"opportunity", "Weighs", "Menurunkan skor peluang"},
		{"risk", "Weighs", "Menaikkan skor risiko"},
		{"risk", "Supports", "Menurunkan skor risiko"},
		{"opportunity", "Neutral", "Netral (peluang)"},
		{"risk", "Neutral", "Netral (risiko)"},
	}
	var sb strings.Builder
	for _, sec := range sections {
		var lines []string
		for _, e := range items {
			if e.Category == sec.category && e.Position == sec.position {
				lines = append(lines, fmt.Sprintf("  * %s: %s (pembanding %s)", e.Metric, e.CompanyValue, e.PeerMedian))
			}
		}
		if len(lines) > 0 {
			sb.WriteString(sec.title + ":\n" + strings.Join(lines, "\n") + "\n")
		}
	}
	return sb.String()
}

// relativeToMedian states the comparison from the numbers themselves. The engine's
// Outperform/Underperform labels are not direction-aware (a volatility far above
// peers is labelled "Outperform"), and the model repeated them verbatim.
func relativeToMedian(e domain.EvidenceItem) string {
	switch e.Position {
	case "Supports":
		return "mendukung"
	case "Weighs":
		return "menekan"
	case "Neutral":
		return "netral"
	}
	var v, m float64
	if _, err := fmt.Sscanf(e.CompanyValue, "%g", &v); err != nil {
		return "posisi: " + e.Position
	}
	if _, err := fmt.Sscanf(e.PeerMedian, "%g", &m); err != nil {
		return "posisi: " + e.Position
	}
	switch {
	case v > m:
		return "di atas median"
	case v < m:
		return "di bawah median"
	default:
		return "setara median"
	}
}

// metricLabel turns engine metric codes into words the model can explain.
func metricLabel(code string) string {
	labels := map[string]string{
		"GROWTH_PROXY":       "Indikator pertumbuhan",
		"VALUATION_PROXY":    "Indikator valuasi",
		"INSTITUTIONAL_FLOW": "Arus dana institusi",
		"FORECAST_PROXY":     "Proyeksi return model",
		"VOL_20D":            "Volatilitas 20 hari (%, makin tinggi makin berisiko)",
	}
	if l, ok := labels[code]; ok {
		return l
	}
	return code
}

func (c *Client) synthesizeRuleBasedSummary(s *domain.IntelligenceSnapshot) string {
	// Do not invent a factor when the model found none — a filler like "stabilitas
	// indikator operasional" reads as a real positive signal with no evidence behind it,
	// which breaks the project's own anti-hallucination rule (every claim must trace back
	// to an actual factor/evidence item). State plainly when a side has nothing to report.
	var positiveSentence string
	if len(s.PositiveFactors) > 0 {
		positiveSentence = fmt.Sprintf("Pendorong utama sinyal ini mencakup %s.", strings.Join(s.PositiveFactors, ", "))
	} else {
		positiveSentence = "Tidak ditemukan faktor pendorong positif yang signifikan pada analisis saat ini."
	}

	var negativeSentence string
	if len(s.NegativeFactors) > 0 {
		negativeSentence = fmt.Sprintf("Di sisi kehati-hatian, pelaku riset perlu memantau %s.", strings.Join(s.NegativeFactors, ", "))
	} else {
		negativeSentence = "Tidak ada faktor risiko spesifik yang tercatat di luar volatilitas pasar pada umumnya."
	}

	var divNote string
	if s.DivergenceDetected {
		divNote = " Sistem juga mendeteksi adanya divergensi fundamental, di mana pergerakan harga atau valuasi memperlihatkan anomali relatif terhadap arah akumulasi data."
	}

	return fmt.Sprintf(
		"Berdasarkan engine intelijen pasar, emiten %s saat ini memperlihatkan sinyal %s dengan Skor Peluang %.1f/100 (Keyakinan %s) dan tingkat risiko %s. %s%s %s",
		s.Symbol, s.Direction, s.OpportunityScore, s.Confidence, s.RiskLevel, positiveSentence, divNote, negativeSentence,
	)
}
