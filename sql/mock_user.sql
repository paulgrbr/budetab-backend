INSERT INTO "user"(user_id, first_name, last_name, is_temporary, price_ranking, permissions)
VALUES

-- No admin access_token
('95cebd35-2489-4dbf-b379-a1f901875831', 'Test', 'User', 'FALSE', 'regular', 'user'),
-- Admin access_token
('1b6b231b-66f0-468a-b900-dfc9a48977b9', 'Test', 'Admin', 'FALSE', 'member', 'admin'),
-- No admin access_token for link test
('0becd0ae-fd81-4f54-9685-160eed903b31', 'Test', 'User', 'FALSE', 'regular', 'user');

UPDATE account
SET linked_user_id = '95cebd35-2489-4dbf-b379-a1f901875831'
WHERE username = 'test_user';

UPDATE account
SET linked_user_id = '1b6b231b-66f0-468a-b900-dfc9a48977b9'
WHERE username = 'test_admin';

