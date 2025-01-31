CREATE TYPE PRICE_RANKING AS ENUM (
    'member', 
    'regular',
    'external'
);

CREATE TYPE PRICE_CATEGORY AS ENUM (
    'normal', 
    'party',
    'big_event'
);

CREATE TABLE "user" (
    user_id UUID PRIMARY KEY,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    time_created TIMESTAMPTZ DEFAULT NOW(),
    is_temporary BOOLEAN NOT NULL,
    price_ranking PRICE_RANKING DEFAULT 'external',
    profile_picture_path TEXT
);

CREATE TABLE account (
    public_id UUID PRIMARY KEY,
    username VARCHAR(36) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    time_created TIMESTAMPTZ DEFAULT NOW(),
    linked_user_id UUID REFERENCES "user"(user_id),
    CONSTRAINT username_format CHECK (username ~ '^[a-zA-Z0-9_]+$')
);

CREATE TYPE PRODUCT_TYPE AS ENUM (
    'beverage'
);

CREATE TABLE product_category(
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE product(
    product_id SERIAL PRIMARY KEY,
    product_picture_path TEXT,
    category_id INT REFERENCES product_category(category_id)
                    ON DELETE SET NULL
                    ON UPDATE CASCADE,
    product_type PRODUCT_TYPE NOT NULL
);

CREATE TABLE beverage(
    product_id INT NOT NULL PRIMARY KEY
                            REFERENCES product(product_id)
                            ON DELETE CASCADE
                            ON UPDATE CASCADE,
    beverage_size NUMERIC(5, 2) NOT NULL CHECK (beverage_size >= 0)
);

CREATE TABLE pricing(
    product_id INT NOT NULL REFERENCES product(product_id)
                            ON DELETE CASCADE
                            ON UPDATE CASCADE,
    pricing_type PRICE_CATEGORY NOT NULL,
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    CONSTRAINT PK_PRICE PRIMARY KEY (product_id, pricing_type)
);

CREATE TABLE financial_operation(
    operation_id SERIAL PRIMARY KEY, 
    title VARCHAR(255) NOT NULL UNIQUE,
    icon TEXT
);

CREATE TYPE TRANSACTION_TYPE AS ENUM (
    'product', 
    'operation'
);

CREATE TABLE tab_transactions(
    transaction_id SERIAL NOT NULL,
    transaction_position INT NOT NULL,
    time_created TIMESTAMPTZ DEFAULT NOW(),
    transaction_type TRANSACTION_TYPE NOT NULL, -- either product or financial_operation is set
    product_id INT REFERENCES product(product_id)
                    ON UPDATE CASCADE,
    quantity INT NOT NULL CHECK (quantity >= 1),
    financial_operation_id INT REFERENCES financial_operation(operation_id)
                                ON UPDATE CASCADE,
    balance NUMERIC(10, 2) NOT NULL,
    user_affected UUID REFERENCES "user"(user_id)
                                ON DELETE SET NULL
                                ON UPDATE CASCADE,
    user_affected_plain_text_if_deleted VARCHAR(255),
    user_created UUID REFERENCES "user"(user_id)
                                ON DELETE SET NULL
                                ON UPDATE CASCADE,
    CONSTRAINT PK_TAB PRIMARY KEY (transaction_id, transaction_position),
    CONSTRAINT CH_transaction_product_operation 
        CHECK (
            (transaction_type = 'product' AND product_id IS NOT NULL AND financial_operation_id IS NULL) OR
            (transaction_type = 'operation' AND financial_operation_id IS NOT NULL AND product_id IS NULL)
        ) 
);

CREATE TABLE register_transactions(
    transaction_id SERIAL NOT NULL,
    transaction_position INT NOT NULL,
    time_created TIMESTAMPTZ DEFAULT NOW(),
    transaction_type TRANSACTION_TYPE NOT NULL, -- either product or financial_operation is set
    product_id INT REFERENCES product(product_id)
                    ON UPDATE CASCADE,
    quantity INT NOT NULL CHECK (quantity >= 1),
    financial_operation_id INT REFERENCES financial_operation(operation_id)
                                ON UPDATE CASCADE,
    balance NUMERIC(10, 2) NOT NULL,
    user_created UUID REFERENCES "user"(user_id)
                                ON DELETE SET NULL
                                ON UPDATE CASCADE,
    CONSTRAINT PK_REGISTER PRIMARY KEY (transaction_id, transaction_position),
    CONSTRAINT CH_transaction_product_operation 
        CHECK (
            (transaction_type = 'product' AND product_id IS NOT NULL AND financial_operation_id IS NULL) OR
            (transaction_type = 'operation' AND financial_operation_id IS NOT NULL AND product_id IS NULL)
        ) 
);

CREATE USER {db_public_user} WITH PASSWORD '{db_public_user_pw}';
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM public_user;
GRANT CONNECT ON DATABASE bude_transactions TO public_user;
GRANT USAGE ON SCHEMA public TO public_user;
-- User grants
GRANT INSERT ON TABLE account TO public_user;
GRANT SELECT ON TABLE account TO public_user;