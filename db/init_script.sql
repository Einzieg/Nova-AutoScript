CREATE TABLE IF NOT EXISTS module
(
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NULL,
    port INT          NULL
);

CREATE TABLE IF NOT EXISTS config
(
    id        INTEGER PRIMARY KEY,
    dark_mode blob         NOT NULL DEFAULT TRUE,
    email     VARCHAR(255) NULL,
    password  VARCHAR(255) NULL,
    receiver  VARCHAR(255) NULL
);

INSERT INTO config (id, dark_mode)
VALUES (1, 0x00);