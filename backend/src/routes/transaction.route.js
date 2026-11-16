import express from "express";
import verifyToken from "../middlewares/auth.middleware.js";
import {
    createTransactionSchema,
    updateTransactionSchema,
    listQuerySchema,
    validate,
    validateQuery,
} from "../validators/transactionValidation.validator.js";
import transactionController from "../controllers/transaction.controller.js";

const router = express.Router();

// Get all transactions with optional filters
router.get(
    "/",
    verifyToken,
    validateQuery(listQuerySchema),
    transactionController.getTransactions,
);

export default router;