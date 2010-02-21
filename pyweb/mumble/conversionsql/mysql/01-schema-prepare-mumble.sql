BEGIN;
-- Model: Mumble
ALTER TABLE `mumble_mumble`
        ADD `server_id` integer FIRST;
ALTER TABLE `mumble_mumble`
        ADD `display` varchar(200) AFTER `name`;
COMMIT;

BEGIN;
CREATE INDEX `mumble_mumble_server_id_idx`
        ON `mumble_mumble` (`server_id`);
COMMIT;
