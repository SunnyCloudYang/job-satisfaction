<script lang="ts">
	let {
		options,
		value,
		onselect
	}: {
		options: { value: string; label: string }[];
		value: string | undefined;
		onselect: (v: string) => void;
	} = $props();
</script>

<div class="grid gap-3" class:sm:grid-cols-2={options.length > 3}>
	{#each options as opt (opt.value)}
		{@const selected = value === opt.value}
		<button
			type="button"
			onclick={() => onselect(opt.value)}
			class="flex items-center justify-between rounded-2xl border px-5 py-4 text-left text-base font-medium transition-all duration-150 active:scale-[0.98]"
			class:selected
			class:border-[var(--color-line)]={!selected}
			class:bg-[var(--color-surface)]={!selected}
			class:text-[var(--color-ink-500)]={!selected}
			class:hover:border-[var(--color-ink-300)]={!selected}
		>
			<span>{opt.label}</span>
			<span
				class="flex size-5 items-center justify-center rounded-full border-2 transition-colors"
				class:border-white={selected}
				class:border-[var(--color-line)]={!selected}
			>
				{#if selected}
					<span class="size-2.5 rounded-full bg-white"></span>
				{/if}
			</span>
		</button>
	{/each}
</div>

<style>
	.selected {
		border-color: var(--color-ink);
		background-color: var(--color-ink);
		color: #fff;
		box-shadow: 0 8px 20px -8px color-mix(in srgb, var(--color-ink) 50%, transparent);
	}
</style>
