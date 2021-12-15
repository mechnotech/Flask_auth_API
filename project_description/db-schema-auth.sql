CREATE SCHEMA IF NOT EXISTS auth;
SET search_path TO auth,public;

CREATE TABLE IF NOT EXISTS auth.users (
    id uuid PRIMARY KEY,
    username text NOT NULL,
    password text NOT NULL,
    email text NOT NULL,
    created_at timestamptz,
    updated_at timestamptz
);

CREATE TABLE IF NOT EXISTS auth.profiles (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL,
    first_name text,
    last_name text,
    role text,
    bio text,
    created_at timestamptz,
    updated_at timestamptz
);

CREATE TABLE IF NOT EXISTS auth.jwt (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL,
    refresh_token text NOT NULL,
    expire timestamptz NOT NULL,
    created_at timestamptz,
    updated_at timestamptz
);


CREATE TABLE IF NOT EXISTS auth.logins (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL,
    info text NOT NULL,
    status text,
    created_at timestamptz
);
