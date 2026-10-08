package memory

import (
	"time"

	"be/internal/domain"
)

func (r *MemoryRepository) seedInitialData() {
	now := time.Now()

	// 1. Seed 18 IDX Companies
	companies := []*domain.Company{
		{Symbol: "BBCA", Name: "Bank Central Asia Tbk", Sector: "Financials", SubSector: "Banks", MarketCap: 1150000000000000, UpdatedAt: now},
		{Symbol: "BBRI", Name: "Bank Rakyat Indonesia Tbk", Sector: "Financials", SubSector: "Banks", MarketCap: 720000000000000, UpdatedAt: now},
		{Symbol: "BMRI", Name: "Bank Mandiri Tbk", Sector: "Financials", SubSector: "Banks", MarketCap: 650000000000000, UpdatedAt: now},
		{Symbol: "BBNI", Name: "Bank Negara Indonesia Tbk", Sector: "Financials", SubSector: "Banks", MarketCap: 198000000000000, UpdatedAt: now},
		{Symbol: "TLKM", Name: "Telkom Indonesia Tbk", Sector: "Telecommunication", SubSector: "Wireless Telecom", MarketCap: 345000000000000, UpdatedAt: now},
		{Symbol: "ASII", Name: "Astra International Tbk", Sector: "Consumer Discretionary", SubSector: "Automotive & Heavy Equipment", MarketCap: 210000000000000, UpdatedAt: now},
		{Symbol: "ICBP", Name: "Indofood CBP Sukses Makmur Tbk", Sector: "Consumer Staples", SubSector: "Packaged Foods", MarketCap: 135000000000000, UpdatedAt: now},
		{Symbol: "UNVR", Name: "Unilever Indonesia Tbk", Sector: "Consumer Staples", SubSector: "Personal Products", MarketCap: 92000000000000, UpdatedAt: now},
		{Symbol: "CPIN", Name: "Charoen Pokphand Indonesia Tbk", Sector: "Consumer Staples", SubSector: "Poultry & Feeds", MarketCap: 85000000000000, UpdatedAt: now},
		{Symbol: "ADRO", Name: "Adaro Energy Indonesia Tbk", Sector: "Energy", SubSector: "Thermal Coal", MarketCap: 112000000000000, UpdatedAt: now},
		{Symbol: "PTBA", Name: "Bukit Asam Tbk", Sector: "Energy", SubSector: "Thermal Coal", MarketCap: 32000000000000, UpdatedAt: now},
		{Symbol: "AMMN", Name: "Amman Mineral Internasional Tbk", Sector: "Basic Materials", SubSector: "Copper & Gold Mining", MarketCap: 580000000000000, UpdatedAt: now},
		{Symbol: "KLBF", Name: "Kalbe Farma Tbk", Sector: "Healthcare", SubSector: "Pharmaceuticals", MarketCap: 78000000000000, UpdatedAt: now},
		{Symbol: "PGAS", Name: "Perusahaan Gas Negara Tbk", Sector: "Utilities", SubSector: "Gas Distribution", MarketCap: 38000000000000, UpdatedAt: now},
		{Symbol: "GOTO", Name: "GoTo Gojek Tokopedia Tbk", Sector: "Technology", SubSector: "Internet & Digital Services", MarketCap: 75000000000000, UpdatedAt: now},
		{Symbol: "BUKA", Name: "Bukalapak.com Tbk", Sector: "Technology", SubSector: "Internet & Digital Services", MarketCap: 18000000000000, UpdatedAt: now},
		{Symbol: "ARTO", Name: "Bank Jago Tbk", Sector: "Financials", SubSector: "Digital Banks", MarketCap: 35000000000000, UpdatedAt: now},
		{Symbol: "EMTK", Name: "Elang Mahkota Teknologi Tbk", Sector: "Technology", SubSector: "Media & Tech Conglomerate", MarketCap: 28000000000000, UpdatedAt: now},
		{Symbol: "AMRT", Name: "Sumber Alfaria Trijaya Tbk", Sector: "Consumer Staples", SubSector: "Food & Staples Retailing", MarketCap: 130000000000000, UpdatedAt: now},
	}

	for _, c := range companies {
		r.companies[c.Symbol] = c
	}

	// 2. Seed Intelligence Snapshots for all companies
	snapshots := []*domain.IntelligenceSnapshot{
		{
			ID: 1, Symbol: "BBCA", OpportunityScore: 88.5, RiskScore: 15.2, Direction: "BULLISH", Confidence: "HIGH", RiskLevel: "LOW",
			IsAnomaly: true, AnomalyScore: 75.0, DivergenceDetected: true,
			PositiveFactors:   []string{"Kenaikan Net Interest Margin 15% YoY didorong pertumbuhan kredit konsumer", "Rasio CASA mencapai 81.2%, tertinggi di industri perbankan", "Return on Equity (ROE) superior di 21.5% vs peer median 14.2%"},
			NegativeFactors:   []string{"Valuasi PBV berada di persentil atas (4.8x)", "Pertumbuhan kredit korporasi melambat di 6.8% YoY"},
			SupportingFactors: []string{"Likuiditas solid (LDR 72.4%) memberi ruang ekspansi kredit", "Efisiensi operasional terdepan (CIR 34.1%)"},
			Evidence: []domain.EvidenceItem{
				{Metric: "ROAE", CompanyValue: "21.5%", PeerMedian: "14.2%", Position: "TOP_10_PERCENT"},
				{Metric: "Net Interest Margin", CompanyValue: "5.7%", PeerMedian: "4.8%", Position: "PREMIUM"},
				{Metric: "Cost to Income Ratio", CompanyValue: "34.1%", PeerMedian: "44.5%", Position: "TOP_10_PERCENT"},
				{Metric: "Price to Book Value", CompanyValue: "4.8x", PeerMedian: "2.1x", Position: "PREMIUM"},
			},
			WhatChanged: []domain.WhatChangedItem{
				{Metric: "NIM (QoQ)", Previous: "5.5%", Current: "5.7%", Delta: "+20 bps", Impact: "HIGH_BULLISH"},
				{Metric: "Net Foreign Flow (7D)", Previous: "-Rp 120B", Current: "+Rp 480B", Delta: "+Rp 600B", Impact: "HIGH_BULLISH"},
				{Metric: "Cost of Fund", Previous: "2.1%", Current: "1.9%", Delta: "-20 bps", Impact: "MODERATE_BULLISH"},
			},
			PeerComparison: []domain.PeerComparisonItem{
				{Metric: "PE Ratio", Target: "24.2x", PeerMedian: "12.8x", Position: "PREMIUM"},
				{Metric: "PBV Ratio", Target: "4.8x", PeerMedian: "2.1x", Position: "PREMIUM"},
				{Metric: "ROE", Target: "21.5%", PeerMedian: "14.2%", Position: "PREMIUM"},
				{Metric: "Dividend Yield", Target: "2.9%", PeerMedian: "4.1%", Position: "DISCOUNT"},
			},
			AIResearchSummary: "BBCA mempertahankan kepemimpinan kualitas aset perbankan Indonesia dengan CASA 81.2% dan ROE 21.5%. Meskipun diperdagangkan pada PBV premium 4.8x, divergensi positif terlihat dari aliran dana asing (+Rp 600B swing) dan efisiensi operasional tak tertandingi (CIR 34.1%).",
			Disclaimer:        "Informasi dan analisis ini merupakan hasil pemrosesan data riset dan bukan merupakan anjuran investasi personal (Bukan rekomendasi Beli/Jual).",
			SmartMoney: &domain.SmartMoneySnapshot{
				State: "Accumulation",
				Score: 0.55,
				Components: map[string]float64{
					"transaction_flow":      0.60,
					"cmf":                   0.45,
					"obv_trend":             0.65,
					"price_flow_divergence": 0.50,
				},
				Confidence: "high",
				Evidence: []string{
					"OBV meningkat 4 dari 5 hari terakhir",
					"CMF(20) = +0.22 menunjukkan tekanan beli institusi",
				},
			},
			Catalysts: &domain.CatalystSnapshot{
				CatalystScore: 0.65,
				NetDirection:  "Positive",
				Events: []domain.CatalystEvent{
					{
						Date:       now.Format("2006-01-02"),
						Type:       "volume_spike",
						Layer:      "market",
						Direction:  "Positive",
						Strength:   0.75,
						Confidence: "high",
						Evidence:   []string{"Volume perdagangan 2.1x rata-rata 60 hari"},
					},
				},
			},
			IsCached:          true, CreatedAt: now,
		},
		{
			ID: 2, Symbol: "BBRI", OpportunityScore: 86.2, RiskScore: 22.5, Direction: "BULLISH", Confidence: "HIGH", RiskLevel: "LOW",
			IsAnomaly: false, AnomalyScore: 28.0, DivergenceDetected: false,
			PositiveFactors:   []string{"Pertumbuhan segmen mikro & Kupedes melampaui 12% YoY", "Dividend yield atraktif 6.8% menjadi bantalan valuasi", "Penyaluran kredit UMKM mencapai 84% dari total portofolio"},
			NegativeFactors:   []string{"Kredit restrukturisasi pasca-pandemi masih memerlukan pencadangan bertahap", "Cost of Credit (CoC) berada di 3.2%"},
			SupportingFactors: []string{"Integrasi ekosistem Ultra Mikro (Pegadaian & PNM) terus memperluas nasabah baru"},
			Evidence: []domain.EvidenceItem{
				{Metric: "Dividend Yield", CompanyValue: "6.8%", PeerMedian: "4.1%", Position: "TOP_10_PERCENT"},
				{Metric: "NIM", CompanyValue: "7.8%", PeerMedian: "4.8%", Position: "PREMIUM"},
			},
			WhatChanged: []domain.WhatChangedItem{
				{Metric: "NPL Gross", Previous: "3.1%", Current: "2.95%", Delta: "-15 bps", Impact: "MODERATE_BULLISH"},
			},
			PeerComparison: []domain.PeerComparisonItem{
				{Metric: "PBV Ratio", Target: "2.3x", PeerMedian: "2.1x", Position: "FAIR"},
				{Metric: "ROE", Target: "18.8%", PeerMedian: "14.2%", Position: "PREMIUM"},
			},
			AIResearchSummary: "BBRI mencatatkan pertumbuhan kredit mikro yang solid didorong oleh ekspansi holding Ultra Mikro. Yield dividen 6.8% menawarkan proteksi downside yang sangat kuat bagi investor institusi.",
			Disclaimer:        "Bukan anjuran investasi personal.", IsCached: true, CreatedAt: now,
		},
		{
			ID: 3, Symbol: "BMRI", OpportunityScore: 84.0, RiskScore: 20.0, Direction: "BULLISH", Confidence: "HIGH", RiskLevel: "LOW",
			IsAnomaly: false, AnomalyScore: 22.0, DivergenceDetected: false,
			PositiveFactors:   []string{"Transformasi digital via Livin' dan Kopra mendorong pertumbuhan fee-based income +22% YoY", "Akselerasi kredit korporasi dan komersial tumbuh double-digit (14.5% YoY)", "Rasio NPL gross turun ke level terendah 1.15%"},
			NegativeFactors:   []string{"Sensitivitas terhadap fluktuasi nilai tukar modal kerja korporasi"},
			SupportingFactors: []string{"Coverage rasio pencadangan mencapai 315%, memberikan ruang mitigasi risiko optimal"},
			Evidence: []domain.EvidenceItem{
				{Metric: "NPL Gross", CompanyValue: "1.15%", PeerMedian: "2.40%", Position: "TOP_10_PERCENT"},
				{Metric: "ROE", CompanyValue: "19.2%", PeerMedian: "14.2%", Position: "PREMIUM"},
			},
			WhatChanged: []domain.WhatChangedItem{
				{Metric: "CASA Ratio", Previous: "75.2%", Current: "77.8%", Delta: "+260 bps", Impact: "HIGH_BULLISH"},
			},
			PeerComparison: []domain.PeerComparisonItem{
				{Metric: "PBV Ratio", Target: "2.2x", PeerMedian: "2.1x", Position: "FAIR"},
				{Metric: "ROE", Target: "19.2%", PeerMedian: "14.2%", Position: "PREMIUM"},
			},
			AIResearchSummary: "BMRI menunjukkan kepemimpinan di sektor korporasi dengan adopsi digital luar biasa. Kualitas aset superior dengan NPL 1.15% dan rasio pencadangan di atas 300% menegaskan status blue-chip yang sangat tangguh.",
			Disclaimer:        "Bukan anjuran investasi personal.", IsCached: true, CreatedAt: now,
		},
		{
			ID: 4, Symbol: "BBNI", OpportunityScore: 81.5, RiskScore: 24.0, Direction: "BULLISH", Confidence: "MEDIUM", RiskLevel: "LOW",
			IsAnomaly: false, AnomalyScore: 20.0, DivergenceDetected: false,
			PositiveFactors:   []string{"Transformasi segmen bisnis korporasi tier-1 dan diaspora banking", "Valuasi PBV 1.25x masih merupakan diskon signifikan terhadap Big 4", "Pertumbuhan laba bersih kuartalan +12.4% YoY"},
			NegativeFactors:   []string{"Rasio CASA (69.4%) masih di bawah peers perbankan buku IV lainnya"},
			SupportingFactors: []string{"Kualitas restrukturisasi portofolio kredit lama telah tuntas terkelola"},
			Evidence: []domain.EvidenceItem{
				{Metric: "PBV Ratio", CompanyValue: "1.25x", PeerMedian: "2.10%", Position: "DISCOUNT"},
			},
			WhatChanged: []domain.WhatChangedItem{
				{Metric: "ROE", Previous: "14.8%", Current: "15.6%", Delta: "+80 bps", Impact: "MODERATE_BULLISH"},
			},
			PeerComparison: []domain.PeerComparisonItem{
				{Metric: "PBV Ratio", Target: "1.25x", PeerMedian: "2.1x", Position: "DISCOUNT"},
			},
			AIResearchSummary: "BBNI menawarkan peluang re-rating valuasi tertinggi di antara perbankan Big 4 dengan PBV 1.25x di tengah percepatan profitabilitas dan modernisasi IT core banking.",
			Disclaimer:        "Bukan anjuran investasi personal.", IsCached: true, CreatedAt: now,
		},
		{
			ID: 5, Symbol: "TLKM", OpportunityScore: 78.4, RiskScore: 28.5, Direction: "BULLISH", Confidence: "HIGH", RiskLevel: "LOW",
			IsAnomaly: false, AnomalyScore: 35.0, DivergenceDetected: false,
			PositiveFactors:   []string{"Konsolidasi pasar FMC (Fixed-Mobile Convergence) IndiHome dan Telkomsel berjalan lancar", "Kapasitas Data Center HyperScale terus mencatatkan utilisasi di atas 85%", "Pertumbuhan trafik data +16.2% YoY"},
			NegativeFactors:   []string{"Kompetisi perang harga paket data seluler menekan ARPU ke Rp 44.500", "Beban belanja modal fiber optic dan spektrum frekuensi"},
			SupportingFactors: []string{"Monopoli infrastruktur backbone fiber optic nasional yang tak tertandingi"},
			Evidence: []domain.EvidenceItem{
				{Metric: "EBITDA Margin", CompanyValue: "52.4%", PeerMedian: "46.2%", Position: "TOP_10_PERCENT"},
			},
			WhatChanged: []domain.WhatChangedItem{
				{Metric: "Data Traffic", Previous: "4.8 PB", Current: "5.6 PB", Delta: "+16.2%", Impact: "HIGH_BULLISH"},
			},
			PeerComparison: []domain.PeerComparisonItem{
				{Metric: "EV/EBITDA", Target: "5.1x", PeerMedian: "5.8x", Position: "DISCOUNT"},
			},
			AIResearchSummary: "TLKM memegang pangsa pasar broadband dan seluler dominan di Indonesia. Meskipun ARPU tertekan jangka pendek, unit bisnis data center dan FMC menjadi katalis pertumbuhan jangka panjang yang kokoh.",
			Disclaimer:        "Bukan anjuran investasi personal.", IsCached: true, CreatedAt: now,
		},
		{
			ID: 6, Symbol: "AMMN", OpportunityScore: 76.0, RiskScore: 34.0, Direction: "BULLISH", Confidence: "HIGH", RiskLevel: "MODERATE",
			IsAnomaly: true, AnomalyScore: 68.0, DivergenceDetected: true,
			PositiveFactors:   []string{"Penyelesaian fasilitas smelter tembaga Sumbawa mencapai tahap commissioning 95%", "Harga tembaga dan emas global bertahan di tren bullish historis", "Kadar bijih (ore grade) fase 7 mencatatkan hasil ekstraksi di atas proyeksi"},
			NegativeFactors:   []string{"Ketergantungan pada izin ekspor konsentrat dan regulasi bea keluar mineral", "Rasio utang modal proyek tinggi"},
			SupportingFactors: []string{"Cadangan tembaga dan emas kelas dunia dengan masa tambang puluhan tahun"},
			Evidence: []domain.EvidenceItem{
				{Metric: "Gross Profit Margin", CompanyValue: "64.2%", PeerMedian: "28.5%", Position: "TOP_10_PERCENT"},
			},
			WhatChanged: []domain.WhatChangedItem{
				{Metric: "Copper Production", Previous: "84M lbs", Current: "112M lbs", Delta: "+33.3%", Impact: "HIGH_BULLISH"},
			},
			PeerComparison: []domain.PeerComparisonItem{
				{Metric: "EV/EBITDA", Target: "11.2x", PeerMedian: "8.5x", Position: "PREMIUM"},
			},
			AIResearchSummary: "AMMN diuntungkan oleh tailwind transisi energi global dan smelter tembaga yang segera beroperasi penuh. Anomali lonjakan produksi dan margin gross 64% menempatkan emiten ini di radar akumulasi institusi.",
			Disclaimer:        "Bukan anjuran investasi personal.", IsCached: true, CreatedAt: now,
		},
		{
			ID: 7, Symbol: "ICBP", OpportunityScore: 75.2, RiskScore: 26.0, Direction: "BULLISH", Confidence: "HIGH", RiskLevel: "LOW",
			IsAnomaly: false, AnomalyScore: 18.0, DivergenceDetected: false,
			PositiveFactors:   []string{"Volume penjualan mie instan domestik dan ekspor (Pinehill) tumbuh resilient", "Penurunan harga komoditas gandum dan CPO memperluas gross margin +180 bps", "Pricing power yang sangat dominan di segmen barang konsumsi pokok"},
			NegativeFactors:   []string{"Eksposur utang obligasi valas (USD) pasca akuisisi Pinehill Company"},
			SupportingFactors: []string{"Jaringan distribusi menjangkau seluruh pelosok nusantara hingga Afrika dan Timur Tengah"},
			Evidence: []domain.EvidenceItem{
				{Metric: "Operating Margin", CompanyValue: "20.8%", PeerMedian: "13.4%", Position: "PREMIUM"},
			},
			WhatChanged: []domain.WhatChangedItem{
				{Metric: "Gross Margin", Previous: "34.2%", Current: "36.0%", Delta: "+180 bps", Impact: "MODERATE_BULLISH"},
			},
			PeerComparison: []domain.PeerComparisonItem{
				{Metric: "PE Ratio", Target: "14.5x", PeerMedian: "18.2x", Position: "DISCOUNT"},
			},
			AIResearchSummary: "ICBP terus membuktikan status defensif terbaik di IDX dengan pricing power prima. Penurunan biaya bahan baku gandum dan valuasi PE 14.5x (diskon vs historis) menjadikannya pilihan konsumer paling menarik.",
			Disclaimer:        "Bukan anjuran investasi personal.", IsCached: true, CreatedAt: now,
		},
		{
			ID: 8, Symbol: "ASII", OpportunityScore: 72.8, RiskScore: 32.0, Direction: "NEUTRAL", Confidence: "MEDIUM", RiskLevel: "MODERATE",
			IsAnomaly: false, AnomalyScore: 25.0, DivergenceDetected: false,
			PositiveFactors:   []string{"Kontribusi bisnis alat berat (United Tractors) dan pertambangan emas tetap kuat", "Lini bisnis jasa keuangan (FIF, ACC) tumbuh sehat dengan NPL terkendali", "Yield dividen konsisten di kisaran 7-8%"},
			NegativeFactors:   []string{"Penjualan mobil domestik melemah 12% YoY di tengah penetrasi EV merek China", "Pangsa pasar roda empat turun tipis ke level 53%"},
			SupportingFactors: []string{"Diversifikasi portofolio ke sektor kesehatan dan infrastruktur tol"},
			Evidence: []domain.EvidenceItem{
				{Metric: "Dividend Yield", CompanyValue: "7.8%", PeerMedian: "4.1%", Position: "TOP_10_PERCENT"},
			},
			WhatChanged: []domain.WhatChangedItem{
				{Metric: "Auto Market Share", Previous: "55.4%", Current: "53.2%", Delta: "-220 bps", Impact: "MODERATE_BEARISH"},
			},
			PeerComparison: []domain.PeerComparisonItem{
				{Metric: "PE Ratio", Target: "6.8x", PeerMedian: "11.5x", Position: "DISCOUNT"},
			},
			AIResearchSummary: "ASII menghadapi tantangan persaingan EV di segmen otomotif, namun terlindungi oleh dividen yield 7.8% dan ketangguhan laba anak usaha pertambangan.",
			Disclaimer:        "Bukan anjuran investasi personal.", IsCached: true, CreatedAt: now,
		},
		{
			ID: 9, Symbol: "ADRO", OpportunityScore: 71.5, RiskScore: 36.0, Direction: "BULLISH", Confidence: "MEDIUM", RiskLevel: "MODERATE",
			IsAnomaly: false, AnomalyScore: 30.0, DivergenceDetected: false,
			PositiveFactors:   []string{"Kas bersih (net cash) melimpah mencapai lebih dari US$ 2.5 miliar", "Diversifikasi hilirisasi smelter aluminium Kaltara dan pembangkit EBT", "Pembagian dividen jumbo konsisten dengan payout di atas 60%"},
			NegativeFactors:   []string{"Volatilitas harga batu bara termal Newcastle yang berangsur normalisasi", "Risiko pajak karbon dan transisi ESG"},
			SupportingFactors: []string{"Biaya penambangan tunai (cash cost) terendah di kelasnya"},
			Evidence: []domain.EvidenceItem{
				{Metric: "Dividend Yield", CompanyValue: "11.2%", PeerMedian: "4.1%", Position: "TOP_10_PERCENT"},
			},
			WhatChanged: []domain.WhatChangedItem{
				{Metric: "Average Selling Price", Previous: "US$ 115/ton", Current: "US$ 98/ton", Delta: "-14.7%", Impact: "MODERATE_BEARISH"},
			},
			PeerComparison: []domain.PeerComparisonItem{
				{Metric: "PE Ratio", Target: "4.5x", PeerMedian: "7.2x", Position: "DISCOUNT"},
			},
			AIResearchSummary: "ADRO memiliki neraca kas yang sangat kokoh untuk mendanai transformasi hijau ke smelter aluminium tanpa mengorbankan komitmen dividen jumbo.",
			Disclaimer:        "Bukan anjuran investasi personal.", IsCached: true, CreatedAt: now,
		},
		{
			ID: 10, Symbol: "KLBF", OpportunityScore: 70.2, RiskScore: 25.0, Direction: "BULLISH", Confidence: "HIGH", RiskLevel: "LOW",
			IsAnomaly: false, AnomalyScore: 16.0, DivergenceDetected: false,
			PositiveFactors:   []string{"Permintaan obat resep dan produk nutrisi premium pulih kuat", "Ekspansi produk bioteknologi dan vaksin lokal Kalbe Genexine", "Pertumbuhan jaringan distribusi Enseval melayani lebih dari 1 juta outlet"},
			NegativeFactors:   []string{"Sebagian besar bahan baku aktif obat (API) masih diimpor dalam mata uang USD"},
			SupportingFactors: []string{"Kondisi keuangan bersih tanpa utang berbunga (zero-debt company)"},
			Evidence: []domain.EvidenceItem{
				{Metric: "ROE", CompanyValue: "15.8%", PeerMedian: "11.2%", Position: "PREMIUM"},
			},
			WhatChanged: []domain.WhatChangedItem{
				{Metric: "Prescription Drug Growth", Previous: "+6.2%", Current: "+11.4%", Delta: "+520 bps", Impact: "MODERATE_BULLISH"},
			},
			PeerComparison: []domain.PeerComparisonItem{
				{Metric: "PE Ratio", Target: "21.5x", PeerMedian: "24.0x", Position: "FAIR"},
			},
			AIResearchSummary: "KLBF mencatatkan pertumbuhan organik solid di seluruh lini usaha dengan neraca tanpa utang, menjadikannya standar emas sektor kesehatan Indonesia.",
			Disclaimer:        "Bukan anjuran investasi personal.", IsCached: true, CreatedAt: now,
		},
		{
			ID: 11, Symbol: "PTBA", OpportunityScore: 68.0, RiskScore: 35.0, Direction: "NEUTRAL", Confidence: "MEDIUM", RiskLevel: "MODERATE",
			IsAnomaly: false, AnomalyScore: 21.0, DivergenceDetected: false,
			PositiveFactors:   []string{"Volume angkutan kereta api Tanjung Enim ke Dermaga Kertapati meningkat", "Penjualan DMO ke PLN memberikan kepastian volume serapan", "Yield dividen BUMN tambang selalu di atas rata-rata"},
			NegativeFactors:   []string{"Keterbatasan infrastruktur jalur logistik kereta api di Sumatera", "Normalisasi harga batu bara kalori sedang"},
			SupportingFactors: []string{"Dukungan holding BUMN MIND ID"},
			Evidence: []domain.EvidenceItem{
				{Metric: "Dividend Yield", CompanyValue: "12.5%", PeerMedian: "4.1%", Position: "TOP_10_PERCENT"},
			},
			WhatChanged: []domain.WhatChangedItem{
				{Metric: "Railway Transport Vol", Previous: "28 Mt", Current: "32 Mt", Delta: "+14.2%", Impact: "MODERATE_BULLISH"},
			},
			PeerComparison: []domain.PeerComparisonItem{
				{Metric: "PE Ratio", Target: "5.8x", PeerMedian: "7.2x", Position: "DISCOUNT"},
			},
			AIResearchSummary: "PTBA adalah penghasil dividen tinggi yang mengandalkan stabilitas serapan pasar domestik PLN dan penambahan kapasitas angkutan kereta api.",
			Disclaimer:        "Bukan anjuran investasi personal.", IsCached: true, CreatedAt: now,
		},
		{
			ID: 12, Symbol: "PGAS", OpportunityScore: 68.0, RiskScore: 32.0, Direction: "BULLISH", Confidence: "MEDIUM", RiskLevel: "MODERATE",
			IsAnomaly: false, AnomalyScore: 19.0, DivergenceDetected: false,
			PositiveFactors:   []string{"Penyelesaian pipa gas transmisi Cirebon-Semarang (Cisem) tahap II", "Volume niaga dan transmisi gas industri tumbuh stabil", "Valuasi PBV 0.85x dan dividen yield konsisten di atas 8%"},
			NegativeFactors:   []string{"Kebijakan Harga Gas Bumi Tertentu (HGBT) membatasi marjin gas industri tertentu"},
			SupportingFactors: []string{"Peran strategis dalam transisi energi gas bumi nasional"},
			Evidence: []domain.EvidenceItem{
				{Metric: "Dividend Yield", CompanyValue: "8.4%", PeerMedian: "4.1%", Position: "PREMIUM"},
			},
			WhatChanged: []domain.WhatChangedItem{
				{Metric: "Gas Transmission Vol", Previous: "1,240 BBTUD", Current: "1,310 BBTUD", Delta: "+5.6%", Impact: "MODERATE_BULLISH"},
			},
			PeerComparison: []domain.PeerComparisonItem{
				{Metric: "PBV Ratio", Target: "0.85x", PeerMedian: "1.20x", Position: "DISCOUNT"},
			},
			AIResearchSummary: "PGAS menawarkan dividen menarik dengan valuasi di bawah nilai buku di tengah ekspansi jaringan transmisi gas nasional.",
			Disclaimer:        "Bukan anjuran investasi personal.", IsCached: true, CreatedAt: now,
		},
		{
			ID: 13, Symbol: "UNVR", OpportunityScore: 52.0, RiskScore: 38.0, Direction: "NEUTRAL", Confidence: "MEDIUM", RiskLevel: "MODERATE",
			IsAnomaly: false, AnomalyScore: 24.0, DivergenceDetected: false,
			PositiveFactors:   []string{"Program transformasi channel dan penataan inventori ritel modern", "Pangsa pasar produk perawatan pribadi inti masih bertahan kuat", "Payout ratio dividen hampir 100%"},
			NegativeFactors:   []string{"Persaingan ketat dari brand lokal yang lebih terjangkau", "Pertumbuhan penjualan domestik masih flat"},
			SupportingFactors: []string{"Brand awareness yang sudah mengakar di konsumen Indonesia"},
			Evidence: []domain.EvidenceItem{
				{Metric: "ROE", CompanyValue: "85.2%", PeerMedian: "13.4%", Position: "TOP_10_PERCENT"},
			},
			WhatChanged: []domain.WhatChangedItem{
				{Metric: "Domestic Sales Growth", Previous: "-1.5%", Current: "+0.8%", Delta: "+230 bps", Impact: "MODERATE_BULLISH"},
			},
			PeerComparison: []domain.PeerComparisonItem{
				{Metric: "PE Ratio", Target: "22.5x", PeerMedian: "18.2x", Position: "PREMIUM"},
			},
			AIResearchSummary: "UNVR sedang menjalani proses restrukturisasi strategi pasar guna merebut kembali momentum pertumbuhan dari brand lokal yang agresif.",
			Disclaimer:        "Bukan anjuran investasi personal.", IsCached: true, CreatedAt: now,
		},
		{
			ID: 14, Symbol: "CPIN", OpportunityScore: 66.5, RiskScore: 30.0, Direction: "BULLISH", Confidence: "MEDIUM", RiskLevel: "MODERATE",
			IsAnomaly: false, AnomalyScore: 22.0, DivergenceDetected: false,
			PositiveFactors:   []string{"Program culling unggas pemerintah membantu menjaga stabilitas harga ayam hidup (livebird)", "Permintaan pakan ternak pulih seiring pertumbuhan peternak mandiri", "Efisiensi pabrik pakan dan bibit DOC terdepan"},
			NegativeFactors:   []string{"Harga jagung lokal dan bungkil kedelai impor fluktuatif"},
			SupportingFactors: []string{"Pangsa pasar pakan ternak nomor satu di Indonesia"},
			Evidence: []domain.EvidenceItem{
				{Metric: "Market Share Poultry Feed", CompanyValue: "35%", PeerMedian: "12%", Position: "TOP_10_PERCENT"},
			},
			WhatChanged: []domain.WhatChangedItem{
				{Metric: "Livebird Price", Previous: "Rp 18,500/kg", Current: "Rp 21,200/kg", Delta: "+14.6%", Impact: "HIGH_BULLISH"},
			},
			PeerComparison: []domain.PeerComparisonItem{
				{Metric: "PE Ratio", Target: "24.8x", PeerMedian: "22.0x", Position: "FAIR"},
			},
			AIResearchSummary: "CPIN memimpin sektor perunggasan nasional dengan efisiensi integrasi hulu ke hilir yang kokoh.",
			Disclaimer:        "Bukan anjuran investasi personal.", IsCached: true, CreatedAt: now,
		},
		{
			ID: 15, Symbol: "ARTO", OpportunityScore: 70.0, RiskScore: 58.0, Direction: "BULLISH", Confidence: "MEDIUM", RiskLevel: "HIGH",
			IsAnomaly: true, AnomalyScore: 65.0, DivergenceDetected: true,
			PositiveFactors:   []string{"Integrasi mendalam dengan aplikasi Gojek dan Tokopedia mendorong jumlah pengguna tembus 11 juta", "Penyaluran kredit digital via ekosistem tumbuh +38% YoY", "Cost of Fund rendah di kisaran 2.8%"},
			NegativeFactors:   []string{"Valuasi PBV tinggi (4.2x)", "Tingkat pembentukan NPL kredit digital perlu dimonitor ketat"},
			SupportingFactors: []string{"Kolaborasi baru dengan ekosistem FinTech dan wealth management"},
			Evidence: []domain.EvidenceItem{
				{Metric: "Loan Growth", CompanyValue: "38.2%", PeerMedian: "11.2%", Position: "TOP_10_PERCENT"},
			},
			WhatChanged: []domain.WhatChangedItem{
				{Metric: "Funding Users", Previous: "8.5M", Current: "11.2M", Delta: "+31.8%", Impact: "HIGH_BULLISH"},
			},
			PeerComparison: []domain.PeerComparisonItem{
				{Metric: "PBV Ratio", Target: "4.2x", PeerMedian: "2.1x", Position: "PREMIUM"},
			},
			AIResearchSummary: "ARTO mewakili pertumbuhan bank digital dengan akuisisi nasabah tercepat melalui sinergi ekosistem GoTo.",
			Disclaimer:        "Bukan anjuran investasi personal.", IsCached: true, CreatedAt: now,
		},
		{
			ID: 16, Symbol: "GOTO", OpportunityScore: 42.0, RiskScore: 68.4, Direction: "BEARISH", Confidence: "HIGH", RiskLevel: "CRITICAL",
			IsAnomaly: true, AnomalyScore: 82.0, DivergenceDetected: true,
			PositiveFactors:   []string{"Adjusted EBITDA berangsur mendekati impas (break-even)", "Kemitraan strategis dengan TikTok Shop menghasilkan pendapatan e-commerce fee bebas risiko inventori", "Efisiensi biaya server, logistik, dan insentif promosi berkurang signifikan"},
			NegativeFactors:   []string{"Arus keluar dana institusi asing yang agresif (-Rp 270B net sell)", "Net Profit Margin masih negatif (-12.4%)", "Pertumbuhan GTV melambat di tengah persaingan e-commerce"},
			SupportingFactors: []string{"Posisi kas dan setara kas masih memadai sekitar Rp 21 triliun"},
			Evidence: []domain.EvidenceItem{
				{Metric: "Net Profit Margin", CompanyValue: "-12.4%", PeerMedian: "2.1%", Position: "BOTTOM_10_PERCENT"},
				{Metric: "GTV Growth", CompanyValue: "8.5%", PeerMedian: "18.2%", Position: "DISCOUNT"},
			},
			WhatChanged: []domain.WhatChangedItem{
				{Metric: "Foreign Flow (30D)", Previous: "-Rp 50B", Current: "-Rp 320B", Delta: "-Rp 270B", Impact: "HIGH_BEARISH"},
				{Metric: "Adjusted EBITDA", Previous: "-Rp 450B", Current: "-Rp 95B", Delta: "+Rp 355B", Impact: "MODERATE_BULLISH"},
			},
			PeerComparison: []domain.PeerComparisonItem{
				{Metric: "Price to Sales", Target: "4.1x", PeerMedian: "3.2x", Position: "PREMIUM"},
			},
			AIResearchSummary: "GOTO menunjukkan divergensi fundamental di mana perbaikan operasional adjusted EBITDA belum mampu mengimbangi tekanan arus keluar modal institusi asing.",
			Disclaimer:        "Bukan anjuran investasi personal.", IsCached: true, CreatedAt: now,
		},
		{
			ID: 17, Symbol: "BUKA", OpportunityScore: 35.0, RiskScore: 72.0, Direction: "BEARISH", Confidence: "MEDIUM", RiskLevel: "CRITICAL",
			IsAnomaly: false, AnomalyScore: 45.0, DivergenceDetected: false,
			PositiveFactors:   []string{"Posisi kas bersih melebihi kapitalisasi pasar perusahaan (Negative Enterprise Value)", "Pendapatan bunga dari penempatan deposito kas mendukung bottom line"},
			NegativeFactors:   []string{"Pertumbuhan transaksi inti Mitra Bukalapak melambat", "Monetisasi marketplace menghadapi persaingan sangat sengit"},
			SupportingFactors: []string{"Tidak memiliki utang berbunga"},
			Evidence: []domain.EvidenceItem{
				{Metric: "Cash to Market Cap", CompanyValue: "115%", PeerMedian: "15%", Position: "TOP_10_PERCENT"},
			},
			WhatChanged: []domain.WhatChangedItem{
				{Metric: "TPV Growth", Previous: "+5.1%", Current: "-2.4%", Delta: "-750 bps", Impact: "HIGH_BEARISH"},
			},
			PeerComparison: []domain.PeerComparisonItem{
				{Metric: "Price to Book", Target: "0.65x", PeerMedian: "1.40x", Position: "DISCOUNT"},
			},
			AIResearchSummary: "BUKA diperdagangkan dengan diskon kas yang dalam namun pasar masih menunggu katalis pertumbuhan bisnis operasional yang jelas.",
			Disclaimer:        "Bukan anjuran investasi personal.", IsCached: true, CreatedAt: now,
		},
		{
			ID: 18, Symbol: "EMTK", OpportunityScore: 62.0, RiskScore: 55.0, Direction: "NEUTRAL", Confidence: "MEDIUM", RiskLevel: "MODERATE",
			IsAnomaly: false, AnomalyScore: 32.0, DivergenceDetected: false,
			PositiveFactors:   []string{"Pemulihan belanja iklan TV FTA (SCTV dan Indosiar)", "Pertumbuhan pelanggan berbayar platform streaming Vidio", "Portofolio investasi teknologi dan rumah sakit Omni"},
			NegativeFactors:   []string{"Valuasi portofolio teknologi anak usaha rentan terhadap suku bunga global"},
			SupportingFactors: []string{"Neraca tanpa utang dengan likuiditas tinggi"},
			Evidence: []domain.EvidenceItem{
				{Metric: "Vidio Paying Subscribers", CompanyValue: "4.5M", PeerMedian: "1.2M", Position: "TOP_10_PERCENT"},
			},
			WhatChanged: []domain.WhatChangedItem{
				{Metric: "FTA Audience Share", Previous: "28.5%", Current: "31.2%", Delta: "+270 bps", Impact: "MODERATE_BULLISH"},
			},
			PeerComparison: []domain.PeerComparisonItem{
				{Metric: "PBV Ratio", Target: "1.1x", PeerMedian: "1.4x", Position: "FAIR"},
			},
			AIResearchSummary: "EMTK mempertahankan dominasi siaran TV FTA nasional dengan opsi pertumbuhan menarik dari platform streaming Vidio.",
			Disclaimer:        "Bukan anjuran investasi personal.", IsCached: true, CreatedAt: now,
		},
		{
			ID: 19, Symbol: "AMRT", OpportunityScore: 78.0, RiskScore: 24.0, Direction: "BULLISH", Confidence: "HIGH", RiskLevel: "LOW",
			IsAnomaly: false, AnomalyScore: 15.0, DivergenceDetected: false,
			PositiveFactors:   []string{"Penambahan lebih dari 1.000 gerai Alfamart per tahun di luar Jawa", "Pertumbuhan Same-Store Sales Growth (SSSG) solid di +7.5%", "Ekspansi fee-based income dari transaksi layanan digital"},
			NegativeFactors:   []string{"Kenaikan upah minimum regional (UMR) di beberapa wilayah operasional utama"},
			SupportingFactors: []string{"Dominasi segmen minimarket convenience store yang tidak tergantikan"},
			Evidence: []domain.EvidenceItem{
				{Metric: "ROAE", CompanyValue: "28.4%", PeerMedian: "14.2%", Position: "TOP_10_PERCENT"},
			},
			WhatChanged: []domain.WhatChangedItem{
				{Metric: "SSSG", Previous: "+5.8%", Current: "+7.5%", Delta: "+170 bps", Impact: "MODERATE_BULLISH"},
			},
			PeerComparison: []domain.PeerComparisonItem{
				{Metric: "PE Ratio", Target: "28.5x", PeerMedian: "18.2x", Position: "PREMIUM"},
			},
			AIResearchSummary: "AMRT membuktikan ketahanan model bisnis minimarket jaringan terluas dengan ROE superior di atas 28%.",
			Disclaimer:        "Bukan anjuran investasi personal.", IsCached: true, CreatedAt: now,
		},
	}

	for _, s := range snapshots {
		r.snapshots[s.Symbol] = s
	}

	// 3. Seed Growth Timeline (12 Months)
	r.growthTimeline = []domain.MarketGrowthTimelinePoint{
		{"period": "Okt 25", "BBCA": 76.5, "BBRI": 74.0, "BMRI": 71.2, "BBNI": 68.5, "TLKM": 69.0, "AMMN": 62.4, "ICBP": 70.1, "ASII": 65.8, "ADRO": 60.2, "KLBF": 64.0},
		{"period": "Nov 25", "BBCA": 78.2, "BBRI": 75.8, "BMRI": 73.0, "BBNI": 70.1, "TLKM": 70.5, "AMMN": 64.8, "ICBP": 71.0, "ASII": 66.5, "ADRO": 62.5, "KLBF": 65.2},
		{"period": "Des 25", "BBCA": 80.0, "BBRI": 77.5, "BMRI": 74.8, "BBNI": 71.9, "TLKM": 71.8, "AMMN": 67.0, "ICBP": 71.5, "ASII": 68.0, "ADRO": 64.0, "KLBF": 66.0},
		{"period": "Jan 26", "BBCA": 82.4, "BBRI": 79.2, "BMRI": 76.5, "BBNI": 73.8, "TLKM": 73.2, "AMMN": 69.5, "ICBP": 72.8, "ASII": 69.2, "ADRO": 66.1, "KLBF": 66.8},
		{"period": "Feb 26", "BBCA": 83.9, "BBRI": 80.6, "BMRI": 78.1, "BBNI": 75.2, "TLKM": 74.0, "AMMN": 71.0, "ICBP": 73.4, "ASII": 68.5, "ADRO": 67.8, "KLBF": 67.5},
		{"period": "Mar 26", "BBCA": 85.1, "BBRI": 82.0, "BMRI": 79.5, "BBNI": 76.9, "TLKM": 75.5, "AMMN": 72.8, "ICBP": 74.0, "ASII": 70.1, "ADRO": 69.2, "KLBF": 68.3},
		{"period": "Apr 26", "BBCA": 84.5, "BBRI": 81.2, "BMRI": 80.2, "BBNI": 77.5, "TLKM": 74.8, "AMMN": 73.5, "ICBP": 73.2, "ASII": 69.4, "ADRO": 70.0, "KLBF": 68.9},
		{"period": "Mei 26", "BBCA": 86.0, "BBRI": 83.1, "BMRI": 81.4, "BBNI": 78.8, "TLKM": 76.2, "AMMN": 74.2, "ICBP": 74.5, "ASII": 71.0, "ADRO": 68.5, "KLBF": 69.4},
		{"period": "Jun 26", "BBCA": 87.2, "BBRI": 84.5, "BMRI": 82.3, "BBNI": 79.9, "TLKM": 77.0, "AMMN": 75.0, "ICBP": 74.8, "ASII": 71.8, "ADRO": 70.4, "KLBF": 69.8},
		{"period": "Jul 26", "BBCA": 86.8, "BBRI": 85.0, "BMRI": 83.1, "BBNI": 80.5, "TLKM": 76.5, "AMMN": 75.5, "ICBP": 75.0, "ASII": 72.2, "ADRO": 71.0, "KLBF": 70.0},
		{"period": "Ags 26", "BBCA": 88.0, "BBRI": 85.8, "BMRI": 83.8, "BBNI": 81.0, "TLKM": 77.8, "AMMN": 75.8, "ICBP": 75.1, "ASII": 72.5, "ADRO": 71.2, "KLBF": 70.1},
		{"period": "Sep 26", "BBCA": 88.5, "BBRI": 86.2, "BMRI": 84.0, "BBNI": 81.5, "TLKM": 78.4, "AMMN": 76.0, "ICBP": 75.2, "ASII": 72.8, "ADRO": 71.5, "KLBF": 70.2},
	}

	// 4. Seed Pipeline Telemetry
	r.pipelineTelemetry = &domain.PipelineTelemetry{
		PipelineStatus:  "HEALTHY",
		TotalDurationMs: 982,
		Stages: []domain.PipelineStage{
			{
				ID:          domain.StageRetrieval,
				Label:       "Data Retrieval",
				Description: "Mengambil data mentah dari Sectors API / MCP: valuasi, peers, forecast, transaksi institusi, ownership, executives.",
				Status:      "COMPLETED",
				DataType:    "Raw Data (JSON)",
				DurationMs:  245,
			},
			{
				ID:          domain.StageValidation,
				Label:       "Validation & Cleaning",
				Description: "Memvalidasi kelengkapan field, menghapus duplikasi, dan mendeteksi data outlier atau null values.",
				Status:      "COMPLETED",
				DataType:    "Validated Data",
				DurationMs:  82,
			},
			{
				ID:          domain.StageNormalization,
				Label:       "Normalization",
				Description: "Menormalisasi skala metrik ke range 0-100, menyeragamkan satuan mata uang, dan mengonversi timestamp ke zona waktu WIB.",
				Status:      "COMPLETED",
				DataType:    "Normalized Data",
				DurationMs:  45,
			},
			{
				ID:          domain.StageTransformation,
				Label:       "Transformation",
				Description: "Menghitung delta antar-periode (YoY, QoQ), menghitung rasio perbandingan peer median, dan memproduksi perubahan signifikan.",
				Status:      "COMPLETED",
				DataType:    "Derived Metrics",
				DurationMs:  120,
			},
			{
				ID:          domain.StageFeatureGeneration,
				Label:       "Feature Generation",
				Description: "Membentuk fitur analitis: anomaly score, divergence flag, composite opportunity/risk score, dan peer position ranking.",
				Status:      "COMPLETED",
				DataType:    "Intelligence Features",
				DurationMs:  180,
			},
			{
				ID:          domain.StageIntelligenceEngine,
				Label:       "Intelligence Engine",
				Description: "Menjalankan engine intelijen untuk menghasilkan sinyal, menentukan direction & confidence, dan menyusun AI research summary.",
				Status:      "COMPLETED",
				DataType:    "Intelligence Output + AI Narrative",
				DurationMs:  310,
			},
		},
	}

	// 5. Seed Macro Indicators & Disaster Risks
	r.macroIndicators = []domain.MacroIndicator{
		{Name: "BI Rate (Suku Bunga Acuan)", Value: "6.00%", Trend: "STABLE", CorrelationWithMarket: "Positif untuk marjin perbankan", ImpactAssessment: "Net Neutral to Positive"},
		{Name: "Inflasi YoY (CPI)", Value: "2.45%", Trend: "DOWN", CorrelationWithMarket: "Mendukung daya beli konsumer", ImpactAssessment: "Positive"},
		{Name: "Nilai Tukar USD/IDR", Value: "15,820", Trend: "STABLE", CorrelationWithMarket: "Stabilitas modal asing", ImpactAssessment: "Neutral"},
		{Name: "Pertumbuhan PDB Nasional", Value: "5.12%", Trend: "UP", CorrelationWithMarket: "Pendorong kredit & investasi", ImpactAssessment: "Highly Positive"},
	}

	r.disasterRisks = []domain.DisasterRisk{
		{Region: "Pesisir Jawa Barat & Banten", RiskType: "Cuaca Ekstrem & Banjir", Severity: "MEDIUM", ImpactedOperations: "Jaringan Cabang & ATM Retail", MitigationStatus: "Mitigasi Aktif (Redundansi Sistem Data Center)"},
		{Region: "Sumatera Bagian Tengah", RiskType: "Kabut Asap Karhutla", Severity: "LOW", ImpactedOperations: "Operasional Logistik & Cabang Regional", MitigationStatus: "Sistem Kerja Hybrid Disiapkan"},
	}

	r.portfolioPositions = []domain.PortfolioPosition{
		{Symbol: "BBCA", Name: "Bank Central Asia", AllocationPct: 40.0, Sector: "Financials", RiskScore: 15.2, OpportunityScore: 88.5},
		{Symbol: "TLKM", Name: "Telkom Indonesia", AllocationPct: 25.0, Sector: "Telecommunication", RiskScore: 28.5, OpportunityScore: 74.2},
		{Symbol: "ASII", Name: "Astra International", AllocationPct: 20.0, Sector: "Consumer Discretionary", RiskScore: 32.0, OpportunityScore: 65.0},
		{Symbol: "GOTO", Name: "GoTo Tokopedia", AllocationPct: 15.0, Sector: "Technology", RiskScore: 68.4, OpportunityScore: 42.0},
	}
}
