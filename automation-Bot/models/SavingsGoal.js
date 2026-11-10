
import { DataTypes } from 'sequelize';
import sequelize from '../config/database.js';

const SavingsGoal = sequelize.define('SavingsGoal', {
    id: {
        type: DataTypes.BIGINT,
        primaryKey: true,
        autoIncrement: true
    },

    userId: {
        type: DataTypes.BIGINT,
        allowNull: false
    },

    name: {
        type: DataTypes.STRING(150),
        allowNull: false
    },

    targetAmount: {
        type: DataTypes.DECIMAL(14, 2),
        allowNull: false,
        validate: {
            min: 0.01
        }
    },

    currentAmount: {
        type: DataTypes.DECIMAL(14, 2),
        allowNull: false,
        defaultValue: 0,
        validate: {
            min: 0
        }
    },

    targetDate: {
        type: DataTypes.DATEONLY,
        allowNull: true
    },

    status: {
        type: DataTypes.ENUM('active', 'completed', 'paused'),
        allowNull: false,
        defaultValue: 'active'
    }
}, {
    tableName: 'savings_goals',
    underscored: true,
    timestamps: true
});

export default SavingsGoal;
