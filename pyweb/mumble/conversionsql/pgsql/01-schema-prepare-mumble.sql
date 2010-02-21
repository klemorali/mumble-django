-- Model: Mumble
ALTER TABLE "mumble_mumble"
        ADD "server_id" integer NULL REFERENCES "mumble_mumbleserver" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "mumble_mumble"
        ADD "display" varchar(200);

CREATE INDEX "mumble_mumble_server_id" ON "mumble_mumble" ("server_id");
