import { useEffect, useState } from "react";

export type Route = { page: "dashboard" } | { page: "panel" } | { page: "new-test" } | { page: "test"; id: string };

export function parseRoute(hash: string): Route {
  const path = hash.replace(/^#/, "");
  if (path === "/panel") return { page: "panel" };
  if (path === "/test/nuovo") return { page: "new-test" };
  const test = /^\/test\/([\w-]+)$/.exec(path);
  return test ? { page: "test", id: test[1] } : { page: "dashboard" };
}

export function routeHref(route: Route): string {
  switch (route.page) {
    case "panel":
      return "#/panel";
    case "new-test":
      return "#/test/nuovo";
    case "test":
      return `#/test/${route.id}`;
    default:
      return "#/";
  }
}

export const go = (route: Route) => {
  window.location.hash = routeHref(route);
};

/** The current page; follows the back button and links. */
export function useRoute(): Route {
  const [route, setRoute] = useState(() => parseRoute(window.location.hash));
  useEffect(() => {
    const onChange = () => {
      setRoute(parseRoute(window.location.hash));
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return route;
}
