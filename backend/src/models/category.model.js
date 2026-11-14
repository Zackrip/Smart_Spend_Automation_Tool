
import { DataTypes } from 'sequelize';
import {sequelize} from '../configs/database.config.js';

const Category = sequelize.define('Category', {
    id: {
        type: DataTypes.BIGINT,
        primaryKey: true,
        autoIncrement: true
    },

    userId: {
        type: DataTypes.BIGINT,
        allowNull: true
    },

    name: {
        type: DataTypes.STRING(100),
        allowNull: false
    },

    type: {
        type: DataTypes.ENUM('income', 'expense'),
        allowNull: false
    },

    icon: {
        type: DataTypes.STRING(50),
        allowNull: true
    },

    isSystem: {
        type: DataTypes.BOOLEAN,
        allowNull: false,
        defaultValue: false
    }
}, {
    tableName: 'categories',
    underscored: true,
    timestamps: true
});

export default Category;
