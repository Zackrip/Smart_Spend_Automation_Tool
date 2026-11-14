import { Op, fn, col } from "sequelize";
import Transaction from "../models/transaction.model.js";
import Category from "../models/category.model.js";
import { buildFilter } from "../utils/transaction.helper.js";

// GET /api/v1/transactions gell all transactions for a user, with optional filters.

const getTransactions = async (req, res) => {
    
}