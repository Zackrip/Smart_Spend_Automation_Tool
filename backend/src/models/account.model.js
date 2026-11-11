
import { DataTypes } from 'sequelize';
import sequelize from '../config/database.js';

const Account = sequelize.define('Account', {
    id: {
        type: DataTypes.BIGINT,
        primaryKey: true,
        autoIncrement: true
    },

    userId: {
        type: DataTypes.BIGINT,
        allowNull: false
    },

    accountName: {
        type: DataTypes.STRING(100),
        allowNull: false
    },

    accountType: {
        type: DataTypes.ENUM('bank', 'wallet', 'cash'),
        allowNull: false
    },

    institutionName: {
        type: DataTypes.STRING(150),
        allowNull: true
    },

    currency: {
        type: DataTypes.STRING(3),
        defaultValue: 'INR'
    },

    isActive: {
        type: DataTypes.BOOLEAN,
        defaultValue: true
    }
}, {
    tableName: 'accounts',
    underscored: true,
    timestamps: true
});

export default Account;
