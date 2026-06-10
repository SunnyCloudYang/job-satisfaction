// Mock 预测逻辑。结构与未来 Flask /api/predict 返回保持一致，
// 方便后端就绪后直接替换为 fetch 调用。
import { sections, dimensionNames } from '$lib/data/questions';

export interface DimensionScore {
	key: string;
	name: string;
	/** 原始均分 */
	mean: number;
	/** 量表满分 */
	max: number;
	/** 归一化到 0-1 */
	normalized: number;
	/** 样本均值（mock 参照） */
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

const LEVEL_LABEL: Record<PredictionResult['level'], string> = {
	low: '低满意度',
	mid: '中满意度',
	high: '高满意度'
};

// mock 的样本归一化均值（参照线），按维度给定一个合理基准
const SAMPLE_BASELINE: Record<string, number> = {
	distributive: 0.52,
	procedural: 0.55,
	interpersonal: 0.62,
	informational: 0.6,
	dedication: 0.58,
	effort: 0.7,
	following: 0.45,
	identification: 0.55,
	internalization: 0.6,
	identity: 0.56
};

const ADVICE_TEMPLATES: Record<string, string> = {
	distributive: '您对工作回报公平性的感知偏低。可关注绩效与回报的对应关系，主动了解考核口径，让付出与所得更透明。',
	procedural: '您对决策过程的公平感知有提升空间。尝试更多参与流程反馈、表达诉求，争取在关键决策中的知情与申诉机会。',
	interpersonal: '您感受到的人际尊重偏低。可与直属上级建立更直接的沟通节奏，明确彼此的期待与边界。',
	informational: '您获得的决策信息不够充分。主动向上级寻求决策背景与解释，能显著改善对组织的信任感。',
	dedication: '您对主管的投入意愿偏低。明确自身角色价值、找到值得投入的工作意义，有助于提升整体职业体验。',
	effort: '您在目标投入上略有保留。与主管对齐清晰、可达成的目标，会让努力更有方向。',
	following: '您与主管的绑定较弱。这未必是坏事——但若希望长期发展，可评估与团队的契合度。',
	identification: '您对主管的认同感偏低。寻找与主管在价值观上的共识点，有助于改善协作体验。',
	internalization: '您对主管理念的认同有限。开放地交流彼此的工作理念，往往能减少摩擦。',
	identity: '您对所在组织的归属感偏低。参与集体事务、建立同事联结，有助于增强认同与满意度。'
};

function mean(values: (number | undefined)[]): number {
	const nums = values.filter((v): v is number => typeof v === 'number');
	if (nums.length === 0) return 0;
	return nums.reduce((a, b) => a + b, 0) / nums.length;
}

/** 计算各维度均分 */
export function computeDimensions(answers: Record<string, number | string>): DimensionScore[] {
	const out: DimensionScore[] = [];
	for (const sec of sections) {
		for (const dim of sec.dimensions) {
			const vals = dim.items.map((_, j) => answers[`${sec.id}.${dim.key}.${j}`] as number | undefined);
			const m = mean(vals);
			out.push({
				key: dim.key,
				name: dimensionNames[dim.key] ?? dim.name,
				mean: m,
				max: sec.scale,
				normalized: m / sec.scale,
				sampleNormalized: SAMPLE_BASELINE[dim.key] ?? 0.55
			});
		}
	}
	return out;
}

function rand(min: number, max: number): number {
	return min + Math.random() * (max - min);
}

/**
 * Mock 预测：基于各维度归一化均分的加权和，叠加随机噪声，
 * 映射到 1-5 的工作满意度分值。
 */
export function mockPredict(answers: Record<string, number | string>): PredictionResult {
	const dimensions = computeDimensions(answers);

	// 加权：组织公平感与组织认同感权重略高
	const weights: Record<string, number> = {
		distributive: 1.2,
		procedural: 1.1,
		interpersonal: 0.9,
		informational: 0.9,
		dedication: 0.7,
		effort: 0.6,
		following: 0.5,
		identification: 0.7,
		internalization: 0.7,
		identity: 1.1
	};

	let wSum = 0;
	let acc = 0;
	for (const d of dimensions) {
		const w = weights[d.key] ?? 1;
		acc += d.normalized * w;
		wSum += w;
	}
	const base = wSum > 0 ? acc / wSum : 0.5; // 0-1

	// 映射到 1-5 + 随机噪声
	const noisy = base * 4 + 1 + rand(-0.25, 0.25);
	const score = Math.min(5, Math.max(1, Number(noisy.toFixed(2))));

	let level: PredictionResult['level'] = 'mid';
	if (score < 3) level = 'low';
	else if (score >= 4) level = 'high';

	// mock 百分位：以 3.28 为样本均值近似正态
	const percentile = Math.round(
		Math.min(99, Math.max(1, 50 + ((score - 3.28) / 0.63) * 20 + rand(-4, 4)))
	);

	// 贡献度（mock SHAP）：维度相对样本基准的偏离 × 权重 + 噪声
	const contributions: Contribution[] = dimensions
		.map((d) => {
			const w = weights[d.key] ?? 1;
			const value = Number(((d.normalized - d.sampleNormalized) * w * 0.8 + rand(-0.05, 0.05)).toFixed(3));
			return { key: d.key, name: d.name, value };
		})
		.sort((a, b) => Math.abs(b.value) - Math.abs(a.value));

	// 建议：取正向影响最大但用户得分低于样本基准的维度
	const advice = dimensions
		.filter((d) => d.normalized < d.sampleNormalized)
		.sort(
			(a, b) =>
				(b.sampleNormalized - b.normalized) * (weights[b.key] ?? 1) -
				(a.sampleNormalized - a.normalized) * (weights[a.key] ?? 1)
		)
		.slice(0, 3)
		.map((d) => ADVICE_TEMPLATES[d.key])
		.filter(Boolean);

	if (advice.length === 0) {
		advice.push('各维度表现均衡且高于样本平均，请继续保持。可将自身经验分享给团队，带动整体氛围。');
	}

	return {
		score,
		level,
		levelLabel: LEVEL_LABEL[level],
		percentile,
		dimensions,
		contributions,
		advice
	};
}
