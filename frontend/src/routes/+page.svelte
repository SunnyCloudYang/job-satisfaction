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
	import ModelDiagram from '$lib/components/ModelDiagram.svelte';
	import { studyMeta, variables, theories, scaleSources } from '$lib/data/research';

	type Phase = 'welcome' | 'intro' | 'survey' | 'result';
	let phase = $state<Phase>('welcome');
	let result = $state<PredictionResult | null>(null);
	let direction = $state(1); // 1 前进, -1 后退
	let introSection = $state<(typeof sections)[number] | null>(null);

	// 首页内的标签页：概览 / 研究模型 / 测量量表
	type HomeTab = 'overview' | 'model' | 'scales';
	let homeTab = $state<HomeTab>('overview');
	const homeTabs: { id: HomeTab; label: string }[] = [
		{ id: 'overview', label: '概览' },
		{ id: 'model', label: '研究模型' },
		{ id: 'scales', label: '测量量表' }
	];
	// 量表来源中仅保留问卷内实际作答的三个量表
	const surveyScales = sections.map((s) => ({ section: s, src: scaleSources[s.id] }));

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
		// 研究背景已整合到首页标签页，这里统一直接进入作答。
		enterSurvey();
	}

	// 从研究模型介绍进入正式作答
	function enterSurvey() {
		direction = 1;
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
	let predictError = $state<string | null>(null);

	async function finish() {
		if (!isComplete() || predicting) return;
		predicting = true;
		predictError = null;
		try {
			result = await predict(survey.answers);
			phase = 'result';
		} catch (err) {
			predictError = err instanceof Error ? err.message : '预测失败，请稍后重试';
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
	<title>工作满意度预测——公安人员</title>
</svelte:head>

{#if phase === 'welcome'}
	<!-- ============ 首页（标签页：概览 / 研究模型 / 测量量表） ============ -->
	<main class="flex min-h-dvh flex-col items-center px-5 py-10 sm:py-14">
		<div class="w-full max-w-xl" in:fade={{ duration: 400 }}>
			<!-- 顶部标识 -->
			<div class="flex flex-col items-center text-center">
				<div
					class="mb-5 flex size-14 items-center justify-center rounded-2xl bg-[var(--color-ink)] shadow-lg"
				>
					<svg viewBox="0 0 24 24" class="size-7 text-[var(--color-brass)]" fill="currentColor">
						<path
							d="M12 2 4 5v6c0 5 3.4 9.3 8 11 4.6-1.7 8-6 8-11V5l-8-3Zm0 6a2.5 2.5 0 0 1 2.5 2.5c0 1-.6 1.9-1.5 2.3V16h-2v-3.2A2.5 2.5 0 0 1 12 8Z"
						/>
					</svg>
				</div>
				<h1 class="text-3xl font-bold tracking-tight text-[var(--color-ink)] sm:text-4xl">
					工作满意度预测——公安人员
				</h1>
				<p class="mt-2 text-sm text-[var(--color-ink-300)]">
					{studyMeta.title} · {studyMeta.subtitle}
				</p>
			</div>

			<!-- 标签页切换 -->
			<div
				class="mx-auto mt-7 flex w-full max-w-sm rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] p-1 shadow-sm"
			>
				{#each homeTabs as t (t.id)}
					<button
						type="button"
						onclick={() => (homeTab = t.id)}
						class="flex-1 rounded-xl px-3 py-2 text-sm font-medium transition-colors {homeTab === t.id
							? 'bg-[var(--color-ink)] text-white shadow'
							: 'text-[var(--color-ink-500)] hover:text-[var(--color-ink)]'}"
					>
						{t.label}
					</button>
				{/each}
			</div>

			<!-- 标签页内容 -->
			<div class="mt-6 min-h-[19rem]">
				{#if homeTab === 'overview'}
					<!-- 概览 -->
					<div in:fade={{ duration: 250 }} class="text-center">
						<p class="mx-auto max-w-md text-base leading-relaxed text-[var(--color-ink-500)]">
							基于一项面向 <span class="tnum font-semibold text-[var(--color-ink)]"
								>{studyMeta.sample.toLocaleString()}</span
							>
							名一线警察的实证研究，通过组织公平感、主管忠诚与组织认同感三个量表的作答，为您预测工作满意度并给出针对性建议。
						</p>

						<div class="mt-8 flex justify-center gap-8 text-sm text-[var(--color-ink-300)]">
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

						<p class="mx-auto mt-8 max-w-md text-xs leading-relaxed text-[var(--color-ink-300)]">
							想先了解背后的研究模型与量表来源？切换上方「研究模型」「测量量表」标签即可，随时点击下方按钮开始测评。
						</p>
					</div>
				{:else if homeTab === 'model'}
					<!-- 研究模型 -->
					<div in:fade={{ duration: 250 }}>
						<p class="text-center text-sm leading-relaxed text-[var(--color-ink-500)]">
							{studyMeta.summary}
						</p>

						<div
							class="mt-5 rounded-3xl border border-[var(--color-line)] bg-[var(--color-surface)] p-5 shadow-sm sm:p-6"
						>
							<ModelDiagram />
							<p class="mt-3 text-center text-xs leading-relaxed text-[var(--color-ink-300)]">
								实线为效应路径，虚线为主管忠诚的调节作用。主管忠诚越高，组织公平感对组织认同感的推动反而减弱。
							</p>
						</div>

						<div class="mt-4 grid grid-cols-2 gap-3">
							{#each variables as v (v.id)}
								<div
									class="rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] p-4 shadow-sm"
								>
									<div class="flex items-center justify-between">
										<span class="text-sm font-semibold text-[var(--color-ink)]">{v.name}</span>
										<span
											class="rounded-full bg-[var(--color-brass-soft)] px-2 py-0.5 text-[10px] font-medium text-[var(--color-ink)]"
										>
											{v.roleLabel}
										</span>
									</div>
									<p class="mt-1.5 text-xs leading-relaxed text-[var(--color-ink-500)]">{v.desc}</p>
								</div>
							{/each}
						</div>

						<div
							class="mt-4 rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] p-5 shadow-sm"
						>
							<h3 class="text-sm font-semibold text-[var(--color-ink)]">理论依据</h3>
							<div class="mt-3 space-y-3">
								{#each theories as t (t.name)}
									<div class="flex gap-2.5">
										<span class="mt-1.5 size-1.5 shrink-0 rounded-full bg-[var(--color-brass)]"></span>
										<p class="text-xs leading-relaxed text-[var(--color-ink-500)]">
											<span class="font-semibold text-[var(--color-ink)]">{t.name}</span>　{t.desc}
										</p>
									</div>
								{/each}
							</div>
						</div>
					</div>
				{:else}
					<!-- 测量量表 -->
					<div in:fade={{ duration: 250 }} class="space-y-3">
						<p class="text-center text-sm leading-relaxed text-[var(--color-ink-500)]">
							测评包含以下三个标准化量表，均选自国际或国内成熟研究并具有良好信度。
						</p>
						{#each surveyScales as { section, src }, i (section.id)}
							<div
								class="rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] p-5 shadow-sm"
							>
								<div class="flex items-center justify-between">
									<h3 class="text-sm font-semibold text-[var(--color-ink)]">
										<span class="tnum mr-1.5 text-[var(--color-brass)]">{i + 1}</span>{section.title}
									</h3>
									{#if src}
										<span class="text-xs text-[var(--color-ink-300)]">{src.author}</span>
									{/if}
								</div>
								<p class="mt-1.5 text-xs leading-relaxed text-[var(--color-ink-500)]">
									{section.intro}
								</p>
								{#if src}
									<div
										class="mt-3 flex flex-wrap gap-x-4 gap-y-1 border-t border-[var(--color-line)] pt-3 text-xs text-[var(--color-ink-500)]"
									>
										<span>共 <span class="tnum">{src.items}</span> 题</span>
										<span><span class="tnum">{src.scale}</span> 级评分</span>
										<span>信度 α=<span class="tnum">{src.alpha}</span></span>
									</div>
									{#if src.note}
										<p class="mt-2 text-xs leading-relaxed text-[var(--color-ink-300)]">{src.note}</p>
									{/if}
								{/if}
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<!-- 始终可见的进入测评按钮 -->
			<div class="mt-8 space-y-3">
				<button
					type="button"
					onclick={() => start(false)}
					class="w-full rounded-2xl bg-[var(--color-ink)] py-4 text-base font-semibold text-white shadow-lg transition-all hover:bg-[var(--color-ink-700)] active:scale-[0.98]"
				>
					{hasSaved ? '重新开始测评' : '开始测评'}
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

			{#if scaleSources[introSection.id]}
				{@const src = scaleSources[introSection.id]}
				<div
					class="mx-auto mt-6 max-w-md rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] px-5 py-4 text-left shadow-sm"
				>
					<p class="text-xs font-medium uppercase tracking-widest text-[var(--color-brass)]">
						量表来源
					</p>
					<p class="mt-1.5 text-sm font-medium text-[var(--color-ink)]">{src.author}</p>
					<div class="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-[var(--color-ink-500)]">
						<span>共 <span class="tnum">{src.items}</span> 题</span>
						<span><span class="tnum">{src.scale}</span> 级评分</span>
						<span>信度 α=<span class="tnum">{src.alpha}</span></span>
					</div>
					{#if src.note}
						<p class="mt-2 text-xs leading-relaxed text-[var(--color-ink-300)]">{src.note}</p>
					{/if}
				</div>
			{/if}

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

				{#if predictError}
					<p
						class="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-center text-sm text-red-700"
						role="alert"
					>
						{predictError}
					</p>
				{/if}

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
