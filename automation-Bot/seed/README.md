# SmartSpend AI demo seed package

This package matches the model definitions in the uploaded `account.zip`. It uses your existing Sequelize models and PostgreSQL tables; it does not create or drop tables.

## Files
- `seed-data.json`: fictional demo users and scenarios.
- `seed-demo.js`: inserts the data through Sequelize in parent-first order.
- `verify-seed.js`: prints total row counts and checks for a sample June grocery transaction.

## Install / place files
1. Copy the `seed` folder into the project root:
   `smart spend ai/seed/`
2. Confirm `package.json` has `"type": "module"` (the project already uses `import` syntax).
3. Confirm your existing `.env` and `config/database.js` connect to the intended local database.
4. Stop and restart the Node server if needed; run the seed script from the project root.

## Run
```powershell
node seed/seed-demo.js
node seed/verify-seed.js
```

The scripts import `../models/index.js`, so they use the same Sequelize connection and associations as the app. The seed script uses a database transaction and `findOrCreate` keys to avoid repeatedly inserting the same demo records on normal reruns.

## Data details
- 4 fictional users with `.test` email addresses.
- Accounts and shared system categories.
- Synthetic transactions from January through June 2026.
- Monthly salary and optional freelance income.
- Expenses across groceries, dining, transport, bills, shopping, entertainment, health, education and rent.
- One intentional June grocery spike for Aarav (₹6,200) to test anomaly detection.
- Budgets, savings goals, recurring payments, clearly labelled sample insights, and one sample AI conversation.

## Important notes
- All data is fictional. The insights are illustrative placeholders, not predictions.
- `passwordHash` is a placeholder string. These demo users cannot log in; do not use the data in production.
- The seed does not delete data and does not use `sync({ force: true })`.
- If you already have a real user with one of the demo email addresses, that user will be reused; their existing fields will not be overwritten.
- If an existing record has a matching natural key but different data, `findOrCreate` will reuse it and will not update it.
- `findOrCreate` helps prevent duplicate demo records, but for production-grade idempotency you should also enforce appropriate unique constraints at the database level.
- Current sample budgets use June 2026 as their period; adjust `startDate` and `endDate` if you want a different analysis month.
- The script does not update account balances because the uploaded Account model has no balance field.
- Confirm the `Budget` import casing in `models/index.js` matches the actual filename exactly. Your screenshot showed `Budget.js`; the uploaded ZIP contains `budget.js`. Pick one filename casing and use it consistently in both the file and import.
