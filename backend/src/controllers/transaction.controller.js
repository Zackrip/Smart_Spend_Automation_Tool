import { Op, fn, col } from "sequelize";
import Transaction from "../models/transaction.model.js";
import Category from "../models/category.model.js";
import transactionHelper from "../utils/transaction.helper.js";

// GET /api/v1/transactions gell all transactions for a user, with optional filters.

const getTransactions = async (req, res) => {
  try {
    // 1. Get validated query parameters
    const q = req.validatedQuery;

    // 2. Build Sequelize WHERE conditions
    const filter = transactionHelper.buildFilter(req.user.id, q);

    // 3. Allow only approved columns for sorting
    const sortColumns = {
      transactionDate: "transactionDate",
      amount: "amount",
      merchant: "merchant",
      createdAt: "createdAt",
    };

    const sortColumn = sortColumns[q.sortBy] || "transactionDate";
    const sortDirection = q.order === "asc" ? "ASC" : "DESC";

    // 4. Run all three database queries concurrently
    const [items, total, totals] = await Promise.all([
      // Fetch the current page of transactions
      Transaction.findAll({
        where: filter,
        order: [
          [sortColumn, sortDirection],
          ["id", "DESC"],
        ],
        offset: (q.page - 1) * q.limit,
        limit: q.limit,
        include: [
          {
            model: Category,
            as: "category",
            attributes: ["id", "name", "icon", "type"],
            required: false,
          },
        ],
      }),

      // Count every transaction matching the filters
      Transaction.count({
        where: filter,
      }),

      // Calculate income and expense totals for all matching transactions
      Transaction.findAll({
        attributes: ["transactionType", [fn("SUM", col("amount")), "total"]],
        where: filter,
        group: ["transactionType"],
        raw: true,
      }),
    ]);

    // 5. Convert grouped totals into numbers
    const sumOf = (type) =>
      Number(totals.find((item) => item.transactionType === type)?.total || 0);

    const totalIncome = sumOf("income");
    const totalExpense = sumOf("expense");

    // 6. Send the response
    return res.status(200).json({
      success: true,
      data: items,
      pagination: {
        page: q.page,
        limit: q.limit,
        total,
        totalPages: Math.ceil(total / q.limit),
      },
      summary: {
        totalIncome,
        totalExpense,
        net: totalIncome - totalExpense,
      },
    });
  } catch (err) {
    console.error("Get transactions error:", err);

    return res.status(500).json({
      success: false,
      message: "Could not fetch transactions",
    });
  }
};

export default {
  getTransactions,
};