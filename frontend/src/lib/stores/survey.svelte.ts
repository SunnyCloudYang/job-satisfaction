// 答题状态管理（Svelte 5 runes）+ localStorage 中途保存。
import { browser } from '$app/environment';
import { buildSteps, TOTAL_STEPS, type Step } from '$lib/data/questions';

const STORAGE_KEY = 'jsp_survey_progress_v1';

export interface SurveyState {
	currentIndex: number;
	/** answerKey -> 选项值（Likert 为数字，人口学为字符串） */
	answers: Record<string, number | string>;
	timestamp: number;
}

interface Persisted {
	currentIndex: number;
	answers: Record<string, number | string>;
	timestamp: number;
}

function load(): Persisted | null {
	if (!browser) return null;
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		if (!raw) return null;
		const data = JSON.parse(raw) as Persisted;
		if (typeof data.currentIndex !== 'number' || typeof data.answers !== 'object') return null;
		return data;
	} catch {
		return null;
	}
}

export const steps: Step[] = buildSteps();
export const total = TOTAL_STEPS;

export const survey = $state<SurveyState>({
	currentIndex: 0,
	answers: {},
	timestamp: 0
});

let dirty = $state(false);

/** 检测是否存在上次未完成的进度（不自动加载，交由 UI 询问） */
export function hasSavedProgress(): boolean {
	const data = load();
	return !!data && Object.keys(data.answers).length > 0 && data.currentIndex < total;
}

export function savedSummary(): { answered: number; timestamp: number } | null {
	const data = load();
	if (!data) return null;
	return { answered: Object.keys(data.answers).length, timestamp: data.timestamp };
}

export function resumeSaved() {
	const data = load();
	if (!data) return;
	survey.currentIndex = Math.min(data.currentIndex, total - 1);
	survey.answers = { ...data.answers };
	survey.timestamp = data.timestamp;
}

export function resetSurvey() {
	survey.currentIndex = 0;
	survey.answers = {};
	survey.timestamp = Date.now();
	if (browser) localStorage.removeItem(STORAGE_KEY);
}

export function persist() {
	if (!browser) return;
	survey.timestamp = Date.now();
	localStorage.setItem(
		STORAGE_KEY,
		JSON.stringify({
			currentIndex: survey.currentIndex,
			answers: survey.answers,
			timestamp: survey.timestamp
		})
	);
}

export function clearStorage() {
	if (browser) localStorage.removeItem(STORAGE_KEY);
}

/** 当前步骤的作答键 */
function keyOf(step: Step): string {
	return step.kind === 'demographic' ? step.q.key : step.answerKey;
}

export function answerCurrent(value: number | string) {
	const step = steps[survey.currentIndex];
	survey.answers[keyOf(step)] = value;
	dirty = true;
	persist();
}

export function getAnswer(step: Step): number | string | undefined {
	return survey.answers[keyOf(step)];
}

export function next() {
	if (survey.currentIndex < total - 1) {
		survey.currentIndex += 1;
		persist();
	}
}

export function prev() {
	if (survey.currentIndex > 0) {
		survey.currentIndex -= 1;
		persist();
	}
}

export function goTo(index: number) {
	survey.currentIndex = Math.max(0, Math.min(index, total - 1));
	persist();
}

export function answeredCount(): number {
	return Object.keys(survey.answers).length;
}

export function isComplete(): boolean {
	return steps.every((s) => survey.answers[keyOf(s)] !== undefined);
}
