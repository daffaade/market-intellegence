import type {
  Company,
  IntelligenceSnapshot,
  MarketOverview,
  GrowthData,
  DividendHistory,
  Shareholder,
  KeyExecutive,
  SmartMoneyTransaction,
  MacroIndicator,
  EventImpact,
  DisasterRisk,
  PortfolioPosition,
  SignalMatrixPoint,
  PipelineStage,
  StandardizedSignalOutput
} from '../types/api';

export const MOCK_COMPANIES: Record<string, Company> = {
  BBCA: {
    symbol: "BBCA",
    name: "Bank Central Asia Tbk",
    sector: "Financials",
    sub_sector: "Banks",
    market_cap: 1150000000000000,
    updated_at: "2026-09-20T18:00:00Z"
  },
  TLKM: {
    symbol: "TLKM",
    name: "Telkom Indonesia Tbk",
    sector: "Telecommunication",
    sub_sector: "Wireless Telecom",
    market_cap: 345000000000000,
    updated_at: "2026-09-20T18:00:00Z"
  },
  ASII: {
    symbol: "ASII",
    name: "Astra International Tbk",
    sector: "Consumer Discretionary",
    sub_sector: "Automotive & Heavy Equipment",
    market_cap: 210000000000000,
    updated_at: "2026-09-20T18:00:00Z"
  },
  UNVR: {
    symbol: "UNVR",
    name: "Unilever Indonesia Tbk",
    sector: "Consumer Staples",
    sub_sector: "Personal Products",
    market_cap: 92000000000000,
    updated_at: "2026-09-20T18:00:00Z"
  },
  GOTO: {
    symbol: "GOTO",
    name: "GoTo Gojek Tokopedia Tbk",
    sector: "Technology",
    sub_sector: "Internet & Digital Services",
    market_cap: 75000000000000,
    updated_at: "2026-09-20T18:00:00Z"
  },
  BBRI: {
    symbol: "BBRI",
    name: "Bank Rakyat Indonesia Tbk",
    sector: "Financials",
    sub_sector: "Banks",
    market_cap: 720000000000000,
    updated_at: "2026-09-20T18:00:00Z"
  },
  BMRI: {
    symbol: "BMRI",
    name: "Bank Mandiri Tbk",
    sector: "Financials",
    sub_sector: "Banks",
    market_cap: 650000000000000,
    updated_at: "2026-09-20T18:00:00Z"
  },
  BUKA: {
    symbol: "BUKA",
    name: "Bukalapak.com Tbk",
    sector: "Technology",
    sub_sector: "Internet & Digital Services",
    market_cap: 18000000000000,
    updated_at: "2026-09-20T18:00:00Z"
  },
  ARTO: {
    symbol: "ARTO",
    name: "Bank Jago Tbk",
    sector: "Financials",
    sub_sector: "Banks",
    market_cap: 35000000000000,
    updated_at: "2026-09-20T18:00:00Z"
  },
  EMTK: {
    symbol: "EMTK",
    name: "Elang Mahkota Teknologi Tbk",
    sector: "Technology",
    sub_sector: "Internet & Digital Services",
    market_cap: 28000000000000,
    updated_at: "2026-09-20T18:00:00Z"
  }
};

export const MOCK_INTELLIGENCE: Record<string, IntelligenceSnapshot> = {
  BBCA: {
    id: 1,
    symbol: "BBCA",
    opportunity_score: 88.5,
    risk_score: 15.2,
    direction: "BULLISH",
    confidence: "HIGH",
    risk_level: "LOW",
    is_anomaly: true,
    anomaly_score: 75.0,
    divergence_detected: true,
    positive_factors: [
      "Kenaikan Net Interest Margin 15% YoY didorong pertumbuhan kredit konsumer",
      "Net Foreign Buy mencapai Rp 500 Miliar minggu ini secara berkelanjutan",
      "Rasio NPL terjaga di 1.8% (jauh di bawah rerata industri 2.6%)",
      "Efisiensi digital banking menekan Cost to Income Ratio (CIR) ke 34%"
    ],
    negative_factors: [
      "Valuasi PBV (4.8x) berada di atas rata-rata 5 tahun (4.2x)",
      "Potensi moderasi margin jika Bank Indonesia memangkas suku bunga"
    ],
    supporting_factors: [
      "Sektor perbankan nasional tumbuh positif 11.2% YoY",
      "Likuiditas pasar modal solid dengan inflow investor domestik"
    ],
    evidence: [
      {
        metric: "ROAE",
        company_value: "21.5%",
        peer_median: "14.2%",
        position: "TOP_10_PERCENT"
      },
      {
        metric: "Net Interest Margin (NIM)",
        company_value: "5.7%",
        peer_median: "4.8%",
        position: "PREMIUM"
      },
      {
        metric: "Cost to Income Ratio",
        company_value: "34.1%",
        peer_median: "44.5%",
        position: "TOP_10_PERCENT"
      },
      {
        metric: "Price to Book Value (PBV)",
        company_value: "4.8x",
        peer_median: "2.1x",
        position: "PREMIUM"
      }
    ],
    what_changed: [
      {
        metric: "Foreign Accumulation",
        previous: "Net Sell 100B",
        current: "Net Buy 500B",
        delta: "+600B",
        impact: "HIGH_BULLISH"
      },
      {
        metric: "CASA Ratio",
        previous: "79.8%",
        current: "81.4%",
        delta: "+1.6%",
        impact: "MODERATE_BULLISH"
      },
      {
        metric: "Loan Growth YoY",
        previous: "10.5%",
        current: "14.2%",
        delta: "+3.7%",
        impact: "HIGH_BULLISH"
      }
    ],
    peer_comparison: [
      {
        metric: "PER (Price Earnings)",
        target: "22.4x",
        peer_median: "15.1x",
        position: "PREMIUM"
      },
      {
        metric: "PBV (Price Book)",
        target: "4.8x",
        peer_median: "2.1x",
        position: "PREMIUM"
      },
      {
        metric: "Dividend Yield",
        target: "2.8%",
        peer_median: "4.5%",
        position: "DISCOUNT"
      }
    ],
    ai_research_summary: "BBCA memperlihatkan akumulasi agresif oleh investor asing (Net Buy Rp 500B) meskipun valuasinya berada pada persentil 90% secara historis. Terjadi fundamental divergence positif di mana marjin CASA meningkat pesat saat suku bunga tinggi. Efisiensi biaya operasional yang unggul menjaga ROAE di atas 21%, menjadikan emiten ini sinyal peluang bernilai tinggi dengan tingkat risiko terendah di sektor perbankan.",
    disclaimer: "Hasil analisis berbasis algoritma intelijen kuantitatif dan pemrosesan data historis. Bukan merupakan rekomendasi jual atau beli langsung.",
    is_cached: true,
    created_at: "2026-09-20T18:30:00Z"
  },
  TLKM: {
    id: 2,
    symbol: "TLKM",
    opportunity_score: 74.2,
    risk_score: 28.5,
    direction: "BULLISH",
    confidence: "HIGH",
    risk_level: "LOW",
    is_anomaly: false,
    anomaly_score: 32.0,
    divergence_detected: false,
    positive_factors: [
      "Pertumbuhan bisnis Data & Data Center (NeutraDC) naik 22% YoY",
      "Valuasi PER berada di bawah rerata 3 tahun (Discount 18%)",
      "Dividend yield stabil di kisaran 5.2%"
    ],
    negative_factors: [
      "Persaingan ketat harga paket data seluler di segmen retail",
      "Kenaikan beban depresiasi aset fixed broadband (IndiHome integration)"
    ],
    supporting_factors: [
      "Monetisasi infrastruktur 5G dan serat optik nasional"
    ],
    evidence: [
      {
        metric: "EBITDA Margin",
        company_value: "51.2%",
        peer_median: "46.0%",
        position: "PREMIUM"
      },
      {
        metric: "EV/EBITDA",
        company_value: "5.8x",
        peer_median: "6.5x",
        position: "DISCOUNT"
      }
    ],
    what_changed: [
      {
        metric: "Data ARPU",
        previous: "Rp 45,500",
        current: "Rp 48,200",
        delta: "+Rp 2,700",
        impact: "MODERATE_BULLISH"
      }
    ],
    peer_comparison: [
      {
        metric: "PER",
        target: "13.8x",
        peer_median: "16.5x",
        position: "DISCOUNT"
      },
      {
        metric: "PBV",
        target: "2.4x",
        peer_median: "2.8x",
        position: "DISCOUNT"
      }
    ],
    ai_research_summary: "TLKM saat ini berada dalam fase akumulasi fundamental di mana bisnis infrastruktur pusat data memberikan katalis pertumbuhan baru. Hambatan persaingan seluler dapat terkompensasi oleh marjin EBITDA yang solid di atas 50%.",
    disclaimer: "Hasil analisis berbasis algoritma intelijen dan sanad data historis.",
    is_cached: true,
    created_at: "2026-09-20T18:30:00Z"
  },
  GOTO: {
    id: 3,
    symbol: "GOTO",
    opportunity_score: 42.0,
    risk_score: 68.4,
    direction: "BEARISH",
    confidence: "MEDIUM",
    risk_level: "HIGH",
    is_anomaly: true,
    anomaly_score: 82.5,
    divergence_detected: true,
    positive_factors: [
      "Adjusted EBITDA grup mendekati break-even",
      "Kemitraan strategis dengan TikTok E-Commerce memperkuat posisi GTV"
    ],
    negative_factors: [
      "Beban insentif pengguna masih menekan bottom-line",
      "Tekanan jual institusi asing dalam 30 hari terakhir"
    ],
    supporting_factors: [
      "Sektor teknologi regional belum menunjukkan pemulihan valuasi secara meluas"
    ],
    evidence: [
      {
        metric: "Net Profit Margin",
        company_value: "-12.4%",
        peer_median: "2.1%",
        position: "BOTTOM_10_PERCENT"
      },
      {
        metric: "GTV Growth",
        company_value: "8.5%",
        peer_median: "18.2%",
        position: "DISCOUNT"
      }
    ],
    what_changed: [
      {
        metric: "Institutional Outflow",
        previous: "Net Sell 50B",
        current: "Net Sell 320B",
        delta: "-270B",
        impact: "HIGH_BEARISH"
      }
    ],
    peer_comparison: [
      {
        metric: "Price to Sales (P/S)",
        target: "4.1x",
        peer_median: "3.2x",
        position: "PREMIUM"
      }
    ],
    ai_research_summary: "GOTO terdeteksi mengalami Fundamental Divergence di mana indikator perbaikan EBITDA operasional direspon negatif oleh arus kas asing yang keluar secara beruntun. Tingkat risiko tergolong tinggi hingga ada kepastian profitability penuh.",
    disclaimer: "Bukan rekomendasi jual/beli.",
    is_cached: false,
    created_at: "2026-09-20T18:30:00Z"
  }
};

export const MOCK_MARKET_OVERVIEW: MarketOverview = {
  top_opportunities: [
    MOCK_INTELLIGENCE.BBCA,
    MOCK_INTELLIGENCE.TLKM
  ],
  top_risks: [
    MOCK_INTELLIGENCE.GOTO
  ],
  detected_anomalies: [
    MOCK_INTELLIGENCE.BBCA,
    MOCK_INTELLIGENCE.GOTO
  ],
  sector_summary: [
    {
      sector: "Financials",
      sentiment: "Bullish",
      avg_opportunity: 85.5,
      anomaly_count: 1
    },
    {
      sector: "Telecommunication",
      sentiment: "Bullish",
      avg_opportunity: 74.2,
      anomaly_count: 0
    },
    {
      sector: "Consumer Staples",
      sentiment: "Neutral",
      avg_opportunity: 62.0,
      anomaly_count: 0
    },
    {
      sector: "Consumer Discretionary",
      sentiment: "Neutral",
      avg_opportunity: 58.4,
      anomaly_count: 0
    },
    {
      sector: "Technology",
      sentiment: "Bearish",
      avg_opportunity: 42.0,
      anomaly_count: 1
    }
  ]
};

export const MOCK_GROWTH_DATA: Record<string, GrowthData[]> = {
  BBCA: [
    { year: "2022", revenue: 87400, net_profit: 40700, margin: 46.5 },
    { year: "2023", revenue: 99800, net_profit: 48600, margin: 48.7 },
    { year: "2024", revenue: 112500, net_profit: 54800, margin: 48.7 },
    { year: "2025", revenue: 124800, net_profit: 61200, margin: 49.0 },
    { year: "2026 (F)", revenue: 138000, net_profit: 68500, margin: 49.6 }
  ],
  TLKM: [
    { year: "2022", revenue: 147300, net_profit: 25800, margin: 17.5 },
    { year: "2023", revenue: 149200, net_profit: 24500, margin: 16.4 },
    { year: "2024", revenue: 154800, net_profit: 26200, margin: 16.9 },
    { year: "2025", revenue: 161000, net_profit: 27900, margin: 17.3 },
    { year: "2026 (F)", revenue: 169500, net_profit: 29800, margin: 17.5 }
  ]
};

export const MOCK_DIVIDENDS: Record<string, DividendHistory[]> = {
  BBCA: [
    { year: "2022", dividend_per_share: 170, yield_percent: 2.1, payout_ratio: 51.4 },
    { year: "2023", dividend_per_share: 205, yield_percent: 2.3, payout_ratio: 52.0 },
    { year: "2024", dividend_per_share: 270, yield_percent: 2.7, payout_ratio: 60.5 },
    { year: "2025", dividend_per_share: 300, yield_percent: 2.9, payout_ratio: 60.2 }
  ]
};

export const MOCK_SHAREHOLDERS: Record<string, Shareholder[]> = {
  BBCA: [
    { name: "PT Dwimuria Investama Andalan", share_percentage: 54.94, category: "INSTITUTIONAL" },
    { name: "Masyarakat (Retail & Institutional)", share_percentage: 42.61, category: "RETAIL" },
    { name: "Direksi & Komisaris (Insider)", share_percentage: 2.45, category: "MANAGEMENT" }
  ]
};

export const MOCK_EXECUTIVES: Record<string, KeyExecutive[]> = {
  BBCA: [
    { name: "Jahja Setiaatmadja", position: "Presiden Direktur", tenure: "13 Tahun", insider_action: "BOUGHT", transaction_amount: "+500,000 lembar" },
    { name: "Armand Wahyudi Hartono", position: "Wakil Presiden Direktur", tenure: "10 Tahun", insider_action: "HELD" },
    { name: "Gregory Hendra Lembong", position: "Direktur IT & Digital Banking", tenure: "6 Tahun", insider_action: "BOUGHT", transaction_amount: "+150,000 lembar" }
  ]
};

export const MOCK_SMART_MONEY: Record<string, SmartMoneyTransaction[]> = {
  BBCA: [
    { date: "2026-09-18", institution: "BlackRock Institutional Fund", action: "ACCUMULATE", volume: "12,400,000", value_idr: "Rp 127.1 M" },
    { date: "2026-09-17", institution: "Vanguard Emerging Markets", action: "ACCUMULATE", volume: "8,900,000", value_idr: "Rp 91.2 M" },
    { date: "2026-09-15", institution: "JPMorgan Asset Mgmt", action: "ACCUMULATE", volume: "15,100,000", value_idr: "Rp 154.8 M" }
  ]
};

export const MOCK_MACRO: MacroIndicator[] = [
  { name: "BI Rate (Suku Bunga Acuan)", value: "6.00%", trend: "STABLE", correlation_with_market: "Positif untuk marjin perbankan", impact_assessment: "Net Neutral to Positive" },
  { name: "Inflasi YoY (CPI)", value: "2.45%", trend: "DOWN", correlation_with_market: "Mendukung daya beli konsumer", impact_assessment: "Positive" },
  { name: "Nilai Tukar USD/IDR", value: "15,820", trend: "STABLE", correlation_with_market: "Stabilitas modal asing", impact_assessment: "Neutral" },
  { name: "Pertumbuhan PDB Nasional", value: "5.12%", trend: "UP", correlation_with_market: "Pendorong kredit & investasi", impact_assessment: "Highly Positive" }
];

export const MOCK_EVENTS: EventImpact[] = [
  { event_name: "Pengumuman Pembagian Dividen Interim BBCA", date: "2026-08-25", category: "Corporate Action", price_reaction_pct: 2.8, market_sentiment: "Very Positive" },
  { event_name: "Rilis Laporan Keuangan Q2 2026 Perbankan", date: "2026-07-28", category: "Earnings", price_reaction_pct: 3.5, market_sentiment: "Positive" },
  { event_name: "Keputusan Suku Bunga Federal Reserve (Fed Rate)", date: "2026-09-12", category: "Macroeconomic", price_reaction_pct: -0.4, market_sentiment: "Neutral" }
];

export const MOCK_DISASTER_RISKS: DisasterRisk[] = [
  { region: "Pesisir Jawa Barat & Banten", risk_type: "Cuaca Ekstrem & Banjir", severity: "MEDIUM", impacted_operations: "Jaringan Cabang & ATM Retail", mitigation_status: "Mitigasi Aktif (Redundansi Sistem Data Center)" },
  { region: "Sumatera Bagian Tengah", risk_type: "Kabut Asap Karhutla", severity: "LOW", impacted_operations: "Operasional Logistik & Cabang Regional", mitigation_status: "Sistem Kerja Hybrid Disiapkan" }
];

export const MOCK_PORTFOLIO: PortfolioPosition[] = [
  { symbol: "BBCA", name: "Bank Central Asia", allocation_pct: 40.0, sector: "Financials", risk_score: 15.2, opportunity_score: 88.5 },
  { symbol: "TLKM", name: "Telkom Indonesia", allocation_pct: 25.0, sector: "Telecommunication", risk_score: 28.5, opportunity_score: 74.2 },
  { symbol: "ASII", name: "Astra International", allocation_pct: 20.0, sector: "Consumer Discretionary", risk_score: 32.0, opportunity_score: 65.0 },
  { symbol: "GOTO", name: "GoTo Tokopedia", allocation_pct: 15.0, sector: "Technology", risk_score: 68.4, opportunity_score: 42.0 }
];

// ─── Signal Matrix Points (2D Quadrant Data) ──────────────────
export const MOCK_SIGNAL_MATRIX: SignalMatrixPoint[] = [
  { symbol: "BBCA", name: "Bank Central Asia", sector: "Financials", opportunity_score: 88.5, risk_score: 15.2, direction: "BULLISH", is_anomaly: true, quadrant: "PRIME_VALUE" },
  { symbol: "BBRI", name: "Bank Rakyat Indonesia", sector: "Financials", opportunity_score: 82.0, risk_score: 22.5, direction: "BULLISH", is_anomaly: false, quadrant: "PRIME_VALUE" },
  { symbol: "TLKM", name: "Telkom Indonesia", sector: "Telecommunication", opportunity_score: 74.2, risk_score: 28.5, direction: "BULLISH", is_anomaly: false, quadrant: "PRIME_VALUE" },
  { symbol: "BMRI", name: "Bank Mandiri", sector: "Financials", opportunity_score: 78.0, risk_score: 20.0, direction: "BULLISH", is_anomaly: false, quadrant: "PRIME_VALUE" },
  { symbol: "ASII", name: "Astra International", sector: "Consumer Discretionary", opportunity_score: 65.0, risk_score: 32.0, direction: "NEUTRAL", is_anomaly: false, quadrant: "CONSERVATIVE" },
  { symbol: "UNVR", name: "Unilever Indonesia", sector: "Consumer Staples", opportunity_score: 52.0, risk_score: 38.0, direction: "NEUTRAL", is_anomaly: false, quadrant: "CONSERVATIVE" },
  { symbol: "GOTO", name: "GoTo Tokopedia", sector: "Technology", opportunity_score: 42.0, risk_score: 68.4, direction: "BEARISH", is_anomaly: true, quadrant: "WARNING_ZONE" },
  { symbol: "BUKA", name: "Bukalapak", sector: "Technology", opportunity_score: 35.0, risk_score: 72.0, direction: "BEARISH", is_anomaly: false, quadrant: "WARNING_ZONE" },
  { symbol: "ARTO", name: "Bank Jago", sector: "Financials", opportunity_score: 70.0, risk_score: 58.0, direction: "BULLISH", is_anomaly: true, quadrant: "HIGH_GROWTH" },
  { symbol: "EMTK", name: "Elang Mahkota", sector: "Technology", opportunity_score: 62.0, risk_score: 55.0, direction: "NEUTRAL", is_anomaly: false, quadrant: "HIGH_GROWTH" }
];

// ─── Sectors API / MCP Pipeline Stages ─────────────────────────
export const MOCK_PIPELINE_STAGES: PipelineStage[] = [
  {
    id: "RETRIEVAL",
    label: "Data Retrieval",
    description: "Mengambil data mentah dari Sectors API/MCP: valuasi, peers, forecast, transaksi institusi, ownership, executives.",
    status: "COMPLETED",
    data_type: "Raw Data (JSON)",
    duration_ms: 245
  },
  {
    id: "VALIDATION",
    label: "Validation & Cleaning",
    description: "Memvalidasi kelengkapan field, menghapus duplikasi, dan mendeteksi data outlier atau null values.",
    status: "COMPLETED",
    data_type: "Validated Data",
    duration_ms: 82
  },
  {
    id: "NORMALIZATION",
    label: "Normalization",
    description: "Menormalisasi skala metrik ke range 0-100, menyeragamkan satuan mata uang, dan mengonversi timestamp ke zona waktu WIB.",
    status: "COMPLETED",
    data_type: "Normalized Data",
    duration_ms: 45
  },
  {
    id: "TRANSFORMATION",
    label: "Transformation",
    description: "Menghitung delta antar-periode (YoY, QoQ), menghitung rasio perbandingan peer median, dan memproduksi perubahan signifikan.",
    status: "COMPLETED",
    data_type: "Derived Metrics",
    duration_ms: 120
  },
  {
    id: "FEATURE_GENERATION",
    label: "Feature Generation",
    description: "Membentuk fitur analitis: anomaly score, divergence flag, composite opportunity/risk score, dan peer position ranking.",
    status: "COMPLETED",
    data_type: "Intelligence Features",
    duration_ms: 180
  },
  {
    id: "INTELLIGENCE_ENGINE",
    label: "Intelligence Engine",
    description: "Menjalankan engine intelijen untuk menghasilkan sinyal, menentukan direction & confidence, dan menyusun AI research summary.",
    status: "COMPLETED",
    data_type: "Intelligence Output + AI Narrative",
    duration_ms: 310
  }
];

// ─── Standardized Signal Outputs ───────────────────────────────
export const MOCK_SIGNAL_OUTPUTS: Record<string, StandardizedSignalOutput> = {
  BBCA: {
    finding: "BBCA menunjukkan akumulasi institusi asing yang agresif (+Rp 600B net buy swing) bersamaan dengan ekspansi marjin CASA dan efisiensi CIR, meskipun valuasi historis sudah berada di persentil atas (PBV 4.8x vs median 2.1x). Pola ini menandakan fundamental divergence positif yang jarang terjadi.",
    score: {
      opportunity: 88.5,
      risk: 15.2,
      composite: 86.7
    },
    explanation: "Skor opportunity tinggi (88.5) didorong oleh kombinasi tiga faktor: (1) percepatan akumulasi modal asing yang konsisten selama 3 minggu berturut-turut, (2) ekspansi Net Interest Margin ke 5.7% yang mengalahkan 90% peer group, dan (3) efisiensi operasional superior dengan CIR 34.1% vs median industri 44.5%. Skor risk rendah (15.2) karena NPL terjaga di 1.8%, jauh di bawah ambang batas industri.",
    evidence: [
      { metric: "ROAE", company_value: "21.5%", peer_median: "14.2%", position: "TOP_10_PERCENT" },
      { metric: "Net Interest Margin", company_value: "5.7%", peer_median: "4.8%", position: "PREMIUM" },
      { metric: "Cost to Income Ratio", company_value: "34.1%", peer_median: "44.5%", position: "TOP_10_PERCENT" },
      { metric: "Price to Book Value", company_value: "4.8x", peer_median: "2.1x", position: "PREMIUM" }
    ],
    related_signals: [
      { signal_type: "Anomaly: Foreign Accumulation Surge", description: "Net buy asing melonjak dari posisi net sell ke net buy Rp 500B dalam 1 minggu", strength: "STRONG" },
      { signal_type: "Divergence: Valuation vs Accumulation", description: "Valuasi premium (PBV 4.8x) namun akumulasi terus meningkat — divergence positif", strength: "STRONG" },
      { signal_type: "Catalyst: Efficiency Expansion", description: "CIR turun ke 34.1%, mengindikasikan leverage digital banking yang optimal", strength: "MODERATE" },
      { signal_type: "Sector Tailwind", description: "Sektor perbankan nasional tumbuh 11.2% YoY, mendukung momentum pertumbuhan kredit", strength: "MODERATE" }
    ]
  },
  GOTO: {
    finding: "GOTO mengalami tekanan distribusi institusi asing yang signifikan (-Rp 270B) meskipun indikator operasional (adjusted EBITDA) menunjukkan perbaikan bertahap. Pola ini menandakan fundamental divergence negatif di mana perbaikan operasional belum mendapat kepercayaan dari smart money.",
    score: {
      opportunity: 42.0,
      risk: 68.4,
      composite: 36.8
    },
    explanation: "Skor risk tinggi (68.4) didominasi oleh: (1) arus keluar institusi asing yang besar dan konsisten, (2) Net Profit Margin masih negatif (-12.4%) sementara peer median sudah positif (2.1%), dan (3) valuasi Price to Sales (4.1x) masih premium terhadap median (3.2x) tanpa didukung profitabilitas. Skor opportunity moderat (42.0) berasal dari tren perbaikan EBITDA dan kemitraan strategis TikTok.",
    evidence: [
      { metric: "Net Profit Margin", company_value: "-12.4%", peer_median: "2.1%", position: "BOTTOM_10_PERCENT" },
      { metric: "GTV Growth", company_value: "8.5%", peer_median: "18.2%", position: "DISCOUNT" }
    ],
    related_signals: [
      { signal_type: "Anomaly: Institutional Exodus", description: "Net sell asing melonjak dari 50B ke 320B dalam 30 hari terakhir", strength: "STRONG" },
      { signal_type: "Divergence: EBITDA Improvement vs Capital Outflow", description: "EBITDA mendekati break-even namun institusi terus menjual", strength: "STRONG" },
      { signal_type: "Risk: Profitability Uncertainty", description: "Belum ada kepastian kapan bottom-line menjadi positif secara berkelanjutan", strength: "MODERATE" }
    ]
  }
};
