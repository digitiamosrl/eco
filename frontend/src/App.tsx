import { Breadcrumb, Screen, Sidebar } from "./ds";
import { go, useRoute } from "./lib/route";
import DashboardScreen from "./screens/DashboardScreen";
import NewTestScreen from "./screens/NewTestScreen";
import PanelScreen from "./screens/PanelScreen";
import TestPage from "./screens/TestPage";
import "./screens/screens.css";

const ITEMS = [
  { key: "dashboard", label: "Dashboard", href: "#/" },
  { key: "panel", label: "Panel", href: "#/panel" },
];

export default function App() {
  const route = useRoute();

  return (
    <div className="scr-app">
      <Screen
        className="eco-screen--side"
        nav={
          <Sidebar
            items={ITEMS}
            current={route.page === "panel" ? "panel" : "dashboard"}
          />
        }
      >
        {route.page === "panel" ? (
          <PanelScreen />
        ) : route.page === "new-test" ? (
          <>
            <Breadcrumb trail={[{ label: "Dashboard", href: "#/" }]} current="Nuovo test" />
            <NewTestScreen onStarted={(id) => go({ page: "test", id })} />
          </>
        ) : route.page === "test" ? (
          <TestPage key={route.id} id={route.id} />
        ) : (
          <DashboardScreen />
        )}
      </Screen>
    </div>
  );
}
