import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";
import { AppProviders } from "@/app/providers/AppProviders";
import { env } from "@/lib/env";

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("Root element '#root' not found.");
}

const renderApp = () => {
  const pendingRedirect = sessionStorage.getItem("spa-redirect");
  if (pendingRedirect) {
    sessionStorage.removeItem("spa-redirect");
    window.history.replaceState(null, "", pendingRedirect);
  }

  createRoot(rootElement).render(
    <AppProviders>
      <App />
    </AppProviders>,
  );
};

const bootstrap = async () => {
  if (env.useMocks) {
    const { startMockWorker } = await import("@/mocks/browser");
    await startMockWorker();
  }
  renderApp();
};

bootstrap();
