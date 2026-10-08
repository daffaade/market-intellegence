package llm

import "testing"

func TestValidateSummary(t *testing.T) {
	facts := "Skor Peluang: 57.2 / 100\nForecast H+7 positive (+0.55%)\nVolatilitas 20 hari (%): emiten 20.99 vs median peer 21.82"
	cases := []struct {
		name    string
		summary string
		ok      bool
	}{
		{"grounded numbers, comma decimal", "Skor peluang BBCA 57,2 dari 100 dengan proyeksi H+7 sebesar 0,55%.", true},
		{"sales word is not advice", "Penjualan dan volatilitas 20,99% berada di bawah median 21,82%.", true},
		{"invented number", "Laba tumbuh 12,5% tahun ini.", false},
		{"buy advice", "Saham ini layak untuk dibeli, investor bisa beli sekarang.", false},
		{"hold advice", "Investor sebaiknya tahan posisi.", false},
		{"empty", "  ", false},
	}
	for _, c := range cases {
		if err := validateSummary(c.summary, facts); (err == nil) != c.ok {
			t.Errorf("%s: got err=%v, want ok=%v", c.name, err, c.ok)
		}
	}
}
