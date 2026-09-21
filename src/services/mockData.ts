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
  StandardizedSignalOutput,
  MarketGrowthTimelinePoint
} from '../types/api';

export const MOCK_COMPANIES: Record<string, Company> = {
  BBCA: {
    symbol: "BBCA",
    name: "Bank Central Asia Tbk",
    sector: "Financials",
    sub_sector: "Banks",
    market_cap: 1150000000000000,
    updated_at: "2026-09-21T18:00:00Z"
  },
  BBRI: {
    symbol: "BBRI",
    name: "Bank Rakyat Indonesia Tbk",
    sector: "Financials",
    sub_sector: "Banks",
    market_cap: 720000000000000,
    updated_at: "2026-09-21T18:00:00Z"
  },
  BMRI: {
    symbol: "BMRI",
    name: "Bank Mandiri Tbk",
    sector: "Financials",
    sub_sector: "Banks",
    market_cap: 650000000000000,
    updated_at: "2026-09-21T18:00:00Z"
  },
  BBNI: {
    symbol: "BBNI",
    name: "Bank Negara Indonesia Tbk",
    sector: "Financials",
    sub_sector: "Banks",
    market_cap: 198000000000000,
    updated_at: "2026-09-21T18:00:00Z"
  },
  TLKM: {
    symbol: "TLKM",
    name: "Telkom Indonesia Tbk",
    sector: "Telecommunication",
    sub_sector: "Wireless Telecom",
    market_cap: 345000000000000,
    updated_at: "2026-09-21T18:00:00Z"
  },
  ASII: {
    symbol: "ASII",
    name: "Astra International Tbk",
    sector: "Consumer Discretionary",
    sub_sector: "Automotive & Heavy Equipment",
    market_cap: 210000000000000,
    updated_at: "2026-09-21T18:00:00Z"
  },
  ICBP: {
    symbol: "ICBP",
    name: "Indofood CBP Sukses Makmur Tbk",
    sector: "Consumer Staples",
    sub_sector: "Packaged Foods",
    market_cap: 135000000000000,
    updated_at: "2026-09-21T18:00:00Z"
  },
  UNVR: {
    symbol: "UNVR",
    name: "Unilever Indonesia Tbk",
    sector: "Consumer Staples",
    sub_sector: "Personal Products",
    market_cap: 92000000000000,
    updated_at: "2026-09-21T18:00:00Z"
  },
  CPIN: {
    symbol: "CPIN",
    name: "Charoen Pokphand Indonesia Tbk",
    sector: "Consumer Staples",
    sub_sector: "Poultry & Feeds",
    market_cap: 85000000000000,
    updated_at: "2026-09-21T18:00:00Z"
  },
  ADRO: {
    symbol: "ADRO",
    name: "Adaro Energy Indonesia Tbk",
    sector: "Energy",
    sub_sector: "Thermal Coal",
    market_cap: 112000000000000,
    updated_at: "2026-09-21T18:00:00Z"
  },
  PTBA: {
    symbol: "PTBA",
    name: "Bukit Asam Tbk",
    sector: "Energy",
    sub_sector: "Thermal Coal",
    market_cap: 32000000000000,
    updated_at: "2026-09-21T18:00:00Z"
  },
  AMMN: {
    symbol: "AMMN",
    name: "Amman Mineral Internasional Tbk",
    sector: "Basic Materials",
    sub_sector: "Copper & Gold Mining",
    market_cap: 580000000000000,
    updated_at: "2026-09-21T18:00:00Z"
  },
  KLBF: {
    symbol: "KLBF",
    name: "Kalbe Farma Tbk",
    sector: "Healthcare",
    sub_sector: "Pharmaceuticals",
    market_cap: 78000000000000,
    updated_at: "2026-09-21T18:00:00Z"
  },
  PGAS: {
    symbol: "PGAS",
    name: "Perusahaan Gas Negara Tbk",
    sector: "Utilities",
    sub_sector: "Gas Distribution",
    market_cap: 38000000000000,
    updated_at: "2026-09-21T18:00:00Z"
  },
  GOTO: {
    symbol: "GOTO",
    name: "GoTo Gojek Tokopedia Tbk",
    sector: "Technology",
    sub_sector: "Internet & Digital Services",
    market_cap: 75000000000000,
    updated_at: "2026-09-21T18:00:00Z"
  },
  BUKA: {
    symbol: "BUKA",
    name: "Bukalapak.com Tbk",
    sector: "Technology",
    sub_sector: "Internet & Digital Services",
    market_cap: 18000000000000,
    updated_at: "2026-09-21T18:00:00Z"
  },
  ARTO: {
    symbol: "ARTO",
    name: "Bank Jago Tbk",
    sector: "Financials",
    sub_sector: "Digital Banks",
    market_cap: 35000000000000,
    updated_at: "2026-09-21T18:00:00Z"
  },
  EMTK: {
    symbol: "EMTK",
    name: "Elang Mahkota Teknologi Tbk",
    sector: "Technology",
    sub_sector: "Media & Tech Conglomerate",
    market_cap: 28000000000000,
    updated_at: "2026-09-21T18:00:00Z"
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
  },
  BBRI: {
    id: 4,
    symbol: "BBRI",
    opportunity_score: 86.2,
    risk_score: 18.5,
    direction: "BULLISH",
    confidence: "HIGH",
    risk_level: "LOW",
    is_anomaly: false,
    anomaly_score: 28.0,
    divergence_detected: false,
    positive_factors: [
      "Pertumbuhan segmen Kupedes & Ultra Mikro (Holding UMi) tumbuh 14.8% YoY",
      "Kualitas aset membaik dengan restrukturisasi kredit terdampak pandemi tuntas",
      "Dividen payout ratio historis tinggi mencapai 80%"
    ],
    negative_factors: [
      "Biaya provisi kredit mikro masih perlu dimonitor secara ketat"
    ],
    supporting_factors: [
      "Inklusi keuangan pedesaan dan digitalisasi AgenBRILink memperkuat fee-based income"
    ],
    evidence: [
      { metric: "ROAE", company_value: "19.8%", peer_median: "14.2%", position: "TOP_10_PERCENT" },
      { metric: "Net Interest Margin", company_value: "6.8%", peer_median: "4.8%", position: "TOP_10_PERCENT" }
    ],
    what_changed: [
      { metric: "Micro Loan Growth", previous: "11.2%", current: "14.8%", delta: "+3.6%", impact: "HIGH_BULLISH" }
    ],
    peer_comparison: [
      { metric: "PBV", target: "2.5x", peer_median: "2.1x", position: "PREMIUM" }
    ],
    ai_research_summary: "BBRI memperlihatkan kekuatan fundamental di segmen mikro dengan marjin bunga tinggi. Sinergi Holding Ultra Mikro mempercepat pertumbuhan CASA dan menjaga efisiensi likuiditas.",
    disclaimer: "Bukan rekomendasi jual/beli.",
    is_cached: true,
    created_at: "2026-09-21T08:00:00Z"
  },
  BMRI: {
    id: 5,
    symbol: "BMRI",
    opportunity_score: 84.0,
    risk_score: 19.2,
    direction: "BULLISH",
    confidence: "HIGH",
    risk_level: "LOW",
    is_anomaly: false,
    anomaly_score: 22.0,
    divergence_detected: false,
    positive_factors: [
      "Kredit wholesale & korporasi melonjak 16.5% YoY",
      "Aplikasi Livin' by Mandiri mencatat transaksi Rp 3.200 Triliun",
      "NPL gross terendah dalam 5 tahun terakhir di level 1.1%"
    ],
    negative_factors: [
      "Ketergantungan moderat pada proyek-proyek infrastruktur berskala besar"
    ],
    supporting_factors: [
      "Perluasan ekosistem Kopra untuk rantai pasok korporasi"
    ],
    evidence: [
      { metric: "ROAE", company_value: "18.5%", peer_median: "14.2%", position: "TOP_10_PERCENT" },
      { metric: "NPL Coverage Ratio", company_value: "320%", peer_median: "210%", position: "TOP_10_PERCENT" }
    ],
    what_changed: [
      { metric: "CASA Ratio", previous: "76.4%", current: "79.1%", delta: "+2.7%", impact: "MODERATE_BULLISH" }
    ],
    peer_comparison: [
      { metric: "PBV", target: "2.2x", peer_median: "2.1x", position: "FAIR" }
    ],
    ai_research_summary: "BMRI menunjukkan momentum kredit korporasi dan digital wholesale yang luar biasa, dengan bantalan provisi NPL coverage tertinggi di industri perbankan nasional.",
    disclaimer: "Bukan rekomendasi jual/beli.",
    is_cached: true,
    created_at: "2026-09-21T08:00:00Z"
  },
  BBNI: {
    id: 6,
    symbol: "BBNI",
    opportunity_score: 81.5,
    risk_score: 22.0,
    direction: "BULLISH",
    confidence: "HIGH",
    risk_level: "LOW",
    is_anomaly: false,
    anomaly_score: 30.0,
    divergence_detected: false,
    positive_factors: [
      "Transformasi digital perbankan mendorong efisiensi operasional berkelanjutan",
      "Valuasi PBV paling atraktif di antara Top 4 Bank BUMN (1.3x)",
      "Pertumbuhan kredit segmen payroll dan korporasi blue chip solid"
    ],
    negative_factors: [
      "Pertumbuhan dana murah (CASA) ritel masih mengejar penetrasi peer utama"
    ],
    supporting_factors: [
      "Aplikasi wondr by BNI memperluas penetrasi generasi muda"
    ],
    evidence: [
      { metric: "ROAE", company_value: "15.8%", peer_median: "14.2%", position: "PREMIUM" },
      { metric: "PBV", company_value: "1.3x", peer_median: "2.1x", position: "DISCOUNT" }
    ],
    what_changed: [
      { metric: "Digital Transaction Vol", previous: "+18%", current: "+34%", delta: "+16%", impact: "HIGH_BULLISH" }
    ],
    peer_comparison: [
      { metric: "PER", target: "9.2x", peer_median: "13.5x", position: "DISCOUNT" }
    ],
    ai_research_summary: "BBNI menawarkan margin of safety valuasi tertinggi di sektor perbankan Tier-1, didukung katalis transformasi aplikasi wondr dan pembersihan portofolio kredit lama.",
    disclaimer: "Bukan rekomendasi jual/beli.",
    is_cached: true,
    created_at: "2026-09-21T08:00:00Z"
  },
  AMMN: {
    id: 7,
    symbol: "AMMN",
    opportunity_score: 76.0,
    risk_score: 34.0,
    direction: "BULLISH",
    confidence: "HIGH",
    risk_level: "MODERATE",
    is_anomaly: true,
    anomaly_score: 72.0,
    divergence_detected: true,
    positive_factors: [
      "Smelter tembaga Batu Hijau mulai beroperasi penuh secara komersial",
      "Kenaikan harga tembaga global di tengah akselerasi kendaraan listrik (EV) & AI data center",
      "Cadangan bijih tembaga dan emas terbukti berkualitas tinggi"
    ],
    negative_factors: [
      "Capex smelter dan beban bunga pinjaman proyek tinggi",
      "Sensitivitas tinggi terhadap fluktuasi harga komoditas global"
    ],
    supporting_factors: [
      "Kebijakan hilirisasi mineral nasional memberikan perlindungan fiskal"
    ],
    evidence: [
      { metric: "EBITDA Margin", company_value: "58.4%", peer_median: "38.0%", position: "TOP_10_PERCENT" },
      { metric: "Revenue Growth YoY", company_value: "42.0%", peer_median: "12.5%", position: "TOP_10_PERCENT" }
    ],
    what_changed: [
      { metric: "Smelter Utilization", previous: "45%", current: "92%", delta: "+47%", impact: "HIGH_BULLISH" }
    ],
    peer_comparison: [
      { metric: "EV/EBITDA", target: "14.5x", peer_median: "8.2x", position: "PREMIUM" }
    ],
    ai_research_summary: "AMMN diuntungkan oleh transisi energi global dan ramp-up fasilitas smelter barunya. Terdapat anomali akumulasi institusi pada saham material dasar ini.",
    disclaimer: "Bukan rekomendasi jual/beli.",
    is_cached: true,
    created_at: "2026-09-21T08:00:00Z"
  },
  ICBP: {
    id: 8,
    symbol: "ICBP",
    opportunity_score: 75.2,
    risk_score: 24.5,
    direction: "BULLISH",
    confidence: "HIGH",
    risk_level: "LOW",
    is_anomaly: false,
    anomaly_score: 25.0,
    divergence_detected: false,
    positive_factors: [
      "Pertumbuhan volume penjualan mi instan global (Pinehill) solid di Timur Tengah & Afrika",
      "Stabilitas harga bahan baku gandum dan CPO menjaga marjin laba kotor",
      "Daya beli domestik konsumsi pangan tetap tangguh"
    ],
    negative_factors: [
      "Eksposur utang mata uang asing (USD) entitas Pinehill terhadap rupiah"
    ],
    supporting_factors: [
      "Kekuatan pricing power merek Indomie yang tidak tertandingi"
    ],
    evidence: [
      { metric: "Gross Margin", company_value: "36.2%", peer_median: "29.5%", position: "PREMIUM" },
      { metric: "Operating Margin", company_value: "20.8%", peer_median: "14.0%", position: "TOP_10_PERCENT" }
    ],
    what_changed: [
      { metric: "Pinehill Sales YoY", previous: "+6.8%", current: "+11.4%", delta: "+4.6%", impact: "MODERATE_BULLISH" }
    ],
    peer_comparison: [
      { metric: "PER", target: "14.5x", peer_median: "16.8x", position: "DISCOUNT" }
    ],
    ai_research_summary: "ICBP menyajikan pertahanan defensif yang prima di segmen kebutuhan pokok, diperkuat marjin stabil dan pemulihan laba valas dari operasional internasional.",
    disclaimer: "Bukan rekomendasi jual/beli.",
    is_cached: true,
    created_at: "2026-09-21T08:00:00Z"
  },
  ASII: {
    id: 9,
    symbol: "ASII",
    opportunity_score: 72.8,
    risk_score: 29.0,
    direction: "BULLISH",
    confidence: "MEDIUM",
    risk_level: "LOW",
    is_anomaly: false,
    anomaly_score: 35.0,
    divergence_detected: false,
    positive_factors: [
      "Valuasi terdiskon dalam dengan dividend yield atraktif di atas 7.5%",
      "Kinerja solid anak usaha United Tractors (UNTR) dan jasa keuangan (Astra Financial)",
      "Penetrasi model hybrid baru meredam kompetisi kendaraan listrik"
    ],
    negative_factors: [
      "Penjualan mobil nasional mengalami perlambatan temporer",
      "Persaingan dari merk otomotif Tiongkok di segmen EV retail"
    ],
    supporting_factors: [
      "Diversifikasi ke sektor kesehatan (Hermina) dan infrastruktur jalan tol"
    ],
    evidence: [
      { metric: "Dividend Yield", company_value: "7.8%", peer_median: "3.5%", position: "TOP_10_PERCENT" },
      { metric: "PER", company_value: "6.8x", peer_median: "12.0x", position: "DISCOUNT" }
    ],
    what_changed: [
      { metric: "Hybrid Car Share", previous: "12%", current: "24%", delta: "+12%", impact: "MODERATE_BULLISH" }
    ],
    peer_comparison: [
      { metric: "PBV", target: "0.95x", peer_median: "1.6x", position: "DISCOUNT" }
    ],
    ai_research_summary: "ASII diperdagangkan pada valuasi di bawah nilai buku (PBV < 1x) dengan yield dividen sangat tinggi, menjadikannya pilihan value investing unggulan saat siklus otomotif membalik.",
    disclaimer: "Bukan rekomendasi jual/beli.",
    is_cached: true,
    created_at: "2026-09-21T08:00:00Z"
  },
  ADRO: {
    id: 10,
    symbol: "ADRO",
    opportunity_score: 71.5,
    risk_score: 33.0,
    direction: "BULLISH",
    confidence: "MEDIUM",
    risk_level: "MODERATE",
    is_anomaly: false,
    anomaly_score: 40.0,
    divergence_detected: false,
    positive_factors: [
      "Transformasi bisnis hijau ke smelter aluminium Kalimantan Utara (Adaro Minerals)",
      "Neraca keuangan bebas utang bersih (net cash position) yang sangat kuat",
      "Dividen jumbo konsisten kepada pemegang saham"
    ],
    negative_factors: [
      "Normalisasi harga batubara termal global dari puncak siklus komoditas"
    ],
    supporting_factors: [
      "Permintaan batubara metalurgi untuk industri baja Asia tetap resilient"
    ],
    evidence: [
      { metric: "Net Cash (IDR)", company_value: "Rp 35 Triliun", peer_median: "Rp 2 Triliun", position: "TOP_10_PERCENT" },
      { metric: "EV/EBITDA", company_value: "3.2x", peer_median: "5.5x", position: "DISCOUNT" }
    ],
    what_changed: [
      { metric: "Aluminium Smelter Progress", previous: "30%", current: "68%", delta: "+38%", impact: "HIGH_BULLISH" }
    ],
    peer_comparison: [
      { metric: "PER", target: "5.4x", peer_median: "7.8x", position: "DISCOUNT" }
    ],
    ai_research_summary: "ADRO mengalokasikan arus kas raksasa batubara ke diversifikasi hijau smelter aluminium, didukung neraca kas bersih yang tebal dan dividen substansial.",
    disclaimer: "Bukan rekomendasi jual/beli.",
    is_cached: true,
    created_at: "2026-09-21T08:00:00Z"
  },
  KLBF: {
    id: 11,
    symbol: "KLBF",
    opportunity_score: 70.2,
    risk_score: 21.0,
    direction: "BULLISH",
    confidence: "HIGH",
    risk_level: "LOW",
    is_anomaly: false,
    anomaly_score: 20.0,
    divergence_detected: false,
    positive_factors: [
      "Pertumbuhan obat resep dan produk biologis/onkologi berlisensi global",
      "Peningkatan kesadaran preventif masyarakat menopang divisi Consumer Health",
      "Beban bahan baku impor farmasi melandai seiring stabilisasi kurs"
    ],
    negative_factors: [
      "Regulasi harga eceran tertinggi BPJS pada obat generik esensial"
    ],
    supporting_factors: [
      "Kemitraan strategis vaksin & biosimilar dengan institusi internasional"
    ],
    evidence: [
      { metric: "ROAE", company_value: "16.2%", peer_median: "11.5%", position: "PREMIUM" },
      { metric: "Debt to Equity", company_value: "0.15x", peer_median: "0.55x", position: "TOP_10_PERCENT" }
    ],
    what_changed: [
      { metric: "Biologics Revenue", previous: "+14%", current: "+26%", delta: "+12%", impact: "HIGH_BULLISH" }
    ],
    peer_comparison: [
      { metric: "PER", target: "22.5x", peer_median: "24.0x", position: "FAIR" }
    ],
    ai_research_summary: "KLBF memimpin industri farmasi Asia Tenggara dengan neraca zero-debt dan ekspansi agresif ke produk biologis bernilai tambah tinggi.",
    disclaimer: "Bukan rekomendasi jual/beli.",
    is_cached: true,
    created_at: "2026-09-21T08:00:00Z"
  },
  UNVR: {
    id: 12,
    symbol: "UNVR",
    opportunity_score: 52.0,
    risk_score: 48.0,
    direction: "NEUTRAL",
    confidence: "MEDIUM",
    risk_level: "MODERATE",
    is_anomaly: false,
    anomaly_score: 38.0,
    divergence_detected: false,
    positive_factors: [
      "Inisiatif peremajaan portofolio merek premium dan efisiensi kanal distribusi",
      "Dividen payout ratio tetap mendekati 100%"
    ],
    negative_factors: [
      "Persaingan sengit dari brand lokal di segmen personal care & pembersih",
      "Pertumbuhan top-line melambat di bawah pertumbuhan PDB riil"
    ],
    supporting_factors: [
      "Peningkatan penetrasi e-commerce dan minimarket modern"
    ],
    evidence: [
      { metric: "ROAE", company_value: "68.0%", peer_median: "18.0%", position: "TOP_10_PERCENT" },
      { metric: "Sales Growth YoY", company_value: "-2.4%", peer_median: "5.5%", position: "BOTTOM_10_PERCENT" }
    ],
    what_changed: [
      { metric: "Distribution Price Reset", previous: "In-Progress", current: "Completed", delta: "OK", impact: "NEUTRAL" }
    ],
    peer_comparison: [
      { metric: "PER", target: "21.0x", peer_median: "18.5x", position: "PREMIUM" }
    ],
    ai_research_summary: "UNVR tengah menjalankan fase turnaround operasional dan restrukturisasi saluran ritel. Butuh konfirmasi perbaikan volume penjualan sebelum momentum pemulihan terbentuk kuat.",
    disclaimer: "Bukan rekomendasi jual/beli.",
    is_cached: true,
    created_at: "2026-09-21T08:00:00Z"
  },
  CPIN: {
    id: 13,
    symbol: "CPIN",
    opportunity_score: 64.5,
    risk_score: 36.0,
    direction: "NEUTRAL",
    confidence: "MEDIUM",
    risk_level: "MODERATE",
    is_anomaly: false,
    anomaly_score: 29.0,
    divergence_detected: false,
    positive_factors: [
      "Normalisasi harga pakan jagung lokal berkat panen raya",
      "Permintaan produk daging olahan Fiesta terus berekspansi"
    ],
    negative_factors: [
      "Volatilitas harga livebird (ayam hidup) di tingkat peternak farm"
    ],
    supporting_factors: [
      "Program culling indukan pemerintah menyeimbangkan pasokan pasar"
    ],
    evidence: [
      { metric: "Operating Margin", company_value: "7.8%", peer_median: "5.5%", position: "PREMIUM" }
    ],
    what_changed: [
      { metric: "Corn Feed Cost", previous: "Rp 5,800/kg", current: "Rp 4,900/kg", delta: "-Rp 900", impact: "MODERATE_BULLISH" }
    ],
    peer_comparison: [
      { metric: "PER", target: "24.2x", peer_median: "20.5x", position: "PREMIUM" }
    ],
    ai_research_summary: "CPIN memiliki integrasi hulu-hilir perunggasan paling matang di Indonesia, dengan marjin pakan yang menopang fluktuasi harga ayam potong.",
    disclaimer: "Bukan rekomendasi jual/beli.",
    is_cached: true,
    created_at: "2026-09-21T08:00:00Z"
  },
  PTBA: {
    id: 14,
    symbol: "PTBA",
    opportunity_score: 66.0,
    risk_score: 35.0,
    direction: "NEUTRAL",
    confidence: "HIGH",
    risk_level: "LOW",
    is_anomaly: false,
    anomaly_score: 22.0,
    divergence_detected: false,
    positive_factors: [
      "Kontrak pasokan batubara DMO ke pembangkit listrik PLN stabil",
      "Peningkatan kapasitas angkut logistik kereta api Sumatra Selatan"
    ],
    negative_factors: [
      "Harga patokan batubara DMO dipatok pada batas atas regulasi"
    ],
    supporting_factors: [
      "Dividen payout konsisten sebagai BUMN holding MIND ID"
    ],
    evidence: [
      { metric: "Dividend Yield", company_value: "11.2%", peer_median: "4.5%", position: "TOP_10_PERCENT" }
    ],
    what_changed: [
      { metric: "Train Capacity Expansion", previous: "32 MT", current: "38 MT", delta: "+6 MT", impact: "MODERATE_BULLISH" }
    ],
    peer_comparison: [
      { metric: "PER", target: "6.2x", peer_median: "7.5x", position: "DISCOUNT" }
    ],
    ai_research_summary: "PTBA adalah emiten penghasil dividen tinggi dengan basis pendapatan terjamin dari pasar listrik domestik serta logistik rel yang terus ditingkatkan.",
    disclaimer: "Bukan rekomendasi jual/beli.",
    is_cached: true,
    created_at: "2026-09-21T08:00:00Z"
  },
  PGAS: {
    id: 15,
    symbol: "PGAS",
    opportunity_score: 68.0,
    risk_score: 31.0,
    direction: "BULLISH",
    confidence: "MEDIUM",
    risk_level: "LOW",
    is_anomaly: false,
    anomaly_score: 30.0,
    divergence_detected: false,
    positive_factors: [
      "Penyaluran gas pipa industri dan jaringan gas rumah tangga meningkat konsisten",
      "Penyelesaian sengketa perpajakan masa lalu memberikan kepastian neraca",
      "Arus kas operasional stabil sebagai distributor gas dominan nasional"
    ],
    negative_factors: [
      "Kebijakan Harga Gas Bumi Tertentu (HGBT) membatasi fleksibilitas margin transmisi"
    ],
    supporting_factors: [
      "Transisi gas sebagai energi jembatan rendah emisi"
    ],
    evidence: [
      { metric: "Free Cash Flow Yield", company_value: "12.5%", peer_median: "6.8%", position: "TOP_10_PERCENT" }
    ],
    what_changed: [
      { metric: "Gas Distribution Volume", previous: "920 BBTUD", current: "985 BBTUD", delta: "+65 BBTUD", impact: "MODERATE_BULLISH" }
    ],
    peer_comparison: [
      { metric: "PER", target: "7.8x", peer_median: "11.0x", position: "DISCOUNT" }
    ],
    ai_research_summary: "PGAS memiliki moat infrastruktur pipa gas bumi terpanjang di tanah air, menjamin dividen yield sehat dan visibilitas kas yang kuat.",
    disclaimer: "Bukan rekomendasi jual/beli.",
    is_cached: true,
    created_at: "2026-09-21T08:00:00Z"
  },
  BUKA: {
    id: 16,
    symbol: "BUKA",
    opportunity_score: 38.0,
    risk_score: 65.0,
    direction: "BEARISH",
    confidence: "MEDIUM",
    risk_level: "HIGH",
    is_anomaly: false,
    anomaly_score: 45.0,
    divergence_detected: false,
    positive_factors: [
      "Kas bersih dan deposito likuid melimpah (melebihi kapitalisasi pasarnya)",
      "Pertumbuhan bisnis O2O Mitra Bukalapak di kota Tier 2 dan Tier 3"
    ],
    negative_factors: [
      "Operasional marketplace inti masih membukukan kerugian operasional",
      "Ketiadaan pertumbuhan top-line yang signifikan dalam 4 kuartal terakhir"
    ],
    supporting_factors: [
      "Pendapatan bunga dari kas bank menopang bottom line bersih"
    ],
    evidence: [
      { metric: "Cash to Market Cap", company_value: "115%", peer_median: "12%", position: "TOP_10_PERCENT" },
      { metric: "Revenue Growth YoY", company_value: "3.2%", peer_median: "16.0%", position: "BOTTOM_10_PERCENT" }
    ],
    what_changed: [
      { metric: "Marketplace GMV", previous: "Down 12%", current: "Down 18%", delta: "-6%", impact: "HIGH_BEARISH" }
    ],
    peer_comparison: [
      { metric: "P/B", target: "0.6x", peer_median: "2.4x", position: "DISCOUNT" }
    ],
    ai_research_summary: "BUKA adalah situasi deep-value dengan tumpukan kas berlimpah, namun belum adanya katalis pertumbuhan bisnis organik menjadi pemberat risiko utama.",
    disclaimer: "Bukan rekomendasi jual/beli.",
    is_cached: true,
    created_at: "2026-09-21T08:00:00Z"
  },
  ARTO: {
    id: 17,
    symbol: "ARTO",
    opportunity_score: 69.5,
    risk_score: 55.0,
    direction: "BULLISH",
    confidence: "MEDIUM",
    risk_level: "MODERATE",
    is_anomaly: true,
    anomaly_score: 68.0,
    divergence_detected: true,
    positive_factors: [
      "Pertumbuhan nasabah dana murah melalui integrasi ekosistem GoPay dan Bibit",
      "Penyaluran kredit digital tumbuh di atas 30% YoY dengan NPL terjaga",
      "Profitabilitas bersih meningkat eksponensial dari basis rendah"
    ],
    negative_factors: [
      "Valuasi PBV tinggi (di atas 4x) menuntut pertumbuhan kredit tanpa henti",
      "Persaingan bank digital makin ketat dari bank konvensional"
    ],
    supporting_factors: [
      "Kerjasama channeling fintech dengan limit risiko terkontrol"
    ],
    evidence: [
      { metric: "Loan Growth YoY", company_value: "34.5%", peer_median: "11.2%", position: "TOP_10_PERCENT" },
      { metric: "Cost of Fund", company_value: "2.8%", peer_median: "4.2%", position: "TOP_10_PERCENT" }
    ],
    what_changed: [
      { metric: "GoPay App Integration", previous: "Beta", current: "Full Rollout", delta: "100%", impact: "HIGH_BULLISH" }
    ],
    peer_comparison: [
      { metric: "PBV", target: "4.2x", peer_median: "2.1x", position: "PREMIUM" }
    ],
    ai_research_summary: "ARTO memvalidasi model bisnis bank digital melalui integrasi dompet GoPay. Terdeteksi anomali pertumbuhan CASA yang cepat menekan beban bunga bank.",
    disclaimer: "Bukan rekomendasi jual/beli.",
    is_cached: true,
    created_at: "2026-09-21T08:00:00Z"
  },
  EMTK: {
    id: 18,
    symbol: "EMTK",
    opportunity_score: 60.5,
    risk_score: 52.0,
    direction: "NEUTRAL",
    confidence: "MEDIUM",
    risk_level: "MODERATE",
    is_anomaly: false,
    anomaly_score: 38.0,
    divergence_detected: false,
    positive_factors: [
      "Portofolio media siaran SCTV & Indosiar memimpin audience share nasional",
      "Platform Vidio.com menduduki peringkat #1 OTT lokal dengan hak siar Liga Inggris & olahraga",
      "Ekspansi ke rantai rumah sakit Omni/EMC Healthcare"
    ],
    negative_factors: [
      "Investasi konten OTT masih menekan laba bersih konsolidasi",
      "Fluktuasi nilai wajar portofolio saham startup teknologi"
    ],
    supporting_factors: [
      "Monetisasi iklan digital video streaming tumbuh tinggi"
    ],
    evidence: [
      { metric: "Vidio Paying Subscribers", company_value: "4.8 Juta", peer_median: "1.2 Juta", position: "TOP_10_PERCENT" }
    ],
    what_changed: [
      { metric: "OTT Ad Revenue", previous: "+25%", current: "+42%", delta: "+17%", impact: "MODERATE_BULLISH" }
    ],
    peer_comparison: [
      { metric: "PBV", target: "1.2x", peer_median: "1.8x", position: "DISCOUNT" }
    ],
    ai_research_summary: "EMTK bertransisi sukses ke ekosistem media digital streaming melalui Vidio.com, ditopang arus kas stabil stasiun televisi FTA dan aset rumah sakit.",
    disclaimer: "Bukan rekomendasi jual/beli.",
    is_cached: true,
    created_at: "2026-09-21T08:00:00Z"
  }
};

// ─── Top 10 Market Growth Time-Series (12 Bulan Terakhir) ──────
export const MOCK_TOP10_GROWTH_TIMELINE: MarketGrowthTimelinePoint[] = [
  { period: "Okt 25", BBCA: 76.5, BBRI: 74.0, BMRI: 71.2, BBNI: 68.5, TLKM: 69.0, AMMN: 62.4, ICBP: 70.1, ASII: 65.8, ADRO: 60.2, KLBF: 64.0 },
  { period: "Nov 25", BBCA: 78.2, BBRI: 75.8, BMRI: 73.0, BBNI: 70.1, TLKM: 70.5, AMMN: 64.8, ICBP: 71.0, ASII: 66.5, ADRO: 62.5, KLBF: 65.2 },
  { period: "Des 25", BBCA: 80.0, BBRI: 77.5, BMRI: 74.8, BBNI: 71.9, TLKM: 71.8, AMMN: 67.0, ICBP: 71.5, ASII: 68.0, ADRO: 64.0, KLBF: 66.0 },
  { period: "Jan 26", BBCA: 82.4, BBRI: 79.2, BMRI: 76.5, BBNI: 73.8, TLKM: 73.2, AMMN: 69.5, ICBP: 72.8, ASII: 69.2, ADRO: 66.1, KLBF: 66.8 },
  { period: "Feb 26", BBCA: 83.9, BBRI: 80.6, BMRI: 78.1, BBNI: 75.2, TLKM: 74.0, AMMN: 71.0, ICBP: 73.4, ASII: 68.5, ADRO: 67.8, KLBF: 67.5 },
  { period: "Mar 26", BBCA: 85.1, BBRI: 82.0, BMRI: 79.5, BBNI: 76.9, TLKM: 75.5, AMMN: 72.8, ICBP: 74.0, ASII: 70.1, ADRO: 69.2, KLBF: 68.3 },
  { period: "Apr 26", BBCA: 84.5, BBRI: 81.2, BMRI: 80.2, BBNI: 77.5, TLKM: 74.8, AMMN: 73.5, ICBP: 73.2, ASII: 69.4, ADRO: 70.0, KLBF: 68.9 },
  { period: "Mei 26", BBCA: 86.0, BBRI: 83.1, BMRI: 81.4, BBNI: 78.8, TLKM: 76.2, AMMN: 74.2, ICBP: 74.5, ASII: 71.0, ADRO: 68.5, KLBF: 69.4 },
  { period: "Jun 26", BBCA: 87.2, BBRI: 84.5, BMRI: 82.3, BBNI: 79.9, TLKM: 77.0, AMMN: 75.0, ICBP: 74.8, ASII: 71.8, ADRO: 70.4, KLBF: 69.8 },
  { period: "Jul 26", BBCA: 86.8, BBRI: 85.0, BMRI: 83.1, BBNI: 80.5, TLKM: 76.5, AMMN: 75.5, ICBP: 75.0, ASII: 72.2, ADRO: 71.0, KLBF: 70.0 },
  { period: "Ags 26", BBCA: 88.0, BBRI: 85.8, BMRI: 83.8, BBNI: 81.0, TLKM: 77.8, AMMN: 75.8, ICBP: 75.1, ASII: 72.5, ADRO: 71.2, KLBF: 70.1 },
  { period: "Sep 26", BBCA: 88.5, BBRI: 86.2, BMRI: 84.0, BBNI: 81.5, TLKM: 78.4, AMMN: 76.0, ICBP: 75.2, ASII: 72.8, ADRO: 71.5, KLBF: 70.2 },
];

export const MOCK_MARKET_OVERVIEW: MarketOverview = {
  top_opportunities: [
    MOCK_INTELLIGENCE.BBCA,
    MOCK_INTELLIGENCE.BBRI,
    MOCK_INTELLIGENCE.BMRI,
    MOCK_INTELLIGENCE.BBNI,
    MOCK_INTELLIGENCE.TLKM,
    MOCK_INTELLIGENCE.AMMN,
    MOCK_INTELLIGENCE.ICBP,
    MOCK_INTELLIGENCE.ASII,
    MOCK_INTELLIGENCE.ADRO,
    MOCK_INTELLIGENCE.KLBF
  ],
  top_risks: [
    MOCK_INTELLIGENCE.GOTO,
    MOCK_INTELLIGENCE.BUKA,
    MOCK_INTELLIGENCE.EMTK,
    MOCK_INTELLIGENCE.UNVR
  ],
  detected_anomalies: [
    MOCK_INTELLIGENCE.BBCA,
    MOCK_INTELLIGENCE.GOTO,
    MOCK_INTELLIGENCE.ARTO,
    MOCK_INTELLIGENCE.AMMN
  ],
  sector_summary: [
    {
      sector: "Financials",
      sentiment: "Bullish",
      avg_opportunity: 85.0,
      anomaly_count: 2
    },
    {
      sector: "Telecommunication",
      sentiment: "Bullish",
      avg_opportunity: 78.4,
      anomaly_count: 0
    },
    {
      sector: "Basic Materials",
      sentiment: "Bullish",
      avg_opportunity: 76.0,
      anomaly_count: 1
    },
    {
      sector: "Consumer Staples",
      sentiment: "Bullish",
      avg_opportunity: 63.9,
      anomaly_count: 0
    },
    {
      sector: "Energy",
      sentiment: "Bullish",
      avg_opportunity: 68.8,
      anomaly_count: 0
    },
    {
      sector: "Healthcare",
      sentiment: "Bullish",
      avg_opportunity: 70.2,
      anomaly_count: 0
    },
    {
      sector: "Utilities",
      sentiment: "Bullish",
      avg_opportunity: 68.0,
      anomaly_count: 0
    },
    {
      sector: "Consumer Discretionary",
      sentiment: "Neutral",
      avg_opportunity: 72.8,
      anomaly_count: 0
    },
    {
      sector: "Technology",
      sentiment: "Bearish",
      avg_opportunity: 46.8,
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
