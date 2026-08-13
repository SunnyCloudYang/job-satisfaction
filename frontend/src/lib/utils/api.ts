// 预测 API 客户端：调用后端 Flask /api/predict（地址由 PUBLIC_API_BASE 配置）。
import { env } from '$env/dynamic/public';
import type { PredictionResult } from './predict';

const API_BASE = (env.PUBLIC_API_BASE ?? '').replace(/\/$/, '');

/**
 * 调用后端预测，返回结构与 PredictionResult 完全一致。
 * 未配置后端地址或请求失败时抛出错误。
 */
export async function predict(
	answers: Record<string, number | string>
): Promise<PredictionResult> {
	if (!API_BASE) {
		throw new Error('未配置后端地址（PUBLIC_API_BASE）');
	}

	const ctrl = new AbortController();
	const timeout = setTimeout(() => ctrl.abort(), 8000);
	try {
		const res = await fetch(`${API_BASE}/api/predict`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ answers }),
			signal: ctrl.signal
		});

		if (!res.ok) throw new Error(`后端响应异常（${res.status}）`);

		const data = (await res.json()) as PredictionResult;
		if (typeof data?.score !== 'number' || !Array.isArray(data?.dimensions)) {
			throw new Error('后端返回数据格式异常');
		}
		return data;
	} catch (err) {
		if (err instanceof DOMException && err.name === 'AbortError') {
			throw new Error('请求超时，请稍后重试');
		}
		throw err instanceof Error ? err : new Error('预测请求失败');
	} finally {
		clearTimeout(timeout);
	}
}
