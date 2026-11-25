import { useState } from "react";
import { Breadcrumb, Screen, Sidebar } from "./ds";
import { go, useRoute } from "./lib/route";
import { getUserName, setUserName } from "./lib/userName";
import DashboardScreen from "./screens/DashboardScreen";
import NameScreen from "./screens/NameScreen";
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
  const [name, setName] = useState(getUserName);
  const [editingName, setEditingName] = useState(false);
  const saveName = (n: string) => {
    setUserName(n);
    setName(n);
    setEditingName(false);
  };

  return (
    <div className="scr-app">
      <Screen
        className="eco-screen--side"
        nav={
          <Sidebar
            items={ITEMS}
            current={route.page === "panel" ? "panel" : "dashboard"}
            user={name || undefined}
            onChangeUser={() => setEditingName(true)}
          />
        }
      >
        {!name || editingName ? (
          <NameScreen initial={name} onDone={saveName} />
        ) : route.page === "panel" ? (
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
