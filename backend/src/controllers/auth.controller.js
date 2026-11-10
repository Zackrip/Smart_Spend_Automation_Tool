import User from '../models/user.model.js';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import nodemailer from 'nodemailer';
import dotenv from 'dotenv';

dotenv.config();

const register = async (req, res) => {
  try {
    const { firstName, lastName, MobileNo, email, passwordHash } = req.body;

    if (!firstName || !lastName || !MobileNo || !email || !passwordHash) {
      return res
        .status(400)
        .json({ message: "Please provide first name, last name, mobile number, email, and password" });
    }

    const existingUser = await User.findOne({ where: { MobileNo, email } });
    if (existingUser) {
      return res.status(400).json({ message: "User already exists" });
    }

    const hashedPassword = await bcrypt.hash(passwordHash, 10);
    const user = await User.create({ firstName, lastName, MobileNo, email, passwordHash: hashedPassword });

    const token = jwt.sign({ id: user.id }, process.env.JWT_SECRET, {
      expiresIn: "7d",
    });

    res.status(201).json({ token, user });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

const login = async (req, res) => {
  try {
    const { MobileNo, email, passwordHash } = req.body;

    const user = await User.findOne({ where: { MobileNo, email } });
    if (!user) {
      return res.status(400).json({ message: "Invalid credentials" });
    }

    const isMatch = await bcrypt.compare(passwordHash, user.passwordHash);
    if (!isMatch) {
      return res.status(400).json({ message: "Invalid credentials" });
    }

    const token = jwt.sign({ id: user.id }, process.env.JWT_SECRET, {
      expiresIn: "7d",
    });

    res.json({ token, user });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

export default { register, login };