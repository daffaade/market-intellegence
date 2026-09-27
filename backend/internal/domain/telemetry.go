package domain

type PipelineStageId string

const (
	StageRetrieval         PipelineStageId = "RETRIEVAL"
	StageValidation        PipelineStageId = "VALIDATION"
	StageNormalization     PipelineStageId = "NORMALIZATION"
	StageTransformation    PipelineStageId = "TRANSFORMATION"
	StageFeatureGeneration PipelineStageId = "FEATURE_GENERATION"
	StageIntelligenceEngine PipelineStageId = "INTELLIGENCE_ENGINE"
)

type PipelineStage struct {
	ID          PipelineStageId `json:"id"`
	Label       string          `json:"label"`
	Description string          `json:"description"`
	Status      string          `json:"status"` // "COMPLETED" | "PROCESSING" | "PENDING"
	DataType    string          `json:"data_type"`
	DurationMs  int64           `json:"duration_ms"`
}

type PipelineTelemetry struct {
	Stages          []PipelineStage `json:"stages"`
	TotalDurationMs int64           `json:"total_duration_ms"`
	PipelineStatus  string          `json:"pipeline_status"`
}
