import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { Link } from "react-router-dom"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { getApiErrorMessage } from "@/lib/apiError"

import { AuthLayout } from "./AuthLayout"
import { useRegister } from "./hooks"
import { registerSchema, type RegisterFormValues } from "./schemas"

export function RegisterPage() {
  const registerUser = useRegister()
  const form = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { full_name: "", email: "", password: "" },
  })

  return (
    <AuthLayout
      title="Create an account"
      description="You’ll use this email to sign in."
    >
      <form
        className="space-y-4"
        onSubmit={form.handleSubmit((values) => registerUser.mutate(values))}
        noValidate
      >
        <div className="space-y-2">
          <Label htmlFor="full_name">Full name</Label>
          <Input
            id="full_name"
            autoComplete="name"
            {...form.register("full_name")}
          />
          {form.formState.errors.full_name ? (
            <p className="text-sm text-destructive">
              {form.formState.errors.full_name.message}
            </p>
          ) : null}
        </div>

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
            autoComplete="new-password"
            {...form.register("password")}
          />
          {form.formState.errors.password ? (
            <p className="text-sm text-destructive">
              {form.formState.errors.password.message}
            </p>
          ) : null}
        </div>

        {registerUser.isError ? (
          <p className="text-sm text-destructive">
            {getApiErrorMessage(registerUser.error, "Could not register")}
          </p>
        ) : null}

        <Button
          type="submit"
          className="w-full"
          disabled={registerUser.isPending}
        >
          {registerUser.isPending ? "Creating account…" : "Create account"}
        </Button>
      </form>

      <p className="mt-4 text-center text-sm text-muted-foreground">
        Already registered?{" "}
        <Link to="/login" className="font-medium text-foreground underline">
          Sign in
        </Link>
      </p>
    </AuthLayout>
  )
}
