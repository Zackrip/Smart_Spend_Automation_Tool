
import { DataTypes } from 'sequelize';
import sequelize from '../config/database.js';

const RecurringPayment = sequelize.define('RecurringPayment', {
    id: {
        type: DataTypes.BIGINT,
        primaryKey: true,
        autoIncrement: true
    },

    userId: {
        type: DataTypes.BIGINT,
        allowNull: false
    },

    categoryId: {
        type: DataTypes.BIGINT,
        allowNull: true
    },

    name: {
        type: DataTypes.STRING(150),
        allowNull: false
    },

    expectedAmount: {
        type: DataTypes.DECIMAL(14, 2),
        allowNull: false,
        validate: {
            min: 0
        }
    },

    frequency: {
        type: DataTypes.ENUM(
            'weekly',
            'monthly',
            'quarterly',
            'yearly'
        ),
        allowNull: false,
        defaultValue: 'monthly'
    },

    nextDueDate: {
        type: DataTypes.DATEONLY,
        allowNull: true
    },

    status: {
        type: DataTypes.ENUM('active', 'paused', 'cancelled'),
        allowNull: false,
        defaultValue: 'active'
    }
}, {
    tableName: 'recurring_payments',
    underscored: true,
    timestamps: true
});

export default RecurringPayment;
