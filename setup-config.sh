#!/bin/bash

set -e

CONFIG_DIR="./config"
DATABASE_DIR="./database"

# Function to get ini value
get_ini_value() {
    local section="$1"
    local key="$2"
    local file="$3"
    grep -A10 "^\[$section\]" "$file" | grep "^$key" | head -1 | cut -d'=' -f2 | xargs
}

# Copy example files
cp "$CONFIG_DIR/redis.example.conf" "$CONFIG_DIR/redis.conf"
cp "$CONFIG_DIR/backend.example.ini" "$CONFIG_DIR/backend.ini"

# Extract secrets
REDIS_PASSWORD=$(get_ini_value "REDIS" "PASSWORD" "$CONFIG_DIR/backend.ini")
REDIS_ROOT_PASSWORD=$(get_ini_value "REDIS" "ROOT_PASSWORD" "$CONFIG_DIR/backend.ini")
POSTGRES_USER=$(get_ini_value "POSTGRESQL" "USER" "$CONFIG_DIR/backend.ini")
POSTGRES_PASSWORD=$(get_ini_value "POSTGRESQL" "PASSWORD" "$CONFIG_DIR/backend.ini")
POSTGRES_DB=$(get_ini_value "POSTGRESQL" "DB" "$CONFIG_DIR/backend.ini")

# Replace in redis.conf
sed -i "s/<master-password>/$REDIS_ROOT_PASSWORD/g" "$CONFIG_DIR/redis.conf"
sed -i "s/<password>/$REDIS_PASSWORD/g" "$CONFIG_DIR/redis.conf"

# Create .env for postgres
cat > "$DATABASE_DIR/.env" << EOF
POSTGRES_USER=$POSTGRES_USER
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_DB=$POSTGRES_DB
EOF

sed -i '/^[[:space:]]*environment:/d' "$DATABASE_DIR/docker-compose.database.yaml"
sed -i '/^[[:space:]]*POSTGRES_USER:/d' "$DATABASE_DIR/docker-compose.database.yaml"
sed -i '/^[[:space:]]*POSTGRES_PASSWORD:/d' "$DATABASE_DIR/docker-compose.database.yaml"
sed -i '/^[[:space:]]*POSTGRES_DB:/d' "$DATABASE_DIR/docker-compose.database.yaml"

sed -i '/^[[:space:]]*env_file:/{N;d;}' "$DATABASE_DIR/docker-compose.database.yaml"
sed -i '/^[[:space:]]*- 5433:5432/a\    env_file:\n      - .env' "$DATABASE_DIR/docker-compose.database.yaml"

sed -i 's/-U", "example"/-U", "$POSTGRES_USER", "-d", "$POSTGRES_DB"/' "$DATABASE_DIR/docker-compose.database.yaml"
