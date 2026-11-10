
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
    console.log("PostgreSQL connected ✅");
  } catch (error) {
    console.error("PostgreSQL connection failed ❌", error.message);
  }
};

export { sequelize, connectDB };
