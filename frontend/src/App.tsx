import { useState } from "react";
import PanelScreen from "./screens/PanelScreen";
import ReportScreen from "./screens/ReportScreen";
import TestScreen from "./screens/TestScreen";

const SCREENS = { panel: "Panel", test: "Test", report: "Report" } as const;
type ScreenKey = keyof typeof SCREENS;

export default function App() {
  const [current, setCurrent] = useState<ScreenKey>("panel");
  const [reportId, setReportId] = useState<string>();

  const showReport = (testId: string) => {
    setReportId(testId);
    setCurrent("report");
  };

  return (
    <>
      <nav className="app-nav">
        <strong>eco</strong>
        {(Object.keys(SCREENS) as ScreenKey[]).map((key) => (
          <button
            key={key}
            type="button"
            aria-current={key === current ? "page" : undefined}
            onClick={() => setCurrent(key)}
          >
            {SCREENS[key]}
          </button>
        ))}
      </nav>
      <main>
        {current === "panel" && <PanelScreen />}
        {current === "test" && <TestScreen onShowReport={showReport} />}
        {current === "report" && <ReportScreen testId={reportId} />}
      </main>
    </>
  );
}
