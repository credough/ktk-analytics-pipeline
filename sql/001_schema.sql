-- One row per platform. The pipeline does not currently write to this table.
CREATE TABLE IF NOT EXISTS dim_platform (
    platform_id text NOT NULL,
    platform_name text NOT NULL,
    source_type text NOT NULL,
    CONSTRAINT dim_platform_pkey PRIMARY KEY (platform_id)
);

-- One follower-count observation for a platform and date. The pipeline does not currently write to this table.
CREATE TABLE IF NOT EXISTS dim_follower_count (
    id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
    platform_id text,
    date date NOT NULL,
    follower_count integer NOT NULL,
    CONSTRAINT dim_follower_count_pkey PRIMARY KEY (id),
    CONSTRAINT dim_follower_count_platform_id_date_key UNIQUE (platform_id, date),
    CONSTRAINT dim_follower_count_platform_id_fkey
        FOREIGN KEY (platform_id) REFERENCES dim_platform (platform_id)
);

-- One published post. The pipeline does not currently write to this table.
CREATE TABLE IF NOT EXISTS dim_posts (
    post_id text NOT NULL,
    platform_id text,
    publish_time timestamp without time zone,
    content_type text,
    CONSTRAINT dim_posts_pkey PRIMARY KEY (post_id),
    CONSTRAINT dim_posts_platform_id_fkey
        FOREIGN KEY (platform_id) REFERENCES dim_platform (platform_id)
);

-- One daily metric value for a platform and metric. This is the only table the pipeline currently populates.
CREATE TABLE IF NOT EXISTS fact_daily_metrics (
    id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
    date date NOT NULL,
    platform_id text,
    metric_name text NOT NULL,
    value numeric NOT NULL,
    CONSTRAINT fact_daily_metrics_pkey PRIMARY KEY (id),
    CONSTRAINT fact_daily_metrics_date_platform_id_metric_name_key
        UNIQUE (date, platform_id, metric_name),
    CONSTRAINT fact_daily_metrics_platform_id_fkey
        FOREIGN KEY (platform_id) REFERENCES dim_platform (platform_id)
);

-- One metric value for a post. The pipeline does not currently write to this table.
CREATE TABLE IF NOT EXISTS fact_post_metrics (
    id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
    post_id text,
    metric_name text NOT NULL,
    value numeric NOT NULL,
    CONSTRAINT fact_post_metrics_pkey PRIMARY KEY (id),
    CONSTRAINT fact_post_metrics_post_id_fkey
        FOREIGN KEY (post_id) REFERENCES dim_posts (post_id),
    CONSTRAINT fact_post_metrics_post_id_metric_name_key
        UNIQUE (post_id, metric_name)
);
