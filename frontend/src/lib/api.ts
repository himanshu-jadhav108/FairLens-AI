import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 60000, // 60s timeout for long-running SHAP tasks
});

/**
 * Handle API errors consistently.
 */
export const getErrorMessage = (err: any): string => {
  if (err.response) {
    return err.response.data?.detail || `Server error (${err.response.status})`;
  } else if (err.request) {
    return "No response from server. Is the backend running?";
  } else {
    return err.message || "An unexpected error occurred";
  }
};

/**
 * Check if the backend is reachable.
 */
export const checkHealth = async () => {
  try {
    const response = await api.get("/health");
    return response.status === 200;
  } catch (err) {
    return false;
  }
};

const toAnalysisResult = (payload: any) => {
  const metrics = payload?.metrics || {};
  const modelInfo = payload?.model_info || {};
  const groups = metrics?.group_stats?.groups || [];

  return {
    dpd: Number(metrics?.demographic_parity_difference || 0),
    eod: Number(metrics?.equalized_odds_difference || 0),
    accuracy: Number(metrics?.accuracy || 0),
    group_stats: groups,
    model_info: {
      model_type: modelInfo?.type || "Logistic Regression",
      features_used: Number(modelInfo?.features_used || 0),
      test_samples: Number(modelInfo?.test_samples || 0),
      groups_found: groups.length,
    },
  };
};

const toAiExplanation = (payload: any) => ({
  explanation: payload?.explanation || "No explanation available.",
  summary: {
    verdict: payload?.summary?.overall_verdict || "unknown",
    dpd_severity: payload?.summary?.demographic_parity_severity || "unknown",
    eod_severity: payload?.summary?.equalized_odds_severity || "unknown",
  },
});

const toFixResult = (payload: any) => {
  const before = payload?.original_metrics || {};
  const after = payload?.fixed_metrics || {};

  const beforeGroups = before?.group_stats?.groups || [];
  const afterGroups = after?.group_stats?.groups || [];

  const group_rates_before = Object.fromEntries(
    beforeGroups.map((g: any) => [String(g.group), Number(g.positive_rate || 0)])
  );
  const group_rates_after = Object.fromEntries(
    afterGroups.map((g: any) => [String(g.group), Number(g.positive_rate || 0)])
  );

  return {
    strategy: payload?.strategy || "Reweighting + Drop Sensitive Feature",
    original_metrics: {
      dpd: Number(before?.demographic_parity_difference || 0),
      eod: Number(before?.equalized_odds_difference || 0),
      accuracy: Number(before?.accuracy || 0),
    },
    fixed_metrics: {
      dpd: Number(after?.demographic_parity_difference || 0),
      eod: Number(after?.equalized_odds_difference || 0),
      accuracy: Number(after?.accuracy || 0),
    },
    comparison: {
      group_rates_before,
      group_rates_after,
    },
  };
};

export const uploadFile = async (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post("/api/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
};

export const analyzeData = async (targetCol: string, sensitiveCol: string) => {
  const response = await api.post("/api/analyze", {
    target_col: targetCol,
    sensitive_col: sensitiveCol,
  });
  return toAnalysisResult(response.data);
};

export const explainShap = async () => {
  const response = await api.post("/api/explain");
  return response.data;
};

export const aiExplain = async () => {
  const response = await api.post("/api/ai-explain");
  return toAiExplanation(response.data);
};

export const applyFix = async () => {
  const response = await api.post("/api/fix");
  return toFixResult(response.data);
};

export default api;
