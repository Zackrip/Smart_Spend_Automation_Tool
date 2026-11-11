
import { DataTypes } from 'sequelize';
import sequelize from '../config/database.js';

const Transaction = sequelize.define('Transaction', {
    id: {
        type: DataTypes.BIGINT,
        primaryKey: true,
        autoIncrement: true
    },

    userId: {
        type: DataTypes.BIGINT,
        allowNull: false
    },

    accountId: {
        type: DataTypes.BIGINT,
        allowNull: false
    },

    categoryId: {
        type: DataTypes.BIGINT,
        allowNull: true
    },

    amount: {
        type: DataTypes.DECIMAL(14, 2),
        allowNull: false,
        validate: {
            min: 0
        }
    },

    transactionType: {
        type: DataTypes.ENUM('income', 'expense', 'transfer'),
        allowNull: false
    },
    
    paymentMethod: {
        type: DataTypes.ENUM('cash', 'card', 'upi', 'wallet', 'other'),
        allowNull: false
    },

    merchant: {
        type: DataTypes.STRING(200),
        allowNull: true
    },

    description: {
        type: DataTypes.TEXT,
        allowNull: true
    },

    transactionDate: {
        type: DataTypes.DATE,
        allowNull: false
    },

    source: {
        type: DataTypes.ENUM('manual', 'csv', 'provider'),
        defaultValue: 'manual'
    }
}, {
    tableName: 'transactions',
    underscored: true,
    timestamps: true
});

export default Transaction;
