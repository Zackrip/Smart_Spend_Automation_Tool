
import { DataTypes } from 'sequelize';
import sequelize from '../config/database.js';

const FinancialInsight = sequelize.define('FinancialInsight', {
    id: {
        type: DataTypes.BIGINT,
        primaryKey: true,
        autoIncrement: true
    },

    userId: {
        type: DataTypes.BIGINT,
        allowNull: false
    },

    insightType: {
        type: DataTypes.ENUM(
            'forecast',
            'anomaly',
            'overspending',
            'saving_opportunity'
        ),
        allowNull: false
    },

    title: {
        type: DataTypes.STRING(200),
        allowNull: false
    },

    description: {
        type: DataTypes.TEXT,
        allowNull: false
    },

    severity: {
        type: DataTypes.ENUM('info', 'warning', 'high'),
        allowNull: false,
        defaultValue: 'info'
    },

    metadata: {
        type: DataTypes.JSONB,
        allowNull: true
    },

    generatedAt: {
        type: DataTypes.DATE,
        allowNull: false,
        defaultValue: DataTypes.NOW
    },

    isRead: {
        type: DataTypes.BOOLEAN,
        allowNull: false,
        defaultValue: false
    }
}, {
    tableName: 'financial_insights',
    underscored: true,
    timestamps: true
});

export default FinancialInsight;
