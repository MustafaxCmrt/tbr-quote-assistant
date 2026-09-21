#!/bin/sh
set -eu
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set ON_ERROR_STOP=1 --set runtime_password="$APP_DB_PASSWORD" <<'SQL'
SELECT format('CREATE ROLE tbr_runtime LOGIN PASSWORD %L', :'runtime_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'tbr_runtime') \gexec
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
SQL
