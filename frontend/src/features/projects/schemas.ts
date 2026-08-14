import { z } from "zod"

export const projectFormSchema = z.object({
  name: z.string().min(1, "Name is required").max(255, "Name is too long"),
  description: z
    .string()
    .max(4000, "Description is too long")
    .optional()
    .or(z.literal("")),
})

export const addMemberSchema = z.object({
  email: z.string().email("Enter a valid email address"),
})

export type ProjectFormValues = z.infer<typeof projectFormSchema>
export type AddMemberFormValues = z.infer<typeof addMemberSchema>
