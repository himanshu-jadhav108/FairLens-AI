import { useApp } from "@/context/AppContext";
import { applyFix, getErrorMessage } from "@/lib/api";
import ScanLineLoader from "@/components/shared/ScanLineLoader";
import ErrorAlert from "@/components/shared/ErrorAlert";
import StaggerItem from "@/components/shared/StaggerItem";
import MetricDeltaRow from "./MetricDeltaRow";
import BeforeAfterChart from "./BeforeAfterChart";

export default function FixBiasSection() {
  const { state, dispatch } = useApp();
  const { fixResult, loading, errors, sensitiveCol } = state;

  const runFix = async () => {
    dispatch({ type: "SET_LOADING", payload: { key: "fix", value: true } });
    dispatch({ type: "SET_ERROR", payload: { key: "fix", value: null } });
    try {
      const data = await applyFix();
      dispatch({ type: "SET_FIX_RESULT", payload: data });
    } catch (err: any) {
      const msg = getErrorMessage(err);
      if (msg.includes("SESSION_EXPIRED")) {
        dispatch({ type: "HANDLE_SESSION_EXPIRED", payload: "Your session has expired or the backend was restarted. Please re-upload your data." });
      } else {
        dispatch({ type: "SET_ERROR", payload: { key: "fix", value: msg } });
      }
    } finally {
      dispatch({ type: "SET_LOADING", payload: { key: "fix", value: false } });
    }
  };

  const strategies = [
    { icon: "⚖️", name: "Sample Reweighting", desc: "Rebalances training samples so all groups are equally represented during learning." },
    { icon: "🚫", name: "Drop Sensitive Feature", desc: `Removes ${sensitiveCol || "sensitive column"} from model input to prevent direct discrimination.` },
    { icon: "🔄", name: "Retrain Model", desc: "Retrains Logistic Regression with the balanced, de-sensitized dataset." },
  ];

  return (
    <div className="space-y-6">
      {/* Strategy Overview */}
      <StaggerItem index={0}>
        <div className="card-border rounded-lg bg-background-surface overflow-hidden">
          <div className="p-5 border-b border-border">
            <h2 className="font-display font-bold text-foreground text-lg">⚙️ Mitigation Strategy</h2>
          </div>
          <div className="p-5 space-y-3">
            {strategies.map((s, i) => (
              <StaggerItem key={s.name} index={i + 1} delay={100}>
                <div
                  className="flex items-center justify-between p-4 rounded-lg bg-background-elevated border border-border-subtle"
                  style={{ borderLeftWidth: 2, borderLeftColor: "hsl(168 47% 52%)" }}
                >
                  <div className="flex items-start gap-3">
                    <span className="text-xl">{s.icon}</span>
                    <div>
                      <p className="font-display text-sm text-foreground font-bold">{s.name}</p>
                      <p className="text-foreground-muted text-xs font-mono mt-1">{s.desc}</p>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-success/15 text-success">Active</span>
                </div>
              </StaggerItem>
            ))}
          </div>
        </div>
      </StaggerItem>

      {/* CTA / Success */}
      {errors.fix && (
        <ErrorAlert
          message={errors.fix}
          onDismiss={() => dispatch({ type: "SET_ERROR", payload: { key: "fix", value: null } })}
        />
      )}

      {!fixResult ? (
        loading.fix ? (
          <div className="card-border rounded-lg bg-background-surface p-8">
            <ScanLineLoader />
            <p className="text-center text-foreground-muted text-sm mt-4 font-mono">Applying Mitigation…</p>
          </div>
        ) : (
          <StaggerItem index={4}>
            <button
              onClick={runFix}
              className="w-full py-3 rounded-lg bg-warning text-warning-foreground font-display font-bold text-sm hover:opacity-90 transition-opacity duration-200"
            >
              🛠 Apply Bias Fix Now
            </button>
          </StaggerItem>
        )
      ) : (
        <>
          {/* Success callout */}
          <StaggerItem index={4}>
            <div className="rounded-lg bg-success/5 border border-success/20 p-4 flex items-center gap-3">
              <span className="text-success text-lg">✅</span>
              <div>
                <p className="font-display text-sm text-foreground font-bold">Mitigation Applied</p>
                <p className="text-foreground-muted text-xs font-mono mt-0.5">
                  Strategy: <span className="text-primary">{fixResult.strategy}</span> — scroll down to view comparison
                </p>
              </div>
            </div>
          </StaggerItem>

          {/* Before/After Metric Deltas */}
          <StaggerItem index={5}>
            <div className="card-border rounded-lg bg-background-surface overflow-hidden">
              <div className="p-5 border-b border-border">
                <h2 className="font-display font-bold text-foreground text-lg">📊 Before vs After</h2>
              </div>
              <div className="p-5 space-y-0 divide-y divide-border">
                <MetricDeltaRow
                  label="Demographic Parity Difference"
                  desc="Gap in positive prediction rates across groups"
                  before={fixResult.original_metrics.dpd}
                  after={fixResult.fixed_metrics.dpd}
                  lowerIsBetter
                />
                <MetricDeltaRow
                  label="Equalized Odds Difference"
                  desc="Gap in true/false positive rates across groups"
                  before={fixResult.original_metrics.eod}
                  after={fixResult.fixed_metrics.eod}
                  lowerIsBetter
                />
                <MetricDeltaRow
                  label="Model Accuracy"
                  desc="Overall classification accuracy"
                  before={fixResult.original_metrics.accuracy}
                  after={fixResult.fixed_metrics.accuracy}
                  lowerIsBetter={false}
                />
              </div>
            </div>
          </StaggerItem>

          {/* Grouped Bar Chart */}
          <StaggerItem index={6}>
            <BeforeAfterChart
              before={fixResult.comparison.group_rates_before}
              after={fixResult.comparison.group_rates_after}
              sensitiveCol={sensitiveCol}
            />
          </StaggerItem>

          {/* Success Banner */}
          <StaggerItem index={7}>
            <div
              className="card-border rounded-lg bg-primary/5 p-5"
              style={{ borderLeftWidth: 3, borderLeftColor: "hsl(168 47% 52%)", boxShadow: "0 0 20px hsla(168,47%,52%,0.1)" }}
            >
              <div className="flex items-start gap-3">
                <span className="text-2xl">🎉</span>
                <div>
                  <h3 className="font-display font-bold text-foreground">Bias Mitigation Applied</h3>
                  <p className="text-foreground-secondary text-sm font-mono mt-1">
                    Strategy: <span className="text-primary">{fixResult.strategy}</span>
                  </p>
                  <p className="text-foreground-muted text-xs font-mono mt-1">
                    DPD reduced by{" "}
                    <span className="text-success">
                      {Math.abs(((fixResult.original_metrics.dpd - fixResult.fixed_metrics.dpd) / (fixResult.original_metrics.dpd || 1)) * 100).toFixed(1)}%
                    </span>
                    {" · "}EOD reduced by{" "}
                    <span className="text-success">
                      {Math.abs(((fixResult.original_metrics.eod - fixResult.fixed_metrics.eod) / (fixResult.original_metrics.eod || 1)) * 100).toFixed(1)}%
                    </span>
                  </p>
                </div>
              </div>
            </div>
          </StaggerItem>

          {/* Next CTA */}
          <StaggerItem index={8}>
            <button
              onClick={() => dispatch({ type: "SET_ACTIVE_STEP", payload: "compare" })}
              className="w-full py-3 rounded-lg border border-primary/40 text-primary font-display font-bold text-sm hover:bg-primary/10 transition-colors duration-200"
            >
              📊 Next: View Full Report →
            </button>
          </StaggerItem>
        </>
      )}
    </div>
  );
}
