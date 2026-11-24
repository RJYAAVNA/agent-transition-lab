INSERT INTO cloud_test_fixture (fixture_id, title)
VALUES ('sample-feed', 'Sample feed for cloud setup')
ON CONFLICT (fixture_id) DO UPDATE SET title = EXCLUDED.title;
