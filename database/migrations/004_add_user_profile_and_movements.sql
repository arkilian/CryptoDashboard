-- Migration to add user profile, address, gender and capital movements tables
-- These tables support the user management functionality from 2000.py

-- Gender lookup table
CREATE TABLE IF NOT EXISTS t_gender (
    gender_id SERIAL PRIMARY KEY,
    gender_name TEXT UNIQUE NOT NULL
);

-- Insert common gender options
INSERT INTO t_gender (gender_name) VALUES 
    ('Masculino'),
    ('Feminino'),
    ('Outro'),
    ('Prefiro não dizer')
ON CONFLICT (gender_name) DO NOTHING;

-- Address table
CREATE TABLE IF NOT EXISTS t_address (
    address_id SERIAL PRIMARY KEY,
    street TEXT,
    city TEXT,
    postal_code TEXT,
    country TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User profile table (extends t_users)
CREATE TABLE IF NOT EXISTS t_user_profile (
    profile_id SERIAL PRIMARY KEY,
    user_id INT UNIQUE REFERENCES t_users(user_id) ON DELETE CASCADE,
    email TEXT,
    first_name TEXT,
    last_name TEXT,
    birth_date DATE,
    gender_id INT REFERENCES t_gender(gender_id),
    address_id INT REFERENCES t_address(address_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User capital movements (deposits, withdrawals, etc.)
CREATE TABLE IF NOT EXISTS t_user_capital_movements (
    movement_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES t_users(user_id) ON DELETE CASCADE,
    movement_date DATE NOT NULL DEFAULT CURRENT_DATE,
    credit NUMERIC(18,2) DEFAULT 0,
    debit NUMERIC(18,2) DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_profile_user_id ON t_user_profile(user_id);
CREATE INDEX IF NOT EXISTS idx_capital_movements_user_id ON t_user_capital_movements(user_id);
CREATE INDEX IF NOT EXISTS idx_capital_movements_date ON t_user_capital_movements(movement_date);
