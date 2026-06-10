<script lang="ts">
	import { sectionMeta } from '$lib/data/questions';

	// 签名元素：贯穿顶部的分段刻度轨道。
	// 四段（基本信息 / 组织公平感 / 主管忠诚 / 组织认同感）像值勤路线上的打卡点。
	let { current, total }: { current: number; total: number } = $props();

	// 计算每段的起始索引
	const segments = $derived.by(() => {
		let start = 0;
		return sectionMeta.map((m) => {
			const seg = { ...m, start, end: start + m.count };
			start += m.count;
			return seg;
		});
	});

	const pct = $derived(total > 0 ? (current / total) * 100 : 0);
	const activeSeg = $derived(segments.find((s) => current >= s.start && current < s.end) ?? segments[0]);
</script>

<div class="w-full">
	<div class="mb-2 flex items-center justify-between text-xs">
		<span class="font-medium text-[var(--color-ink-500)]">
			{activeSeg.title}
		</span>
		<span class="tnum text-[var(--color-ink-300)]">
			{Math.min(current + 1, total)} / {total}
		</span>
	</div>

	<!-- 轨道 -->
	<div class="relative h-[3px] w-full rounded-full bg-[var(--color-line)]">
		<div
			class="absolute left-0 top-0 h-full rounded-full bg-[var(--color-brass)] transition-[width] duration-500 ease-out"
			style="width: {pct}%"
		></div>

		<!-- 段落分隔节点（打卡点） -->
		{#each segments as seg (seg.id)}
			{@const nodePct = (seg.start / total) * 100}
			{@const reached = current >= seg.start}
			<span
				class="absolute top-1/2 size-2 -translate-x-1/2 -translate-y-1/2 rounded-full border transition-colors duration-300"
				class:bg-[var(--color-brass)]={reached}
				class:border-[var(--color-brass)]={reached}
				class:bg-[var(--color-surface)]={!reached}
				class:border-[var(--color-line)]={!reached}
				style="left: {nodePct}%"
			></span>
		{/each}
	</div>
</div>
