<script lang="ts">
	// 有调节的中介模型示意图：
	//   组织公平感 ──直接效应──▶ 工作满意度
	//        │                      ▲
	//        └──▶ 组织认同感 ───────┘ (中介)
	//             ▲
	//          主管忠诚 (负向调节 公平感→认同感)
	import { pathEffects } from '$lib/data/research';

	// 是否展示效应系数标注（结果页可关闭以保持简洁）
	let { showEffects = true }: { showEffects?: boolean } = $props();
</script>

<div class="w-full">
	<svg viewBox="0 0 388 220" class="w-full" role="img" aria-label="有调节的中介模型示意图">
		<defs>
			<marker
				id="arrow"
				viewBox="0 0 10 10"
				refX="9"
				refY="5"
				markerWidth="6"
				markerHeight="6"
				orient="auto-start-reverse"
			>
				<path d="M0 0 L10 5 L0 10 z" fill="var(--color-ink-300)" />
			</marker>
			<marker
				id="arrow-brass"
				viewBox="0 0 10 10"
				refX="9"
				refY="5"
				markerWidth="6"
				markerHeight="6"
				orient="auto-start-reverse"
			>
				<path d="M0 0 L10 5 L0 10 z" fill="var(--color-brass)" />
			</marker>
		</defs>

		<!-- 路径线 -->
		<!-- 公平感 → 满意度（直接效应） -->
		<path
			d="M88 56 C 170 56, 210 90, 280 90"
			fill="none"
			stroke="var(--color-ink-300)"
			stroke-width="1.6"
			marker-end="url(#arrow)"
		/>
		<!-- 公平感 → 认同感（a 路径） -->
		<path
			d="M70 74 L 70 128"
			fill="none"
			stroke="var(--color-ink-300)"
			stroke-width="1.6"
			marker-end="url(#arrow)"
		/>
		<!-- 认同感 → 满意度（b 路径） -->
		<path
			d="M112 146 C 190 146, 215 110, 278 100"
			fill="none"
			stroke="var(--color-ink-300)"
			stroke-width="1.6"
			marker-end="url(#arrow)"
		/>
		<!-- 主管忠诚 → a 路径（调节，从节点上沿出发，箭头水平切入 a 路径中点 (70,101)） -->
		<path
			d="M245 170 C 245 132, 145 101, 73 101"
			fill="none"
			stroke="var(--color-brass)"
			stroke-width="1.6"
			stroke-dasharray="4 3"
			marker-end="url(#arrow-brass)"
		/>

		<!-- 效应标注 -->
		{#if showEffects}
			<text x="178" y="58" class="lbl" fill="var(--color-ink-500)"
				>直接 β={pathEffects.directEffect}</text
			>
			<text x="20" y="106" class="lbl" fill="var(--color-ink-500)">a</text>
			<text x="196" y="122" class="lbl" fill="var(--color-ink-500)">b</text>
			<text x="150" y="124" class="lbl" fill="var(--color-brass)"
				>负向调节 B={pathEffects.moderationB}</text
			>
		{/if}

		<!-- 节点：组织公平感（自变量） -->
		<g>
			<rect x="20" y="40" width="100" height="32" rx="9" fill="var(--color-ink)" />
			<text x="70" y="60" class="node-t" fill="#fff">组织公平感</text>
		</g>

		<!-- 节点：组织认同感（中介） -->
		<g>
			<rect
				x="20"
				y="130"
				width="100"
				height="32"
				rx="9"
				fill="var(--color-surface)"
				stroke="var(--color-ink)"
				stroke-width="1.5"
			/>
			<text x="70" y="150" class="node-t" fill="var(--color-ink)">组织认同感</text>
		</g>

		<!-- 节点：工作满意度（因变量） -->
		<g>
			<rect x="278" y="74" width="100" height="32" rx="9" fill="var(--color-high)" />
			<text x="328" y="94" class="node-t" fill="#fff">工作满意度</text>
		</g>

		<!-- 节点：主管忠诚（调节） -->
		<g>
			<rect
				x="195"
				y="170"
				width="100"
				height="32"
				rx="9"
				fill="var(--color-brass-soft)"
				stroke="var(--color-brass)"
				stroke-width="1.5"
			/>
			<text x="245" y="190" class="node-t" fill="var(--color-ink)">主管忠诚</text>
		</g>
	</svg>
</div>

<style>
	.node-t {
		font-size: 11px;
		font-weight: 600;
		text-anchor: middle;
		dominant-baseline: middle;
	}
	.lbl {
		font-size: 8px;
		text-anchor: middle;
	}
</style>
