import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import App from "./App.tsx";
import { Login } from "./components/Login.tsx";
import { ProfilePage } from "./components/ProfilePage.tsx";
import { EmailComposer } from "./components/EmailComposer.tsx";
import "./styles/global.css";

function _decodeJwtPayload(token: string): any {
  try {
    return JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
  } catch {
    return null;
  }
}

function isTokenValid(): boolean {
  const token = localStorage.getItem("hres_token");
  if (!token) return false;
  const payload = _decodeJwtPayload(token);
  if (!payload || !payload.exp) return false;
  // Valid if expires more than 60 seconds from now
  return Date.now() / 1000 < payload.exp - 60;
}

// Protected route: clears expired tokens and redirects to /login
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  if (!isTokenValid()) {
    localStorage.removeItem("hres_token");
    localStorage.removeItem("hres_user");
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <App />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <ProfilePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/email"
          element={
            <ProtectedRoute>
              <EmailComposer />
            </ProtectedRoute>
          }
        />
        {/* Catch-all: redirect everything unknown to dashboard (which itself may redirect to login) */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
