<script lang="ts">
	import { fly, fade } from 'svelte/transition';
	import { sections } from '$lib/data/questions';
	import ProgressTrack from '$lib/components/ProgressTrack.svelte';
	import LikertScale from '$lib/components/LikertScale.svelte';
	import DemoSelect from '$lib/components/DemoSelect.svelte';
	import ResultPanel from '$lib/components/ResultPanel.svelte';
	import {
		survey,
		steps,
		total,
		answerCurrent,
		getAnswer,
		next,
		prev,
		resetSurvey,
		resumeSaved,
		savedSummary,
		isComplete
	} from '$lib/stores/survey.svelte';
	import { type PredictionResult } from '$lib/utils/predict';
	import { predict } from '$lib/utils/api';

	type Phase = 'welcome' | 'intro' | 'survey' | 'result';
	let phase = $state<Phase>('welcome');
	let result = $state<PredictionResult | null>(null);
	let direction = $state(1); // 1 前进, -1 后退
	let introSection = $state<(typeof sections)[number] | null>(null);

	const saved = savedSummary();
	const hasSaved = !!saved && saved.answered > 0 && saved.answered < total;

	const current = $derived(steps[survey.currentIndex]);
	const currentAnswer = $derived(getAnswer(current));
	const answered = $derived(currentAnswer !== undefined);

	// 判断进入新的 likert 段落时是否需要展示指导语
	function maybeIntro(prevIdx: number, nextIdx: number): boolean {
		const a = steps[prevIdx];
		const b = steps[nextIdx];
		if (b.kind !== 'likert') return false;
		const prevSection = a.kind === 'likert' ? a.sectionId : null;
		if (b.sectionId !== prevSection) {
			introSection = sections.find((s) => s.id === b.sectionId) ?? null;
			return true;
		}
		return false;
	}

	function start(resume = false) {
		if (resume) resumeSaved();
		else resetSurvey();
		direction = 1;
		// 起始若直接进入 likert 段，先看指导语
		const first = steps[survey.currentIndex];
		if (first.kind === 'likert') {
			introSection = sections.find((s) => s.id === first.sectionId) ?? null;
			phase = 'intro';
		} else {
			phase = 'survey';
		}
	}

	function handleSelect(v: number | string) {
		answerCurrent(v);
		// 作答后短暂延迟自动前进，给一点反馈时间
		setTimeout(() => goNext(), 220);
	}

	function goNext() {
		if (survey.currentIndex >= total - 1) {
			finish();
			return;
		}
		const from = survey.currentIndex;
		const to = from + 1;
		direction = 1;
		if (maybeIntro(from, to)) {
			next();
			phase = 'intro';
		} else {
			next();
		}
	}

	function goPrev() {
		if (survey.currentIndex === 0) return;
		direction = -1;
		prev();
	}

	function dismissIntro() {
		phase = 'survey';
	}

	let predicting = $state(false);

	async function finish() {
		if (!isComplete() || predicting) return;
		predicting = true;
		try {
			const { result: r } = await predict(survey.answers);
			result = r;
			phase = 'result';
		} finally {
			predicting = false;
		}
	}

	function restart() {
		resetSurvey();
		result = null;
		phase = 'welcome';
	}

	function fmtTime(ts: number): string {
		const d = new Date(ts);
		return `${d.getMonth() + 1}月${d.getDate()}日 ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
	}
</script>

<svelte:head>
	<title>工作满意度预测</title>
</svelte:head>

{#if phase === 'welcome'}
	<!-- ============ 欢迎页 ============ -->
	<main class="flex min-h-dvh flex-col items-center justify-center px-6 py-12">
		<div class="w-full max-w-lg text-center" in:fade={{ duration: 400 }}>
			<div
				class="mx-auto mb-8 flex size-16 items-center justify-center rounded-2xl bg-[var(--color-ink)] shadow-lg"
			>
				<svg viewBox="0 0 24 24" class="size-8 text-[var(--color-brass)]" fill="currentColor">
					<path
						d="M12 2 4 5v6c0 5 3.4 9.3 8 11 4.6-1.7 8-6 8-11V5l-8-3Zm0 6a2.5 2.5 0 0 1 2.5 2.5c0 1-.6 1.9-1.5 2.3V16h-2v-3.2A2.5 2.5 0 0 1 12 8Z"
					/>
				</svg>
			</div>

			<h1 class="text-3xl font-bold tracking-tight text-[var(--color-ink)] sm:text-4xl">
				工作满意度预测
			</h1>
			<p class="mx-auto mt-4 max-w-md text-base leading-relaxed text-[var(--color-ink-500)]">
				通过组织公平感、主管忠诚与组织认同感三个维度的作答，为您预测工作满意度，并给出针对性的改善建议。
			</p>

			<div class="mt-8 flex justify-center gap-6 text-sm text-[var(--color-ink-300)]">
				<span class="flex flex-col items-center gap-1">
					<span class="tnum text-2xl font-semibold text-[var(--color-ink)]">{total}</span> 道题目
				</span>
				<span class="flex flex-col items-center gap-1">
					<span class="tnum text-2xl font-semibold text-[var(--color-ink)]">~5</span> 分钟
				</span>
				<span class="flex flex-col items-center gap-1">
					<span class="tnum text-2xl font-semibold text-[var(--color-ink)]">3</span> 个量表
				</span>
			</div>

			<div class="mt-10 space-y-3">
				<button
					type="button"
					onclick={() => start(false)}
					class="w-full rounded-2xl bg-[var(--color-ink)] py-4 text-base font-semibold text-white shadow-lg transition-all hover:bg-[var(--color-ink-700)] active:scale-[0.98]"
				>
					{hasSaved ? '重新开始' : '开始测评'}
				</button>

				{#if hasSaved && saved}
					<button
						type="button"
						onclick={() => start(true)}
						class="w-full rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] py-3.5 text-sm font-medium text-[var(--color-ink-500)] transition-colors hover:border-[var(--color-ink-300)]"
					>
						继续上次（已答 {saved.answered} 题 · {fmtTime(saved.timestamp)}）
					</button>
				{/if}
			</div>
		</div>
	</main>
{:else if phase === 'intro' && introSection}
	<!-- ============ 段落指导语 ============ -->
	<main class="flex min-h-dvh flex-col items-center justify-center px-6 py-12">
		<div class="w-full max-w-lg text-center" in:fly={{ y: 16, duration: 400 }}>
			<p class="text-sm font-medium uppercase tracking-widest text-[var(--color-brass)]">
				量表 {sections.findIndex((s) => s.id === introSection!.id) + 1} / {sections.length}
			</p>
			<h2 class="mt-3 text-2xl font-bold text-[var(--color-ink)] sm:text-3xl">
				{introSection.title}
			</h2>
			<p class="mx-auto mt-4 max-w-md text-base leading-relaxed text-[var(--color-ink-500)]">
				{introSection.intro}
			</p>
			<button
				type="button"
				onclick={dismissIntro}
				class="mt-8 rounded-2xl bg-[var(--color-ink)] px-10 py-3.5 text-base font-semibold text-white shadow-lg transition-all hover:bg-[var(--color-ink-700)] active:scale-[0.98]"
			>
				继续
			</button>
		</div>
	</main>
{:else if phase === 'survey'}
	<!-- ============ 逐题作答 ============ -->
	<div class="flex min-h-dvh flex-col">
		<!-- 顶部进度轨道 -->
		<header
			class="sticky top-0 z-10 border-b border-[var(--color-line)] bg-[color-mix(in_srgb,var(--color-canvas)_85%,transparent)] px-4 py-3 backdrop-blur-md sm:px-6"
		>
			<div class="mx-auto max-w-xl">
				<ProgressTrack current={survey.currentIndex} {total} />
			</div>
		</header>

		<!-- 题目卡片 -->
		<main class="flex flex-1 items-center justify-center px-4 py-8 sm:px-6">
			<div class="w-full max-w-xl">
				{#key survey.currentIndex}
					<div
						in:fly={{ x: direction * 40, duration: 280, opacity: 0 }}
						class="rounded-3xl border border-[var(--color-line)] bg-[var(--color-surface)] p-6 shadow-sm sm:p-8"
					>
						{#if current.kind === 'demographic'}
							<p class="mb-1 text-xs font-medium uppercase tracking-widest text-[var(--color-brass)]">
								基本信息
							</p>
							<h2 class="mb-6 text-xl font-semibold leading-snug text-[var(--color-ink)] sm:text-2xl">
								{current.q.prompt}
							</h2>
							<DemoSelect
								options={current.q.options}
								value={currentAnswer as string | undefined}
								onselect={handleSelect}
							/>
						{:else}
							<div class="mb-1 flex items-center justify-between">
								<p class="text-xs font-medium uppercase tracking-widest text-[var(--color-brass)]">
									{current.sectionTitle} · {current.dimensionName}
								</p>
							</div>
							<h2 class="mb-7 text-xl font-semibold leading-snug text-[var(--color-ink)] sm:text-2xl">
								{current.text}
							</h2>
							<LikertScale
								scale={current.scale}
								labels={current.labels}
								value={currentAnswer as number | undefined}
								onselect={handleSelect}
							/>
						{/if}
					</div>
				{/key}

				<!-- 导航 -->
				<div class="mt-6 flex items-center justify-between">
					<button
						type="button"
						onclick={goPrev}
						disabled={survey.currentIndex === 0}
						class="flex items-center gap-1.5 rounded-xl px-4 py-2.5 text-sm font-medium text-[var(--color-ink-500)] transition-colors hover:bg-[var(--color-surface)] disabled:cursor-not-allowed disabled:opacity-30"
					>
						<svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="2">
							<path d="m15 18-6-6 6-6" stroke-linecap="round" stroke-linejoin="round" />
						</svg>
						上一题
					</button>

					<span class="text-xs text-[var(--color-ink-300)]">进度自动保存</span>

					{#if survey.currentIndex === total - 1 && answered}
						<button
							type="button"
							onclick={finish}
							disabled={predicting}
							class="flex items-center gap-2 rounded-xl bg-[var(--color-ink)] px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-[var(--color-ink-700)] disabled:cursor-not-allowed disabled:opacity-60"
						>
							{#if predicting}
								<svg class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
									<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
									<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.4 0 0 5.4 0 12h4z" />
								</svg>
								预测中…
							{:else}
								查看结果
							{/if}
						</button>
					{:else}
						<button
							type="button"
							onclick={goNext}
							disabled={!answered}
							class="flex items-center gap-1.5 rounded-xl px-4 py-2.5 text-sm font-medium text-[var(--color-ink-500)] transition-colors hover:bg-[var(--color-surface)] disabled:cursor-not-allowed disabled:opacity-30"
						>
							下一题
							<svg
								viewBox="0 0 24 24"
								class="size-4"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
							>
								<path d="m9 18 6-6-6-6" stroke-linecap="round" stroke-linejoin="round" />
							</svg>
						</button>
					{/if}
				</div>
			</div>
		</main>
	</div>
{:else if phase === 'result' && result}
	<!-- ============ 结果页 ============ -->
	<main class="min-h-dvh" in:fade={{ duration: 400 }}>
		<ResultPanel {result} onrestart={restart} />
	</main>
{/if}
