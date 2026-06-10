// 量表题目定义 —— 不含工作满意度量表（那是预测目标）。
// 来源：组织公平感(20)、主管忠诚(17)、组织认同感(6) + 人口学信息(3)。

export type ScaleType = 5 | 7;

export interface LikertSection {
	id: string;
	title: string;
	intro: string;
	scale: ScaleType;
	/** 评分标签，从低到高 */
	labels: string[];
	dimensions: { key: string; name: string; items: string[] }[];
}

export interface DemographicQuestion {
	key: string;
	prompt: string;
	options: { value: string; label: string }[];
}

/** 人口学信息 */
export const demographics: DemographicQuestion[] = [
	{
		key: 'gender',
		prompt: '您的性别',
		options: [
			{ value: '女', label: '女' },
			{ value: '男', label: '男' }
		]
	},
	{
		key: 'marital',
		prompt: '您的婚姻状况',
		options: [
			{ value: '未婚/离异', label: '未婚 / 离异 / 分居 / 丧偶' },
			{ value: '已婚/同居', label: '已婚 / 同居' }
		]
	},
	{
		key: 'police_type',
		prompt: '您的警种',
		options: [
			{ value: '刑警', label: '刑警' },
			{ value: '治安警', label: '治安警' },
			{ value: '交巡警', label: '交巡警' },
			{ value: '户籍警', label: '户籍警' },
			{ value: '社区警', label: '社区警' },
			{ value: '其他', label: '其他' }
		]
	}
];

const labels7 = ['非常不同意', '不同意', '有点不同意', '中立', '有点同意', '同意', '非常同意'];
const labels5 = ['非常不符合', '不符合', '不确定', '符合', '非常符合'];

/** 组织公平感量表 (1-7) */
const organizationalJustice: LikertSection = {
	id: 'justice',
	title: '组织公平感',
	intro: '接下来请就您对组织公平性的感受作答。采用 7 级评分，从「非常不同意」到「非常同意」。',
	scale: 7,
	labels: labels7,
	dimensions: [
		{
			key: 'distributive',
			name: '分配公平',
			items: [
				'我的工作结果（如薪酬、奖励、晋升、评价）反映了我对工作的投入。',
				'我的工作结果（如薪酬、奖励、晋升、评价）与我的工作表现是相称的。',
				'我的工作结果（如薪酬、奖励、晋升、评价）公平地反映了我对工作的贡献。',
				'我的工作结果（如薪酬、奖励、晋升、评价）与我所承担的工作职责是相符的。'
			]
		},
		{
			key: 'procedural',
			name: '程序公平',
			items: [
				'我能够对即将发生的结果/决策表达自己的意见和看法。',
				'我在程序执行过程中有提出申诉的机会。',
				'制定结果的程序是中立的，没有偏见。',
				'制定结果的程序是基于准确信息的。',
				'我可以对已有的结果/决策提出复议。',
				'制定结果的程序符合道德和伦理标准。',
				'制定结果的程序对所有受影响的人都是一视同仁的。'
			]
		},
		{
			key: 'interpersonal',
			name: '人际公平',
			items: [
				'上级在执行决策程序时，能够体贴地对待我。',
				'上级在执行决策程序时，能够尊重地对待我。',
				'上级在执行决策程序时，能够避免做出不恰当的言论或评论。',
				'上级在执行决策程序时，能够以礼相待。'
			]
		},
		{
			key: 'informational',
			name: '信息公平',
			items: [
				'上级对我就决策程序进行了坦诚的沟通。',
				'上级就决策程序向我提供了合理的解释。',
				'上级就决策程序与我沟通时是及时的。',
				'上级就决策程序与我进行的沟通是具体的。',
				'上级就决策程序与我沟通时，似乎调整了他/她的表述以适应我的理解需要。'
			]
		}
	]
};

/** 主管忠诚量表 (1-7) */
const supervisorLoyalty: LikertSection = {
	id: 'loyalty',
	title: '主管忠诚',
	intro: '接下来请就您对直接主管的态度作答。同样采用 7 级评分，从「非常不同意」到「非常同意」。',
	scale: 7,
	labels: labels7,
	dimensions: [
		{
			key: 'dedication',
			name: '奉献',
			items: [
				'我愿意为我主管的成功付出额外的努力。',
				'为了帮助主管完成他/她的工作，我愿意承担额外的职责。',
				'我愿意为我的主管做任何事。',
				'为了我主管的利益，我愿意牺牲自己的个人利益。'
			]
		},
		{
			key: 'effort',
			name: '努力',
			items: [
				'我会努力工作，以帮助我的主管实现他/她的目标。',
				'为了不辜负主管的期望，我会非常努力地工作。',
				'我会尽最大努力去实现主管为我设定的工作目标。'
			]
		},
		{
			key: 'following',
			name: '跟随',
			items: [
				'如果我的主管被调往另一个部门，我愿意跟他/她一起过去。',
				'如果我的主管决定辞职去另一家公司，我愿意跟他/她一起离开。',
				'我愿意在任何时候都追随我的主管。',
				'我愿意放弃现在的职位，去追随我的主管。'
			]
		},
		{
			key: 'identification',
			name: '认同主管',
			items: [
				'我主管的成功就是我的成功。',
				'当别人称赞我的主管时，我觉得就像是在称赞我一样。',
				'我对我主管的失败感到非常遗憾。'
			]
		},
		{
			key: 'internalization',
			name: '内化主管价值观',
			items: [
				'我认为我主管的商业哲学和理念是值得遵循的。',
				'我认同我主管的经营理念。',
				'我主管对工作的看法和态度深深地影响了我。'
			]
		}
	]
};

/** 组织认同感量表 (1-5) */
const organizationalIdentification: LikertSection = {
	id: 'identity',
	title: '组织认同感',
	intro: '最后一部分，请就您与所在组织的关系作答。采用 5 级评分，从「非常不符合」到「非常符合」。',
	scale: 5,
	labels: labels5,
	dimensions: [
		{
			key: 'identity',
			name: '组织认同感',
			items: [
				'当有人批评我所在的组织时，我感觉就像是在批评我本人。',
				'我对别人如何看待我所在的组织非常感兴趣。',
				'当我谈论我所在的组织时，我通常会说「我们」而不是「他们」。',
				'组织的成功就是我的成功。',
				'当有人称赞我所在的组织时，我感觉就像是在称赞我本人。',
				'如果媒体发表了一篇关于我所在组织的负面报道，我会感到难堪。'
			]
		}
	]
};

export const sections: LikertSection[] = [
	organizationalJustice,
	supervisorLoyalty,
	organizationalIdentification
];

/** 维度中文名映射（用于结果页展示） */
export const dimensionNames: Record<string, string> = {
	distributive: '分配公平',
	procedural: '程序公平',
	interpersonal: '人际公平',
	informational: '信息公平',
	dedication: '奉献',
	effort: '努力',
	following: '跟随',
	identification: '认同主管',
	internalization: '内化主管价值观',
	identity: '组织认同感'
};

/** 扁平化的题目流（逐题作答用） */
export type Step =
	| { kind: 'demographic'; q: DemographicQuestion; index: number }
	| {
			kind: 'likert';
			sectionId: string;
			sectionTitle: string;
			scale: ScaleType;
			labels: string[];
			dimensionKey: string;
			dimensionName: string;
			text: string;
			/** 全局唯一作答键 */
			answerKey: string;
			localIndex: number;
	  };

export function buildSteps(): Step[] {
	const steps: Step[] = [];
	demographics.forEach((q, i) => steps.push({ kind: 'demographic', q, index: i }));
	for (const sec of sections) {
		let n = 0;
		for (const dim of sec.dimensions) {
			dim.items.forEach((text, j) => {
				steps.push({
					kind: 'likert',
					sectionId: sec.id,
					sectionTitle: sec.title,
					scale: sec.scale,
					labels: sec.labels,
					dimensionKey: dim.key,
					dimensionName: dim.name,
					text,
					answerKey: `${sec.id}.${dim.key}.${j}`,
					localIndex: n++
				});
			});
		}
	}
	return steps;
}

/** 段落元信息（用于进度轨道分段） */
export const sectionMeta = [
	{ id: 'demographic', title: '基本信息', count: demographics.length },
	...sections.map((s) => ({
		id: s.id,
		title: s.title,
		count: s.dimensions.reduce((a, d) => a + d.items.length, 0)
	}))
];

export const TOTAL_STEPS =
	demographics.length +
	sections.reduce((a, s) => a + s.dimensions.reduce((b, d) => b + d.items.length, 0), 0);
