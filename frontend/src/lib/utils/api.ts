// 预测 API 客户端。
// - 优先调用后端 Flask /api/predict（地址由 PUBLIC_API_BASE 配置）。
// - 后端不可用或未配置时，自动回退到本地 mockPredict，保证静态站点可独立运行。
import { env } from '$env/dynamic/public';
import { mockPredict, type PredictionResult } from './predict';

// 使用 dynamic public env，未配置时为空字符串（回退到 mock），
// 无需在构建期强制定义 PUBLIC_API_BASE。
const API_BASE = (env.PUBLIC_API_BASE ?? '').replace(/\/$/, '');

/** 是否配置了后端地址 */
export function hasBackend(): boolean {
	return API_BASE.length > 0;
}

/**
 * 调用后端预测；失败时回退到本地 mock。
 * 返回结构与 PredictionResult 完全一致。
 */
export async function predict(
	answers: Record<string, number | string>
): Promise<{ result: PredictionResult; source: 'backend' | 'mock' }> {
	if (!hasBackend()) {
		return { result: mockPredict(answers), source: 'mock' };
	}

	try {
		const ctrl = new AbortController();
		const timeout = setTimeout(() => ctrl.abort(), 8000);
		const res = await fetch(`${API_BASE}/api/predict`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ answers }),
			signal: ctrl.signal
		});
		clearTimeout(timeout);

		if (!res.ok) throw new Error(`backend responded ${res.status}`);
		const data = (await res.json()) as PredictionResult;
		// 基本校验，字段缺失则回退
		if (typeof data?.score !== 'number' || !Array.isArray(data?.dimensions)) {
			throw new Error('unexpected backend payload');
		}
		return { result: data, source: 'backend' };
	} catch (err) {
		console.warn('[predict] backend unavailable, falling back to mock:', err);
		return { result: mockPredict(answers), source: 'mock' };
	}
}
