-- Table: public.flights

DROP TABLE IF EXISTS public.flights;

CREATE TABLE IF NOT EXISTS public.flights
(
    flight_id character varying(15) COLLATE pg_catalog."default" NOT NULL,
    plane_id character varying(15) COLLATE pg_catalog."default" NOT NULL,
    from_airport character varying(5) COLLATE pg_catalog."default",
    to_airport character varying(5) COLLATE pg_catalog."default",
    from_runway character varying(3) COLLATE pg_catalog."default",
    to_runway character varying(3) COLLATE pg_catalog."default",
    from_gate character varying(4) COLLATE pg_catalog."default",
    to_gate character varying(4) COLLATE pg_catalog."default",
    CONSTRAINT flights_pkey PRIMARY KEY (flight_id, plane_id)
)

TABLESPACE pg_default;

