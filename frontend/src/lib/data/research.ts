// 研究内容数据 —— 来源于实证研究《组织公平感对警察工作满意度的影响：
// 一个关于组织认同感、主管忠诚的有调节的中介模型》。
// 这里把论文的核心结论结构化，供欢迎页、模型介绍页、结果页引用，
// 让交互界面与研究内容保持一致、可追溯。

/** 研究基本信息 */
export const studyMeta = {
	title: '组织公平感对警察工作满意度的影响',
	subtitle: '一个有调节的中介模型',
	sample: 4271,
	population: '某市一线警察',
	period: '问卷调查',
	summary:
		'本测评以一项面向 4271 名一线警察的实证研究为基础。研究发现，组织公平感不仅直接提升工作满意度，还通过组织认同感间接产生影响，而这一中介路径会受到主管忠诚的调节。'
};

/** 四个核心变量 */
export interface Variable {
	id: string;
	name: string;
	role: 'predictor' | 'mediator' | 'moderator' | 'outcome';
	roleLabel: string;
	desc: string;
}

export const variables: Variable[] = [
	{
		id: 'justice',
		name: '组织公平感',
		role: 'predictor',
		roleLabel: '自变量',
		desc: '个体对组织在分配、程序、人际与信息四个方面是否公平的整体感知。'
	},
	{
		id: 'identity',
		name: '组织认同感',
		role: 'mediator',
		roleLabel: '中介变量',
		desc: '个体将组织成败视为自身成败、产生归属与「我们」意识的程度。'
	},
	{
		id: 'loyalty',
		name: '主管忠诚',
		role: 'moderator',
		roleLabel: '调节变量',
		desc: '个体对直接主管的奉献、努力、跟随、认同与价值观内化。'
	},
	{
		id: 'satisfaction',
		name: '工作满意度',
		role: 'outcome',
		roleLabel: '因变量',
		desc: '个体对工作整体的积极情感评价，是本测评的预测目标。'
	}
];

/** 关键效应与相关系数（用于结果页参照说明） */
export const correlations = [
	{ pair: '组织公平感 ↔ 工作满意度', r: 0.705, note: '高度正相关' },
	{ pair: '组织认同感 ↔ 工作满意度', r: 0.534, note: '中度正相关' },
	{ pair: '主管忠诚 ↔ 工作满意度', r: 0.38, note: '中度正相关' }
];

/** 模型路径效应 */
export const pathEffects = {
	totalEffect: 0.359, // 组织公平感 → 工作满意度 总效应
	directEffect: 0.334, // 直接效应
	indirectEffect: 0.025, // 经组织认同感的间接效应
	indirectCI: '95% CI [0.019, 0.031]',
	moderationB: -0.027, // 主管忠诚对「公平感→认同感」的负向调节
	mediationDesc: '部分中介'
};

/** 简单斜率：主管忠诚高低时，组织公平感对组织认同感的影响强度 */
export const simpleSlopes = [
	{ level: '主管忠诚较低', slope: 0.156 },
	{ level: '主管忠诚较高', slope: 0.097 }
];

/** 理论依据 */
export const theories = [
	{
		name: '公平启发理论',
		desc: '人们会用公平感作为「认知捷径」，快速判断是否值得信任并融入组织，从而影响其态度与归属。'
	},
	{
		name: '社会交换理论',
		desc: '当个体感到被组织公平对待，会以更高的认同与投入作为回报，形成良性的互惠关系。'
	}
];

/** 量表来源与信度（用于量表指导语补充） */
export const scaleSources: Record<
	string,
	{ author: string; items: number; scale: number; alpha: number; note?: string }
> = {
	justice: {
		author: 'Colquitt (2001)',
		items: 20,
		scale: 7,
		alpha: 0.977,
		note: '分配、程序、人际、信息四维度'
	},
	loyalty: {
		author: 'Chen 等 (2002)',
		items: 17,
		scale: 7,
		alpha: 0.958,
		note: '奉献、努力、跟随、认同主管、内化价值观五维度'
	},
	identity: {
		author: 'Mael & Ashforth (1992)',
		items: 6,
		scale: 5,
		alpha: 0.896
	},
	satisfaction: {
		author: 'MSQ 简式量表',
		items: 20,
		scale: 5,
		alpha: 0.941,
		note: '本测评的预测目标，未在问卷中作答'
	}
};
