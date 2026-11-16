
import { z } from "zod";
import { TRANSACTION_CONSTANTS } from "../constants/transaction.constant.js";

// PostgreSQL BIGINT IDs
const databaseId = z.coerce.number().int().positive();

const amount = z
  .number()
  .positive("Amount must be greater than 0")
  .max(1_000_000_000, "Amount is too large")
  .refine(
    (value) => Math.abs(value * 100 - Math.round(value * 100)) < 1e-6,
    "Amount can have at most 2 decimal places"
  );

const date = z.coerce
  .date()
  .refine(
    (value) => value.getTime() <= Date.now() + 24 * 60 * 60 * 1000,
    "Date cannot be in the future"
  );

const base = z.object({
  amount,
  transactionType: z.enum(TRANSACTION_CONSTANTS.TRANSACTION_TYPES),
  categoryId: databaseId.nullable().optional(),
  merchant: z.string().trim().max(200).optional(),
  transactionDate: date,
  paymentMethod: z.enum(TRANSACTION_CONSTANTS.PAYMENT_MODES).optional(),
  notes: z.string().trim().max(500).optional(),
  isRecurring: z.boolean().optional(),
});

// POST: Create transaction
const createTransactionSchema = base;

// PATCH: Update transaction
const updateTransactionSchema = base
  .partial()
  .refine(
    (data) => Object.keys(data).length > 0,
    { message: "Provide at least one field to update" }
  );

// GET: List transactions
const listQuerySchema = z
  .object({
    page: z.coerce.number().int().min(1).default(1),
    limit: z.coerce.number().int().min(1).max(100).default(20),

    transactionType: z
      .enum(TRANSACTION_CONSTANTS.TRANSACTION_TYPES)
      .optional(),

    categoryId: databaseId.optional(),

    paymentMethod: z
      .enum(TRANSACTION_CONSTANTS.PAYMENT_MODES)
      .optional(),

    from: z.coerce.date().optional(),
    to: z.coerce.date().optional(),

    minAmount: z.coerce.number().min(0).optional(),
    maxAmount: z.coerce.number().min(0).optional(),

    search: z.string().trim().max(50).optional(),

    sortBy: z
      .enum(["transactionDate", "amount", "merchant", "createdAt"])
      .default("transactionDate"),

    order: z.enum(["asc", "desc"]).default("desc"),
  })
  .refine(
    (query) => !query.from || !query.to || query.from <= query.to,
    {
      message: '"from" must be before "to"',
      path: ["from"],
    }
  )
  .refine(
    (query) =>
      query.minAmount === undefined ||
      query.maxAmount === undefined ||
      query.minAmount <= query.maxAmount,
    {
      message: '"minAmount" must be less than "maxAmount"',
      path: ["minAmount"],
    }
  );

// Format Zod errors
const formatErrors = (error) =>
  error.issues.map((issue) => ({
    field: issue.path.join("."),
    message: issue.message,
  }));

// Validate request body
const validate = (schema) => (req, res, next) => {
  const result = schema.safeParse(req.body);

  if (!result.success) {
    return res.status(400).json({
      success: false,
      message: "Validation failed",
      errors: formatErrors(result.error),
    });
  }

  req.body = result.data;
  next();
};

// Validate GET query parameters
const validateQuery = (schema) => (req, res, next) => {
  const cleaned = Object.fromEntries(
    Object.entries(req.query).filter(([, value]) => value !== "")
  );

  const result = schema.safeParse(cleaned);

  if (!result.success) {
    return res.status(400).json({
      success: false,
      message: "Invalid query",
      errors: formatErrors(result.error),
    });
  }

  req.validatedQuery = result.data;
  next();
};

export {
  createTransactionSchema,
  updateTransactionSchema,
  listQuerySchema,
  validate,
  validateQuery,
};
