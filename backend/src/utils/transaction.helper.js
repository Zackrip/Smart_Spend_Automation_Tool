import { Op } from "sequelize";
import Transaction from "../models/transaction.model.js";
import Category from "../models/category.model.js";

const transactions = await Transaction.findAll({
    include: [
        {
            model: Category,
            attributes: ["id", "name", "icon", "type"],
        },
    ],
});

const checkCategory = async (userId, categoryId, type) => {
    if (!categoryId) return null;

    const category = await Category.findOne({
        where: {
            id: categoryId,
            [Op.or]: [
                { userId: null },
                { userId: userId },
            ],
        },
    });

    if (!category) return "Category not found";

    if (category.type !== type) {
        return `This category is for ${category.type} transactions`;
    }

    return null;
};

// Build database filters from API query parameters.
const buildFilter = (userId, q) => {
    const filter = {
        userId: userId,
    };

    // Filter by income or expense.
    if (q.type) {
        filter.transactionType = q.type;
    }

    // Filter by category.
    if (q.categoryId) {
        filter.categoryId = q.categoryId;
    }

    // Filter by payment method.
    if (q.paymentMode) {
        filter.paymentMethod = q.paymentMode;
    }

    // Filter by transaction date range.
    if (q.from || q.to) {
        filter.transactionDate = {};

        if (q.from) {
            filter.transactionDate[Op.gte] = q.from;
        }

        if (q.to) {
            const isDateOnly =
                q.to.getUTCHours() === 0 &&
                q.to.getUTCMinutes() === 0 &&
                q.to.getUTCSeconds() === 0 &&
                q.to.getUTCMilliseconds() === 0;

            filter.transactionDate[Op.lte] = isDateOnly
                ? new Date(q.to.getTime() + 24 * 60 * 60 * 1000 - 1)
                : q.to;
        }
    }

    // Filter by minimum and maximum amount.
    if (q.minAmount !== undefined || q.maxAmount !== undefined) {
        filter.amount = {};

        if (q.minAmount !== undefined) {
            filter.amount[Op.gte] = q.minAmount;
        }

        if (q.maxAmount !== undefined) {
            filter.amount[Op.lte] = q.maxAmount;
        }
    }

    // Search merchant and notes.
    if (q.search) {
        filter[Op.or] = [
            { merchant: { [Op.iLike]: `%${q.search}%` } },
            { notes: { [Op.iLike]: `%${q.search}%` } },
        ];
    }

    return filter;
};

export default {transactions, checkCategory, buildFilter };