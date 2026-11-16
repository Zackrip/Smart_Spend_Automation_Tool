import { z } from "zod";

// Common validation rules
const base = z.object({
  name: z.string().trim().min(2).max(30),
  type: z.enum(["expense", "income"]),
  icon: z.string().trim().max(30).optional(),
  color: z
    .string()
    .regex(/^#[0-9a-fA-F]{6}$/, "Color must be a hex like #22c55e")
    .optional(),
});

// Create category: name and type are required
const createCategorySchema = base;

// Update category: all fields are optional,
// but at least one field must be provided
const updateCategorySchema = base
  .partial()
  .refine((data) => Object.keys(data).length > 0, {
    message: "Provide at least one field to update",
  });

// Reusable validation middleware

const validate = (schema) => (req, res, next) => {
  const result = schema.safeParse(req.body);

  if (!result.success) {
    return res.status(400).json({
      success: false,
      message: "Validation failed",
      errors: result.error.issues.map((issue) => ({
        field: issue.path.join("."),
        message: issue.message,
      })),
    });
  }

  // Only validated data reaches the controller
  req.body = result.data;

  next();
};

export {
  createCategorySchema,
  updateCategorySchema,
  validate,
};