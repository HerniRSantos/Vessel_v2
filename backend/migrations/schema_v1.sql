-- Phase 1: Core Tables - PRD v1.2 Compliant
-- Run with: docker exec -i vessel_v2_db psql -U vessel_user -d vessels_db < migrations/schema_v1.sql

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- VESSELS MASTER TABLE
CREATE TABLE IF NOT EXISTS vessels_master (
    mmsi BIGINT PRIMARY KEY,
    name TEXT,
    vessel_type TEXT DEFAULT 'Desconhecido',
    flag TEXT,
    callsign TEXT,
    imo_number TEXT,
    dimension_a INTEGER,
    dimension_b INTEGER,
    dimension_c INTEGER,
    dimension_d INTEGER,
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ,
    last_updated TIMESTAMPTZ,
    destination TEXT,
    eta TEXT,
    draft REAL,
    suspicious BOOLEAN DEFAULT FALSE,
    suspect_reason TEXT,
    notes TEXT,
    position_count INTEGER DEFAULT 0
);

-- POSITIONS HISTORY TABLE (with raw_msg for forense)
CREATE TABLE IF NOT EXISTS positions (
    id BIGSERIAL PRIMARY KEY,
    mmsi BIGINT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    sog REAL,
    cog REAL,
    heading SMALLINT,
    nav_status INTEGER,
    timestamp TIMESTAMPTZ NOT NULL,
    raw_msg TEXT NOT NULL,
    geom GEOMETRY(Point, 4326)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_positions_mmsi_time ON positions(mmsi, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_positions_timestamp ON positions(timestamp);

-- Add foreign key after table exists
ALTER TABLE positions ADD CONSTRAINT fk_positions_vessel 
    FOREIGN KEY (mmsi) REFERENCES vessels_master(mmsi) ON DELETE CASCADE;

-- DEAD LETTER QUEUE (DLQ)
CREATE TABLE IF NOT EXISTS positions_dlq (
    id BIGSERIAL PRIMARY KEY,
    raw_msg TEXT NOT NULL,
    reject_reason TEXT NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed BOOLEAN DEFAULT FALSE
);

-- OCCURRENCES TABLE
CREATE TABLE IF NOT EXISTS occurrences (
    id BIGSERIAL PRIMARY KEY,
    mmsi BIGINT,
    severity TEXT,
    occurrence_type TEXT,
    description TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_occurrences_mmsi ON occurrences(mmsi);
CREATE INDEX IF NOT EXISTS idx_occurrences_type ON occurrences(occurrence_type);
CREATE INDEX IF NOT EXISTS idx_occurrences_time ON occurrences(start_time);

SELECT 'Schema v1 initialized' AS status;