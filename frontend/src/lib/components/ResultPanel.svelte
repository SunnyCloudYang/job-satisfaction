<script lang="ts">
	import type { PredictionResult } from '$lib/utils/predict';
	import RadarChart from './RadarChart.svelte';
	import ContributionBars from './ContributionBars.svelte';
	import ModelDiagram from './ModelDiagram.svelte';
	import { correlations, pathEffects } from '$lib/data/research';

	let { result, onrestart }: { result: PredictionResult; onrestart: () => void } = $props();

	const levelColor = $derived(
		result.level === 'low'
			? 'var(--color-low)'
			: result.level === 'high'
				? 'var(--color-high)'
				: 'var(--color-mid)'
	);

	const topFactor = $derived(result.contributions[0]);
</script>

<div class="mx-auto w-full max-w-2xl space-y-5 px-4 pb-16 pt-8">
	<!-- 区块一：核心结果 -->
	<section
		class="overflow-hidden rounded-3xl border border-[var(--color-line)] bg-[var(--color-surface)] p-8 text-center shadow-sm"
	>
		<p class="text-sm text-[var(--color-ink-300)]">预测工作满意度</p>
		<div class="my-3 flex items-end justify-center gap-1">
			<span class="tnum text-6xl font-bold leading-none" style="color: {levelColor}">
				{result.score.toFixed(2)}
			</span>
			<span class="mb-1 text-lg text-[var(--color-ink-300)]">/ 5.00</span>
		</div>
		<span
			class="inline-block rounded-full px-4 py-1 text-sm font-semibold text-white"
			style="background: {levelColor}"
		>
			{result.levelLabel}
		</span>
		<p class="mx-auto mt-4 max-w-md text-sm leading-relaxed text-[var(--color-ink-500)]">
			您的预测分值高于约 <span class="tnum font-semibold text-[var(--color-ink)]">{result.percentile}%</span>
			的受访者。对您影响最大的因素是「{topFactor.name}」。
		</p>
	</section>

	<!-- 区块二：维度雷达图 -->
	<section class="rounded-3xl border border-[var(--color-line)] bg-[var(--color-surface)] p-6 shadow-sm">
		<h2 class="mb-1 text-base font-semibold text-[var(--color-ink)]">各维度表现</h2>
		<p class="mb-4 text-xs text-[var(--color-ink-300)]">归一化后与样本平均对比</p>
		<RadarChart dimensions={result.dimensions} />
	</section>

	<!-- 区块三：因素贡献度 -->
	<section class="rounded-3xl border border-[var(--color-line)] bg-[var(--color-surface)] p-6 shadow-sm">
		<h2 class="mb-1 text-base font-semibold text-[var(--color-ink)]">因素贡献度</h2>
		<p class="mb-5 text-xs text-[var(--color-ink-300)]">
			绿色表示对满意度的正向拉动，橙色表示负向影响
		</p>
		<ContributionBars contributions={result.contributions} />
	</section>

	<!-- 区块四：对比建议 -->
	<section class="rounded-3xl border border-[var(--color-line)] bg-[var(--color-surface)] p-6 shadow-sm">
		<h2 class="mb-4 text-base font-semibold text-[var(--color-ink)]">改善建议</h2>
		<ul class="space-y-3">
			{#each result.advice as a, i (i)}
				<li class="flex gap-3 text-sm leading-relaxed text-[var(--color-ink-500)]">
					<span
						class="tnum mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full bg-[var(--color-brass-soft)] text-xs font-semibold text-[var(--color-ink)]"
					>
						{i + 1}
					</span>
					<span>{a}</span>
				</li>
			{/each}
		</ul>
	</section>

	<!-- 区块五：研究依据 -->
	<section class="rounded-3xl border border-[var(--color-line)] bg-[var(--color-surface)] p-6 shadow-sm">
		<h2 class="mb-1 text-base font-semibold text-[var(--color-ink)]">研究依据</h2>
		<p class="mb-4 text-xs text-[var(--color-ink-300)]">您的结果背后的作用机制</p>

		<ModelDiagram showEffects={false} />

		<p class="mt-3 text-sm leading-relaxed text-[var(--color-ink-500)]">
			实证研究显示，组织公平感对工作满意度有显著正向影响（总效应 β={pathEffects.totalEffect}），其中一部分通过<span
				class="font-medium text-[var(--color-ink)]">组织认同感</span
			>这条中介路径起作用（{pathEffects.mediationDesc}，间接效应 {pathEffects.indirectEffect}）。而<span
				class="font-medium text-[var(--color-ink)]">主管忠诚</span
			>会负向调节这条路径——当对主管的忠诚很高时，组织公平感对认同感的推动作用反而被削弱。
		</p>

		<div class="mt-4 space-y-2">
			{#each correlations as c (c.pair)}
				<div class="flex items-center justify-between gap-3 text-sm">
					<span class="text-[var(--color-ink-500)]">{c.pair}</span>
					<span class="flex items-center gap-2">
						<span class="tnum font-semibold text-[var(--color-ink)]">r={c.r}</span>
						<span class="rounded-full bg-[var(--color-brass-soft)] px-2 py-0.5 text-[10px] text-[var(--color-ink)]">{c.note}</span>
					</span>
				</div>
			{/each}
		</div>
	</section>

	<p class="px-2 text-center text-xs leading-relaxed text-[var(--color-ink-300)]">
		本结果由预测模型生成，作用机制参考相关实证研究，仅供参考。
	</p>

	<button
		type="button"
		onclick={onrestart}
		class="w-full rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] py-3.5 text-sm font-medium text-[var(--color-ink-500)] transition-colors hover:border-[var(--color-ink-300)]"
	>
		重新测评
	</button>
</div>
