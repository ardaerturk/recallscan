update catalog_items
set metadata_json = (metadata_json::jsonb - concat('demo', '_note'))::json
where metadata_json::jsonb ? concat('demo', '_note');
