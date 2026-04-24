-- PostgreSQL Schema for Vessel V2 - PRD v1.2 Compliant
-- Uses PostGIS 3.4 for geoespatial queries

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- VESSELS MASTER TABLE
-- ============================================
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

-- ============================================
-- POSITIONS HISTORY TABLE (with raw_msg for forense)
-- ============================================
CREATE TABLE IF NOT EXISTS positions (
    id BIGSERIAL PRIMARY KEY,
    mmsi BIGINT NOT NULL REFERENCES vessels_master(mmsi),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    sog REAL,  -- Speed Over Ground
    cog REAL,  -- Course Over Ground
    heading SMALLINT,  -- True Heading (0-359)
    nav_status INTEGER,
    timestamp TIMESTAMPTZ NOT NULL,
    raw_msg TEXT NOT NULL,  -- NMEA/AIS original message - forense
    geom GEOMETRY(Point, 4326)  -- PostGIS geometry
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_positions_mmsi_time ON positions(mmsi, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_positions_timestamp ON positions(timestamp);
CREATE INDEX IF NOT EXISTS idx_positions_geom ON positions USING GIST(geom);

-- ============================================
-- DEAD LETTER QUEUE (DLQ)
-- ============================================
CREATE TABLE IF NOT EXISTS positions_dlq (
    id BIGSERIAL PRIMARY KEY,
    raw_msg TEXT NOT NULL,  -- Original message received (corrupted or suspicious)
    reject_reason TEXT NOT NULL,  -- Rejection reason (e.g., invalid MMSI, checksum failed)
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed BOOLEAN DEFAULT FALSE
);

-- ============================================
-- OCCURRENCES / THREATS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS occurrences (
    id BIGSERIAL PRIMARY KEY,
    mmsi BIGINT REFERENCES vessels_master(mmsi),
    severity TEXT,  -- low, medium, high, critical
    occurrence_type TEXT,  -- dark_vessel, rendezvous, spoofing, etc.
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

-- ============================================
-- DARK EVENTS VIEW (computed gaps/dark vessels)
-- ============================================
-- This view computes gaps in AIS signal for each vessel
-- A "dark event" is when a vessel disappears for > 2 hours in open sea

-- Function to detect dark events
CREATE OR REPLACE FUNCTION detect_dark_events()
RETURNS TABLE (
    mmsi BIGINT,
    last_lat DOUBLE PRECISION,
    last_lon DOUBLE PRECISION,
    last_time TIMESTAMPTZ,
    gap_minutes DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    WITH vessel_last_position AS (
        SELECT 
            mmsi,
            latitude AS last_lat,
            longitude AS last_lon,
            timestamp AS last_time,
            LAG(timestamp) OVER w AS prev_time,
            LAG(latitude) OVER w AS prev_lat,
            LAG(longitude) OVER w AS prev_lon
        FROM positions
        WINDOW w AS (PARTITION BY mmsi ORDER BY timestamp)
    )
    SELECT 
        v.mmsi,
        v.last_lat,
        v.last_lon,
        v.last_time,
        EXTRACT(EPOCH FROM (v.last_time - v.prev_time)) / 60.0 AS gap_minutes
    FROM vessel_last_position v
    WHERE v.prev_time IS NOT NULL
      AND (v.last_time - v.prev_time) > INTERVAL '2 hours'
      AND (
        -- Check if last position is in open sea (> 12 NM from coast)
        -- Simplified: assume all positions are potential dark events
        TRUE
      )
    ORDER BY v.last_time DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- RETENTION POLICY FUNCTION
-- ============================================
-- HOT (0-3 months): full granularity, immediate access
-- WARM (3-12 months): aggregated to 5-min intervals in non-classified zones
-- COLD (> 12 months): export to Parquet, remove from active DB

-- Function to apply retention policy
CREATE OR REPLACE FUNCTION apply_retention_policy()
RETURNS void AS $$
DECLARE
    warm_cutoff TIMESTAMPTZ := NOW() - INTERVAL '3 months';
    cold_cutoff TIMESTAMPTZ := NOW() - INTERVAL '12 months';
BEGIN
    -- Mark suspicious vessels for indefinite retention
    -- (handled in query logic, not deletion)

    -- Delete positions older than 12 months (except suspicious vessels)
    DELETE FROM positions p
    WHERE p.timestamp < cold_cutoff
      AND NOT EXISTS (
          SELECT 1 FROM vessels_master v
          WHERE v.mmsi = p.mmsi AND v.suspicious = TRUE
      );

    -- Log retention action
    RAISE NOTICE 'Retention policy applied: removed positions older than 12 months';
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- FUNCTIONS FOR API
-- ============================================

-- Get vessel's last known position
CREATE OR REPLACE FUNCTION get_vessel_position(p_mmsi BIGINT)
RETURNS TABLE (
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    sog REAL,
    cog REAL,
    timestamp TIMESTAMPTZ,
    raw_msg TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.latitude,
        p.longitude,
        p.sog,
        p.cog,
        p.timestamp,
        p.raw_msg
    FROM positions p
    WHERE p.mmsi = p_mmsi
    ORDER BY p.timestamp DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Get vessel trail within time range
CREATE OR REPLACE FUNCTION get_vessel_trail(
    p_mmsi BIGINT,
    p_hours INTEGER DEFAULT 24
)
RETURNS TABLE (
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    sog REAL,
    cog REAL,
    true_heading SMALLINT,
    timestamp TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.latitude,
        p.longitude,
        p.sog,
        p.cog,
        p.heading,
        p.timestamp
    FROM positions p
    WHERE p.mmsi = p_mmsi
      AND p.timestamp > NOW() - (p_hours || ' hours')::INTERVAL
    ORDER BY p.timestamp ASC;
END;
$$ LANGUAGE plpgsql;

-- Get active vessels (seen in last 24 hours)
CREATE OR REPLACE FUNCTION get_active_vessels()
RETURNS TABLE (
    mmsi BIGINT,
    name TEXT,
    vessel_type TEXT,
    flag TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    timestamp TIMESTAMPTZ,
    suspicious BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        v.mmsi,
        v.name,
        v.vessel_type,
        v.flag,
        p.latitude,
        p.longitude,
        p.timestamp,
        v.suspicious
    FROM vessels_master v
    JOIN LATERAL (
        SELECT latitude, longitude, timestamp
        FROM positions
        WHERE mmsi = v.mmsi
        ORDER BY timestamp DESC
        LIMIT 1
    ) p ON TRUE
    WHERE p.timestamp > NOW() - INTERVAL '1 hour'
    ORDER BY p.timestamp DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- GRANTS FOR APPLICATION USER
-- ============================================
-- NOTE: Execute as superuser or database owner
-- GRANT USAGE ON SCHEMA public TO vessel_user;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO vessel_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO vessel_user;