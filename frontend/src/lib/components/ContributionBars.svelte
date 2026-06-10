<script lang="ts">
	import type { Contribution } from '$lib/utils/predict';

	let { contributions }: { contributions: Contribution[] } = $props();

	const maxAbs = $derived(Math.max(0.001, ...contributions.map((c) => Math.abs(c.value))));
</script>

<div class="space-y-2.5">
	{#each contributions as c (c.key)}
		{@const w = (Math.abs(c.value) / maxAbs) * 50}
		{@const positive = c.value >= 0}
		<div class="flex items-center gap-3">
			<span class="w-24 shrink-0 text-right text-xs text-[var(--color-ink-500)]">{c.name}</span>
			<!-- 双向柱：中线向左为负、向右为正 -->
			<div class="relative h-5 flex-1">
				<span class="absolute left-1/2 top-0 h-full w-px bg-[var(--color-line)]"></span>
				{#if positive}
					<span
						class="absolute left-1/2 top-1/2 h-3 -translate-y-1/2 rounded-r-md transition-[width] duration-500"
						style="width: {w}%; background: var(--color-high);"
					></span>
				{:else}
					<span
						class="absolute top-1/2 h-3 -translate-y-1/2 rounded-l-md transition-[width] duration-500"
						style="right: 50%; width: {w}%; background: var(--color-low);"
					></span>
				{/if}
			</div>
			<span
				class="tnum w-12 shrink-0 text-xs"
				class:text-[var(--color-high)]={positive}
				class:text-[var(--color-low)]={!positive}
			>
				{positive ? '+' : ''}{c.value.toFixed(2)}
			</span>
		</div>
	{/each}
</div>
