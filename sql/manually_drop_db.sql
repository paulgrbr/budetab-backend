SELECT pg_terminate_backend(pg_stat_activity.pid) 
FROM pg_stat_activity 
WHERE datname = 'bude_transactions';

DROP DATABASE bude_transactions;

DO $$ 
DECLARE r RECORD;
BEGIN
    FOR r IN (SELECT rolname FROM pg_roles WHERE rolname NOT LIKE 'pg_%' AND rolname <> 'postgres') 
    LOOP
        EXECUTE 'DROP ROLE IF EXISTS "' || r.rolname || '";';
    END LOOP;
END $$;

-----------

CREATE DATABASE bude_transactions;