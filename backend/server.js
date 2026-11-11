import app from './src/app.js';
import dotenv from 'dotenv';
import { connectDB } from "./src/configs/database.config.js"
import { sequelize } from "./src/configs/database.config.js";

dotenv.config({ quiet: true });

const PORT = process.env.PORT || 3000;

connectDB();
await sequelize.sync();

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
}); 

