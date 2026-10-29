INSERT INTO dim_platform (platform_id, platform_name, source_type)
VALUES
    ('fb', 'Facebook', 'social'),
    ('ig', 'Instagram', 'social'),
    ('linkedin', 'LinkedIn', 'social'),
    ('ads', 'Ads', 'paid'),
    ('brevo', 'Brevo', 'email')
ON CONFLICT DO NOTHING;
