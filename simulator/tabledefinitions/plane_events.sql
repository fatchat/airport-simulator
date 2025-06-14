-- Table: public.plane_events

DROP TABLE IF EXISTS public.plane_events;

CREATE TABLE IF NOT EXISTS public.plane_events
(
    plane_id character varying(15) COLLATE pg_catalog."default" NOT NULL,
    flight_id character varying(15) COLLATE pg_catalog."default" NOT NULL,
    ticks bigint NOT NULL,
    event_time timestamptz not null,
    from_state character varying(25) COLLATE pg_catalog."default" NOT NULL,
    to_state character varying(25) COLLATE pg_catalog."default" NOT NULL
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.flights
    OWNER to airportsim;