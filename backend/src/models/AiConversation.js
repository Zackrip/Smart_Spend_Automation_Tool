
import { DataTypes } from 'sequelize';
import sequelize from '../config/database.js';

const AiConversation = sequelize.define('AiConversation', {
    id: {
        type: DataTypes.BIGINT,
        primaryKey: true,
        autoIncrement: true
    },

    userId: {
        type: DataTypes.BIGINT,
        allowNull: false
    },

    title: {
        type: DataTypes.STRING(200),
        allowNull: true
    }
}, {
    tableName: 'ai_conversations',
    underscored: true,
    timestamps: true
});

export default AiConversation;
