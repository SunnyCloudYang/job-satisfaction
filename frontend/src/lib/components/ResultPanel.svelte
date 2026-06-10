<script lang="ts">
	import type { PredictionResult } from '$lib/utils/predict';
	import RadarChart from './RadarChart.svelte';
	import ContributionBars from './ContributionBars.svelte';

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

	<p class="px-2 text-center text-xs leading-relaxed text-[var(--color-ink-300)]">
		本结果由预测模型生成，仅供参考。当前为演示数据。
	</p>

	<button
		type="button"
		onclick={onrestart}
		class="w-full rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] py-3.5 text-sm font-medium text-[var(--color-ink-500)] transition-colors hover:border-[var(--color-ink-300)]"
	>
		重新测评
	</button>
</div>
