CREATE TABLE users (
    discord_id BIGINT PRIMARY KEY,
    uuid VARCHAR(36) NOT NULL UNIQUE
);

CREATE TABLE sessions (
    uuid VARCHAR(36) PRIMARY KEY,
    wins INT NOT NULL,
    weighted INT NOT NULL,
    kills INT NOT NULL,
    finals INT NOT NULL,
    beds INT NOT NULL,
    star INT NOT NULL,
    xp BIGINT NOT NULL,
    start_time INT NOT NULL
);

CREATE TABLE historical_snapshots (
    uuid VARCHAR(36) NOT NULL,
    snapshot_date DATE NOT NULL,

    wins INT NOT NULL,
    weighted INT NOT NULL,
    kills INT NOT NULL,
    finals INT NOT NULL,
    beds INT NOT NULL,
    star INT NOT NULL,
    xp BIGINT NOT NULL,

    PRIMARY KEY (uuid, snapshot_date)
);

CREATE TABLE historical_players (
    uuid VARCHAR(36) PRIMARY KEY,
    tracked_since DATE NOT NULL
);

CREATE TABLE leaderboard_snapshot (
    type VARCHAR(50) PRIMARY KEY,
    data JSON NOT NULL,
    updated_at INT NOT NULL
);

CREATE TABLE leaderboard_channels (
    guild_id BIGINT PRIMARY KEY,
    channel_id BIGINT NOT NULL
);

CREATE TABLE accounts (
    discord_id BIGINT PRIMARY KEY,
    created_at INT NOT NULL,
    blacklisted BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE command_usage (
    command VARCHAR(100) NOT NULL,
    discord_id BIGINT NOT NULL,
    times_used INT NOT NULL DEFAULT 0,
    PRIMARY KEY (command, discord_id)
);

CREATE TABLE milestones (
    discord_id BIGINT NOT NULL,
    uuid VARCHAR(36) NOT NULL,
    type VARCHAR(64) NOT NULL,
    value BIGINT NOT NULL,
    threshold BIGINT NOT NULL,
    notified BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (discord_id, uuid, type)
);

CREATE TABLE server_config (
    server_id BIGINT PRIMARY KEY,
    chart_logs BIGINT NOT NULL,
    max_guilds INT NOT NULL DEFAULT 1
);

CREATE TABLE tracked_server_guilds (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    server_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    log_channel_id BIGINT NULL,
    UNIQUE KEY uq_server_guild (server_id, guild_id),
    FOREIGN KEY (server_id)
        REFERENCES server_config(server_id)
        ON DELETE CASCADE
);

CREATE TABLE tracked_guilds (
    guild_id BIGINT PRIMARY KEY,
    guild_xp BIGINT NOT NULL DEFAULT 0
);

CREATE TABLE tracked_players (
    uuid VARCHAR(36) PRIMARY KEY,
    guild_id BIGINT NULL,
    level INT NOT NULL DEFAULT 0,
    xp BIGINT NOT NULL DEFAULT 0,
    highest_week DOUBLE NOT NULL DEFAULT 0,
    FOREIGN KEY (guild_id)
        REFERENCES tracked_guilds(guild_id)
        ON DELETE CASCADE
);

CREATE TABLE player_past_weeks (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    uuid VARCHAR(36) NOT NULL,
    week INT NOT NULL,
    stars DOUBLE NOT NULL,
    UNIQUE KEY uq_uuid_week (uuid, week),
    FOREIGN KEY (uuid)
        REFERENCES tracked_players(uuid)
        ON DELETE CASCADE
);

CREATE TABLE last_week_updates (
    id INT PRIMARY KEY,
    xp_chart INT NOT NULL,
    gxp_chart INT NOT NULL
);

INSERT IGNORE INTO last_week_updates (
    id,
    xp_chart,
    gxp_chart
) VALUES (
    1,
    0,
    0
);

CREATE TABLE backgrounds (
    discord_id BIGINT UNSIGNED NOT NULL,
    background_id INT NOT NULL DEFAULT 1,

    PRIMARY KEY (discord_id)
);

CREATE TABLE tracked_guild_snapshots (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    gxp BIGINT NOT NULL,
    snapshot_date DATE NOT NULL,
    UNIQUE KEY uq_guild_snapshot_date (guild_id, snapshot_date),
    INDEX idx_snapshot_date (snapshot_date),
    FOREIGN KEY (guild_id)
        REFERENCES tracked_guilds(guild_id)
        ON DELETE CASCADE
);

CREATE TABLE guild_snapshot_reports (
    report_type ENUM('daily', 'weekly', 'monthly') NOT NULL,
    report_date DATE NOT NULL,
    PRIMARY KEY (report_type, report_date)
);