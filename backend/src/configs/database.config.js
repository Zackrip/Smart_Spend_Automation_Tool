
import dotenv from 'dotenv';
import { Sequelize } from 'sequelize';
dotenv.config();
const sequelize = new Sequelize({    
    database:process.env.DB_NAME, // Database name
    username:process.env.DB_USER, // PostgreSQL username
    password:process.env.DB_PASSWORD,  // Your actual PostgreSQL password
    host:process.env.DB_HOST,
    port:Number(process.env.DB_PORT) || 5432,
    dialect: 'postgres'
    }
);


const connectDB = async () => {
    try {
        await sequelize.authenticate();

        console.log("PostgreSQL connected!");

        const [dbInfo] = await sequelize.query(`
            SELECT
                current_database() AS database,
                current_schema() AS schema,
                current_user AS username
        `);

        console.log("DATABASE INFO:", dbInfo);

        const [columns] = await sequelize.query(`
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        `);

        console.log("USERS TABLE COLUMNS:", columns);

    } catch (error) {
        console.error("Database connection failed:", error);
        throw error;
    }
};


export { sequelize, connectDB };
