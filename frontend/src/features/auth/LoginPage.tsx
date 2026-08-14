import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { Link, useLocation } from "react-router-dom"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { getApiErrorMessage } from "@/lib/apiError"

import { AuthLayout } from "./AuthLayout"
import { useLogin } from "./hooks"
import { loginSchema, type LoginFormValues } from "./schemas"

export function LoginPage() {
  const location = useLocation()
  const registered = Boolean(
    (location.state as { registered?: boolean } | null)?.registered,
  )
  const login = useLogin()
  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  })

  return (
    <AuthLayout
      title="Sign in"
      description="Use your work email to continue."
    >
      {registered ? (
        <p className="mb-4 rounded-md bg-muted px-3 py-2 text-sm">
          Account created. Sign in to continue.
        </p>
      ) : null}

      <form
        className="space-y-4"
        onSubmit={form.handleSubmit((values) => login.mutate(values))}
        noValidate
      >
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            {...form.register("email")}
          />
          {form.formState.errors.email ? (
            <p className="text-sm text-destructive">
              {form.formState.errors.email.message}
            </p>
          ) : null}
        </div>

        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            {...form.register("password")}
          />
          {form.formState.errors.password ? (
            <p className="text-sm text-destructive">
              {form.formState.errors.password.message}
            </p>
          ) : null}
        </div>

        {login.isError ? (
          <p className="text-sm text-destructive">
            {getApiErrorMessage(login.error, "Could not sign in")}
          </p>
        ) : null}

        <Button type="submit" className="w-full" disabled={login.isPending}>
          {login.isPending ? "Signing in…" : "Sign in"}
        </Button>
      </form>

      <p className="mt-4 text-center text-sm text-muted-foreground">
        Need an account?{" "}
        <Link to="/register" className="font-medium text-foreground underline">
          Register
        </Link>
      </p>
    </AuthLayout>
  )
}
