<script lang="ts">
	let {
		scale,
		labels,
		value,
		onselect
	}: {
		scale: 5 | 7;
		labels: string[];
		value: number | undefined;
		onselect: (v: number) => void;
	} = $props();

	const points = $derived(Array.from({ length: scale }, (_, i) => i + 1));
</script>

<div class="select-none">
	<!-- 两端锚点标签 -->
	<div class="mb-3 flex justify-between text-xs text-[var(--color-ink-300)]">
		<span>{labels[0]}</span>
		<span>{labels[labels.length - 1]}</span>
	</div>

	<!-- 刻度块 -->
	<div
		class="grid gap-1.5 sm:gap-2"
		style="grid-template-columns: repeat({scale}, minmax(0, 1fr));"
		role="radiogroup"
		aria-label="评分"
	>
		{#each points as p (p)}
			{@const selected = value === p}
			<button
				type="button"
				role="radio"
				aria-checked={selected}
				aria-label={labels[p - 1] ?? String(p)}
				onclick={() => onselect(p)}
				class="group relative flex h-14 flex-col items-center justify-center rounded-xl border text-base font-semibold transition-all duration-150 active:scale-95 sm:h-16"
				class:selected
				class:border-[var(--color-line)]={!selected}
				class:bg-[var(--color-surface)]={!selected}
				class:text-[var(--color-ink-500)]={!selected}
				class:hover:border-[var(--color-ink-300)]={!selected}
			>
				<span class="tnum">{p}</span>
			</button>
		{/each}
	</div>

	<!-- 选中项的语义标签 -->
	<div class="mt-3 h-5 text-center text-sm">
		{#if value}
			<span class="font-medium text-[var(--color-ink)]">{labels[value - 1]}</span>
		{:else}
			<span class="text-[var(--color-ink-300)]">请选择一个选项</span>
		{/if}
	</div>
</div>

<style>
	.selected {
		border-color: var(--color-ink);
		background-color: var(--color-ink);
		color: #fff;
		box-shadow: 0 6px 16px -6px color-mix(in srgb, var(--color-ink) 55%, transparent);
		transform: translateY(-2px);
	}
</style>
