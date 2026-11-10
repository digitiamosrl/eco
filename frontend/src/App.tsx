import { useState } from "react";
import { AppNav, Screen, type AppNavProps } from "./ds";
import PanelScreen from "./screens/PanelScreen";
import ReportScreen from "./screens/ReportScreen";
import TestScreen from "./screens/TestScreen";
import "./screens/screens.css";

type ScreenKey = NonNullable<AppNavProps["current"]>;

export default function App() {
  const [current, setCurrent] = useState<ScreenKey>("panel");
  const [reportId, setReportId] = useState<string>();

  const showReport = (testId: string) => {
    setReportId(testId);
    setCurrent("report");
  };

  return (
    <div className="scr-app">
      <Screen nav={<AppNav current={current} onNavigate={setCurrent} />}>
        {current === "panel" && <PanelScreen />}
        {current === "test" && <TestScreen onShowReport={showReport} />}
        {current === "report" && <ReportScreen testId={reportId} onGoTest={() => setCurrent("test")} />}
      </Screen>
    </div>
  );
}
