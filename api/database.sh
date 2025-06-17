#!/bin/bash

# Start Postgres container (if not already running)
docker run --name my-postgres -e POSTGRES_PASSWORD=password -e POSTGRES_USER=postgres -e POSTGRES_DB=apps -p 5432:5432 -d postgres

# Wait until Postgres is ready
until docker exec my-postgres pg_isready -U postgres -d apps; do
  echo "Waiting for Postgres to be ready..."
  sleep 1
done

# Pipe SQL directly into the running container
docker exec -i my-postgres psql -q -U postgres -d apps <<EOF
CREATE TABLE apps (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner VARCHAR(255) NOT NULL,
    language VARCHAR(100) NOT NULL,
    framework VARCHAR(100) NOT NULL,
    namespace VARCHAR(100)
);

INSERT INTO apps (name, owner, language, framework, namespace) VALUES ('billing-engine', 'Ledger', 'Kotlin', 'Spring Boot', 'billing');
INSERT INTO apps (name, owner, language, framework) VALUES ('payment-gateway', 'Paystream', 'Python', 'FastAPI');
INSERT INTO apps (name, owner, language, framework, namespace) VALUES ('customer-portal', 'Horizon', 'Python', 'FastAPI', 'customer');
INSERT INTO apps (name, owner, language, framework) VALUES ('inventory-management', 'Stockpile', 'Python', 'FastAPI');
INSERT INTO apps (name, owner, language, framework) VALUES ('order-management', 'Fulfill', 'Kotlin', 'Spring Boot');
INSERT INTO apps (name, owner, language, framework) VALUES ('shipping-management', 'Dispatch', 'go', 'gin');
INSERT INTO apps (name, owner, language, framework) VALUES ('customer-support', 'Aegis', 'go', 'gin');
INSERT INTO apps (name, owner, language, framework) VALUES ('marketing-automation', 'Beacon', 'go', 'gin');
INSERT INTO apps (name, owner, language, framework) VALUES ('sales-automation', 'Velocity', 'go', 'gin');
EOF
