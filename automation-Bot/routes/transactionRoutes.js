
import express from 'express';
import models from '../models/index.js';
const router = express.Router();
// GET /api/transactions
// Retrieve transactions from PostgreSQL
router.get('/', async (req, res) => {
    try {
        const transactions = await models.Transaction.findAll({
            order: [['transactionDate', 'DESC']],
            limit: 100
        });
        res.status(200).json({
            success: true,
            count: transactions.length,
            data: transactions
        });
    } catch (error) {
        console.error('Error fetching transactions:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to fetch transactions'
        });
    }
});

export default router;
