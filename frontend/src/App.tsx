import { QueryClientProvider } from "@tanstack/react-query"
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"

import { AppLayout } from "@/components/AppLayout"
import { AuthProvider } from "@/features/auth/AuthProvider"
import { LoginPage } from "@/features/auth/LoginPage"
import { RegisterPage } from "@/features/auth/RegisterPage"
import { queryClient } from "@/lib/queryClient"
import { GuestRoute, ProtectedRoute } from "@/routes/ProtectedRoute"

function SignedInHome() {
  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">Welcome</h1>
      <p className="mt-1 text-muted-foreground">
        You are signed in. Project and task screens land in the next commits.
      </p>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route element={<GuestRoute />}>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
            </Route>
            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route index element={<SignedInHome />} />
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
