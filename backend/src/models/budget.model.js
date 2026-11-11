
import { DataTypes } from 'sequelize';
import sequelize from '../config/database.js';

const Budget = sequelize.define('budget', {
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

    amountLimit: {
        type: DataTypes.DECIMAL(14, 2),
        allowNull: false,
        validate: {
            min: 0
        }
    },

    period: {
        type: DataTypes.ENUM('weekly', 'monthly', 'custom'),
        allowNull: false,
        defaultValue: 'monthly'
    },

    startDate: {
        type: DataTypes.DATEONLY,
        allowNull: false
    },

    endDate: {
        type: DataTypes.DATEONLY,
        allowNull: true
    }
}, {
    tableName: 'budgets',
    underscored: true,
    timestamps: true
});

export default Budget;
