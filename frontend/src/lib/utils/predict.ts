// 预测结果类型，与 Flask /api/predict 返回结构一致。

export interface DimensionScore {
	key: string;
	name: string;
	/** 原始均分 */
	mean: number;
	/** 量表满分 */
	max: number;
	/** 归一化到 0-1 */
	normalized: number;
	/** 样本均值（参照线） */
	sampleNormalized: number;
}

export interface Contribution {
	key: string;
	name: string;
	/** 对预测的影响，正负值 */
	value: number;
}

export interface PredictionResult {
	score: number; // 1-5
	level: 'low' | 'mid' | 'high';
	levelLabel: string;
	percentile: number; // 0-100
	dimensions: DimensionScore[];
	contributions: Contribution[];
	advice: string[];
}
