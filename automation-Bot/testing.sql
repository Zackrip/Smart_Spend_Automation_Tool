
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
      'users',
      'accounts',
      'categories',
      'transactions',
      'budgets',
      'savings_goals',
      'recurring_payments',
      'financial_insights',
      'ai_conversations',
      'ai_messages'
  )
ORDER BY table_name;

SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'transactions'
ORDER BY ordinal_position;


select * from users;
select * from categories;
select * from accounts;
select * from transactions;
SELECT
    id,
    user_id,
    category_id,
    amount,
    transaction_type
FROM transactions
WHERE user_id = 4
  AND transaction_type = 'expense'
  AND amount > 0
ORDER BY category_id, id;