import { createBrowserRouter, Outlet } from "react-router-dom";
import Index from "@/pages/Index";
import Register from "@/pages/auth/Register";
import Login from "@/pages/auth/Login";
import VerifyEmail from "@/pages/auth/VerifyEmail";
import Dashboard from "@/pages/app/Dashboard";

export const appRouter = createBrowserRouter([
  {
    path: "/",
    element: <Index />,
  },
  {
    path: "/auth",
    element: <Outlet />,
    children: [
      { path: "register", element: <Register /> },
      { path: "login", element: <Login /> },
      { path: "verify-email", element: <VerifyEmail /> },
    ],
  },
  {
    path: "/app",
    element: <Outlet />,
    children: [{ path: "dashboard", element: <Dashboard /> }],
  },
]);
