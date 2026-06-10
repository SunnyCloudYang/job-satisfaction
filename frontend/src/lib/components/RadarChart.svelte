<script lang="ts">
	import type { DimensionScore } from '$lib/utils/predict';

	let { dimensions }: { dimensions: DimensionScore[] } = $props();

	const size = 320;
	const cx = size / 2;
	const cy = size / 2;
	const r = size / 2 - 54;
	const n = $derived(dimensions.length);

	function point(value: number, i: number, radius = r) {
		const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
		return {
			x: cx + Math.cos(angle) * radius * value,
			y: cy + Math.sin(angle) * radius * value
		};
	}

	function polygon(values: number[]) {
		return values.map((v, i) => `${point(v, i).x},${point(v, i).y}`).join(' ');
	}

	const userPoly = $derived(polygon(dimensions.map((d) => d.normalized)));
	const samplePoly = $derived(polygon(dimensions.map((d) => d.sampleNormalized)));
	const grid = [0.25, 0.5, 0.75, 1];
</script>

<div class="flex flex-col items-center">
	<svg viewBox="0 0 {size} {size}" class="w-full max-w-[340px]" role="img" aria-label="维度雷达图">
		<!-- 网格 -->
		{#each grid as g (g)}
			<polygon
				points={dimensions.map((_, i) => `${point(g, i).x},${point(g, i).y}`).join(' ')}
				fill="none"
				stroke="var(--color-line)"
				stroke-width="1"
			/>
		{/each}

		<!-- 轴线 -->
		{#each dimensions as _, i (i)}
			{@const p = point(1, i)}
			<line x1={cx} y1={cy} x2={p.x} y2={p.y} stroke="var(--color-line)" stroke-width="1" />
		{/each}

		<!-- 样本参照 -->
		<polygon
			points={samplePoly}
			fill="color-mix(in srgb, var(--color-ink-300) 14%, transparent)"
			stroke="var(--color-ink-300)"
			stroke-width="1.5"
			stroke-dasharray="4 3"
		/>

		<!-- 用户得分 -->
		<polygon
			points={userPoly}
			fill="color-mix(in srgb, var(--color-brass) 22%, transparent)"
			stroke="var(--color-brass)"
			stroke-width="2"
		/>
		{#each dimensions as d, i (d.key)}
			{@const p = point(d.normalized, i)}
			<circle cx={p.x} cy={p.y} r="3" fill="var(--color-brass)" />
		{/each}

		<!-- 维度标签 -->
		{#each dimensions as d, i (d.key)}
			{@const p = point(1.18, i)}
			<text
				x={p.x}
				y={p.y}
				text-anchor="middle"
				dominant-baseline="middle"
				font-size="11"
				fill="var(--color-ink-500)"
			>
				{d.name}
			</text>
		{/each}
	</svg>

	<div class="mt-2 flex gap-5 text-xs text-[var(--color-ink-500)]">
		<span class="flex items-center gap-1.5">
			<span class="inline-block h-2 w-4 rounded-full bg-[var(--color-brass)]"></span> 您的得分
		</span>
		<span class="flex items-center gap-1.5">
			<span class="inline-block h-2 w-4 rounded-full border border-dashed border-[var(--color-ink-300)]"></span>
			样本平均
		</span>
	</div>
</div>
