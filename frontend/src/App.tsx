import { QueryClientProvider } from "@tanstack/react-query"
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"

import { AppLayout } from "@/components/AppLayout"
import { AuthProvider } from "@/features/auth/AuthProvider"
import { DashboardPage } from "@/features/dashboard/DashboardPage"
import { LoginPage } from "@/features/auth/LoginPage"
import { RegisterPage } from "@/features/auth/RegisterPage"
import { ProjectDetailsPage } from "@/features/projects/ProjectDetailsPage"
import { ProjectListPage } from "@/features/projects/ProjectListPage"
import { TaskDetailsPage } from "@/features/tasks/TaskDetailsPage"
import { queryClient } from "@/lib/queryClient"
import { GuestRoute, ProtectedRoute } from "@/routes/ProtectedRoute"

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
                <Route index element={<DashboardPage />} />
                <Route path="projects" element={<ProjectListPage />} />
                <Route path="projects/:projectId" element={<ProjectDetailsPage />} />
                <Route
                  path="projects/:projectId/tasks/:taskId"
                  element={<TaskDetailsPage />}
                />
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
