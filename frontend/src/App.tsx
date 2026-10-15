import { useState } from "react";
import PanelScreen from "./screens/PanelScreen";
import ReportScreen from "./screens/ReportScreen";
import TestScreen from "./screens/TestScreen";

const screens = {
  panel: { label: "Panel", component: PanelScreen },
  test: { label: "Test", component: TestScreen },
  report: { label: "Report", component: ReportScreen },
} as const;

type ScreenKey = keyof typeof screens;

export default function App() {
  const [current, setCurrent] = useState<ScreenKey>("panel");
  const Screen = screens[current].component;

  return (
    <>
      <nav>
        {(Object.keys(screens) as ScreenKey[]).map((key) => (
          <button key={key} onClick={() => setCurrent(key)} disabled={key === current}>
            {screens[key].label}
          </button>
        ))}
      </nav>
      <main>
        <Screen />
      </main>
    </>
  );
}
