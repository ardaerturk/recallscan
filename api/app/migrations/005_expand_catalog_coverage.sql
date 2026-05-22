insert into stores (id, name, city, state, region, latitude, longitude)
values
  ('store_sf', 'Northstar Market Mission', 'San Francisco', 'CA', 'West', 37.7516, -122.4350),
  ('store_oak', 'Northstar Market Rockridge', 'Oakland', 'CA', 'West', 37.8044, -122.2712),
  ('store_bk', 'Northstar Market Williamsburg', 'Brooklyn', 'NY', 'Northeast', 40.7081, -73.9571),
  ('store_jer', 'Northstar Market Grove Street', 'Jersey City', 'NJ', 'Northeast', 40.7178, -74.0431),
  ('store_atl', 'Northstar Market Midtown', 'Atlanta', 'GA', 'South', 33.7838, -84.3839),
  ('store_col', 'Northstar Market Short North', 'Columbus', 'OH', 'Midwest', 39.9788, -83.0030),
  ('store_dal', 'Northstar Market Deep Ellum', 'Dallas', 'TX', 'South', 32.8218, -96.7877),
  ('store_chi', 'Northstar Market Wicker Park', 'Chicago', 'IL', 'Midwest', 41.9105, -87.6776),
  ('store_la', 'Northstar Market Silver Lake', 'Los Angeles', 'CA', 'West', 34.0928, -118.2807),
  ('store_sea', 'Northstar Market Capitol Hill', 'Seattle', 'WA', 'West', 47.6245, -122.3208),
  ('store_den', 'Northstar Market LoDo', 'Denver', 'CO', 'Mountain', 39.7530, -104.9990),
  ('store_phx', 'Northstar Market Arcadia', 'Phoenix', 'AZ', 'Southwest', 33.5092, -112.0719),
  ('store_mia', 'Northstar Market Brickell', 'Miami', 'FL', 'South', 25.7617, -80.1918),
  ('store_bos', 'Northstar Market Back Bay', 'Boston', 'MA', 'Northeast', 42.3505, -71.0763),
  ('store_phl', 'Northstar Market Rittenhouse', 'Philadelphia', 'PA', 'Northeast', 39.9496, -75.1669),
  ('store_msp', 'Northstar Market North Loop', 'Minneapolis', 'MN', 'Midwest', 44.9847, -93.2793),
  ('store_pdx', 'Northstar Market Pearl', 'Portland', 'OR', 'West', 45.5290, -122.6819),
  ('store_clt', 'Northstar Market South End', 'Charlotte', 'NC', 'South', 35.2138, -80.8571)
on conflict (id) do update set
  name = excluded.name,
  city = excluded.city,
  state = excluded.state,
  region = excluded.region,
  latitude = excluded.latitude,
  longitude = excluded.longitude;

insert into catalog_items (
  id, sku, brand, product_name, upc, category, supplier_name, co_manufacturer_name,
  ingredients_json, allergens_json, supplier_aliases_json, metadata_json
)
values
  (
    'cat_ghirardelli_cocoa', 'GHI-COCOA-DOUBLE-CHOC', 'Ghirardelli',
    'Double Chocolate Premium Hot Cocoa Mix', null, 'powdered drink mixes',
    'Ghirardelli Chocolate Company', null,
    '["cocoa", "sugar", "dry milk", "powdered milk"]'::jsonb,
    '["milk"]'::jsonb,
    '["Ghirardelli", "Ghirardelli Chocolate", "California Dairies Inc.", "California Dairies"]'::jsonb,
    '{"channels":["grocery"],"store_states":["CA","WA","CO","AZ","FL","MA"],"catalog_source":"bootstrap"}'::jsonb
  ),
  (
    'cat_great_value_pizza', 'GV-PIZZA-RISING-CRUST', 'Great Value',
    'Rising Crust Pepperoni Pizza', null, 'frozen pizza',
    'Walmart Private Brands', null,
    '["wheat flour", "mozzarella cheese", "tomato sauce", "milk powder"]'::jsonb,
    '["milk", "wheat"]'::jsonb,
    '["Great Value", "Walmart", "California Dairies Inc.", "California Dairies"]'::jsonb,
    '{"channels":["grocery"],"store_states":["CA","TX","IL","PA","NC"],"catalog_source":"bootstrap"}'::jsonb
  ),
  (
    'cat_zapps_voodoo_chips', 'ZAP-VOODOO-CHIPS', 'Zapp''s',
    'Voodoo Potato Chips', null, 'potato chips',
    'Utz Brands', null,
    '["potatoes", "vegetable oil", "seasoning blend", "whey powder"]'::jsonb,
    '["milk"]'::jsonb,
    '["Zapp''s", "Zapps", "Utz", "Utz Brands", "California Dairies Inc."]'::jsonb,
    '{"channels":["grocery"],"store_states":["GA","FL","NC","TX","PA"],"catalog_source":"bootstrap"}'::jsonb
  ),
  (
    'cat_kars_trail_mix', 'KARS-SWEET-SALTY-MIX', 'Kar''s',
    'Sweet ''n Salty Trail Mix', null, 'trail mix',
    'Second Nature Brands', null,
    '["peanuts", "raisins", "sunflower kernels", "milk chocolate candies"]'::jsonb,
    '["milk", "peanuts", "tree nuts"]'::jsonb,
    '["Kar''s", "Kars", "Second Nature Brands"]'::jsonb,
    '{"channels":["grocery"],"store_states":["OH","MI","IL","MN","PA"],"catalog_source":"bootstrap"}'::jsonb
  ),
  (
    'cat_david_sunflower_seeds', 'DAVID-SUNFLOWER-ORIGINAL', 'David',
    'Original Sunflower Seeds', null, 'sunflower seeds',
    'Conagra Brands', null,
    '["sunflower seeds", "salt"]'::jsonb,
    '[]'::jsonb,
    '["David", "Conagra", "Conagra Brands"]'::jsonb,
    '{"channels":["grocery"],"store_states":["CA","AZ","CO","TX"],"catalog_source":"bootstrap"}'::jsonb
  ),
  (
    'cat_organic_valley_eggs', 'OV-LARGE-BROWN-EGGS', 'Organic Valley',
    'Large Brown Eggs', null, 'eggs',
    'Organic Valley', null,
    '["eggs"]'::jsonb,
    '["eggs"]'::jsonb,
    '["Organic Valley", "CROPP Cooperative"]'::jsonb,
    '{"channels":["grocery"],"store_states":["CA","WA","OR","NY","MA","PA"],"catalog_source":"bootstrap"}'::jsonb
  ),
  (
    'cat_365_walnuts', '365-ORGANIC-WALNUTS', '365 by Whole Foods Market',
    'Organic Walnut Halves and Pieces', null, 'walnuts',
    'Whole Foods Market', null,
    '["organic walnuts"]'::jsonb,
    '["tree nuts"]'::jsonb,
    '["Whole Foods", "Whole Foods Market", "365"]'::jsonb,
    '{"channels":["grocery"],"store_states":["CA","NY","NJ","MA","PA"],"catalog_source":"bootstrap"}'::jsonb
  ),
  (
    'cat_dole_cantaloupe_chunks', 'DOLE-CANTALOUPE-CHUNKS', 'Dole',
    'Cantaloupe Chunks', null, 'cantaloupe',
    'Dole Fresh Produce', null,
    '["cantaloupe"]'::jsonb,
    '[]'::jsonb,
    '["Dole", "Dole Fresh Produce"]'::jsonb,
    '{"channels":["grocery"],"store_states":["CA","AZ","CO","TX","FL"],"catalog_source":"bootstrap"}'::jsonb
  ),
  (
    'cat_wawona_peach_slices', 'WAWONA-FROZEN-PEACHES', 'Wawona',
    'Frozen Peach Slices', null, 'peaches',
    'Wawona Frozen Foods', null,
    '["peaches"]'::jsonb,
    '[]'::jsonb,
    '["Wawona", "Wawona Frozen Foods"]'::jsonb,
    '{"channels":["grocery"],"store_states":["CA","WA","OR","AZ"],"catalog_source":"bootstrap"}'::jsonb
  ),
  (
    'cat_raw_farm_cheddar', 'RAWFARM-RAW-CHEDDAR', 'Raw Farm',
    'Raw Milk Cheddar Cheese', null, 'dairy cheese',
    'Raw Farm', null,
    '["raw milk", "cheese", "salt", "cultures"]'::jsonb,
    '["milk"]'::jsonb,
    '["Raw Farm", "Raw Farm LLC"]'::jsonb,
    '{"channels":["grocery"],"store_states":["CA","WA","OR","AZ"],"catalog_source":"bootstrap"}'::jsonb
  ),
  (
    'cat_spring_mulberry_bar', 'SM-CHOCOLATE-BAR', 'Spring & Mulberry',
    'Date-Sweetened Chocolate Bar', null, 'chocolate bars',
    'Spring & Mulberry', null,
    '["cocoa", "dates", "cocoa butter"]'::jsonb,
    '[]'::jsonb,
    '["Spring & Mulberry", "Spring and Mulberry"]'::jsonb,
    '{"channels":["grocery"],"store_states":["NY","NJ","MA","PA","CA"],"catalog_source":"bootstrap"}'::jsonb
  ),
  (
    'cat_diamond_shruumz_bar', 'DIAMOND-SHRUUMZ-DARK-CHOC', 'Diamond Shruumz',
    'Dark Chocolate Bar', null, 'mushroom chocolate',
    'Prophet Premium Blends', 'Prophet Premium Blends',
    '["chocolate", "mushroom blend"]'::jsonb,
    '[]'::jsonb,
    '["Diamond Shruumz", "Prophet Premium Blends"]'::jsonb,
    '{"channels":["grocery"],"store_states":["CA","NY","FL","TX","IL"],"catalog_source":"bootstrap"}'::jsonb
  ),
  (
    'cat_ghirardelli_chocolate_bar', 'GHI-DARK-CHOCOLATE-BAR', 'Ghirardelli',
    'Dark Chocolate Bar', null, 'chocolate bars',
    'Ghirardelli Chocolate Company', null,
    '["cocoa", "sugar", "cocoa butter"]'::jsonb,
    '[]'::jsonb,
    '["Ghirardelli", "Ghirardelli Chocolate"]'::jsonb,
    '{"channels":["grocery"],"store_states":["CA","WA","CO","AZ","FL","MA"],"catalog_source":"bootstrap"}'::jsonb
  )
on conflict (id) do update set
  sku = excluded.sku,
  brand = excluded.brand,
  product_name = excluded.product_name,
  upc = excluded.upc,
  category = excluded.category,
  supplier_name = excluded.supplier_name,
  co_manufacturer_name = excluded.co_manufacturer_name,
  ingredients_json = excluded.ingredients_json,
  allergens_json = excluded.allergens_json,
  supplier_aliases_json = excluded.supplier_aliases_json,
  metadata_json = excluded.metadata_json,
  updated_at = now();

update catalog_items
set metadata_json = coalesce(metadata_json, '{}'::jsonb) || '{"store_states":["CA","NY","TX"],"catalog_source":"bootstrap"}'::jsonb
where id = 'cat_fbj_sesame_single';

update catalog_items
set metadata_json = coalesce(metadata_json, '{}'::jsonb) || '{"store_states":["CA","IL"],"catalog_source":"bootstrap"}'::jsonb
where id = 'cat_fbj_sauce';

update catalog_items
set metadata_json = coalesce(metadata_json, '{}'::jsonb) || '{"store_states":["GA","OH","IL"],"catalog_source":"bootstrap"}'::jsonb
where id = 'cat_kroger_croutons';

update catalog_items
set metadata_json = coalesce(metadata_json, '{}'::jsonb) || '{"store_states":["NY","NJ","CA"],"catalog_source":"bootstrap"}'::jsonb
where id = 'cat_ns_croutons';

update catalog_items
set metadata_json = coalesce(metadata_json, '{}'::jsonb) || '{"store_states":["CA","WA"],"catalog_source":"bootstrap"}'::jsonb
where id = 'cat_gg_snackmix';

update catalog_items
set metadata_json = coalesce(metadata_json, '{}'::jsonb) || '{"store_states":["CA"],"catalog_source":"bootstrap"}'::jsonb
where id = 'cat_leafy_greens';

insert into inventory_lots (id, catalog_item_id, store_id, lot_code, quantity_on_hand)
values
  ('lot_ghirardelli_cocoa_la', 'cat_ghirardelli_cocoa', 'store_la', 'COCOA-0526-A', 38),
  ('lot_ghirardelli_cocoa_sea', 'cat_ghirardelli_cocoa', 'store_sea', 'COCOA-0526-B', 24),
  ('lot_ghirardelli_cocoa_den', 'cat_ghirardelli_cocoa', 'store_den', 'COCOA-0526-C', 19),
  ('lot_gv_pizza_chi', 'cat_great_value_pizza', 'store_chi', 'PIZZA-0526-IL', 27),
  ('lot_gv_pizza_dal', 'cat_great_value_pizza', 'store_dal', 'PIZZA-0526-TX', 31),
  ('lot_gv_pizza_clt', 'cat_great_value_pizza', 'store_clt', 'PIZZA-0526-NC', 22),
  ('lot_zapps_mia', 'cat_zapps_voodoo_chips', 'store_mia', 'ZAP-0526-FL', 46),
  ('lot_zapps_atl', 'cat_zapps_voodoo_chips', 'store_atl', 'ZAP-0526-GA', 34),
  ('lot_zapps_phl', 'cat_zapps_voodoo_chips', 'store_phl', 'ZAP-0526-PA', 29),
  ('lot_kars_msp', 'cat_kars_trail_mix', 'store_msp', 'TRAIL-0426-MN', 41),
  ('lot_kars_chi', 'cat_kars_trail_mix', 'store_chi', 'TRAIL-0426-IL', 33),
  ('lot_kars_col', 'cat_kars_trail_mix', 'store_col', 'TRAIL-0426-OH', 28),
  ('lot_david_phx', 'cat_david_sunflower_seeds', 'store_phx', 'SUN-0426-AZ', 52),
  ('lot_david_den', 'cat_david_sunflower_seeds', 'store_den', 'SUN-0426-CO', 37),
  ('lot_eggs_bos', 'cat_organic_valley_eggs', 'store_bos', 'EGG-0625-MA', 64),
  ('lot_eggs_bk', 'cat_organic_valley_eggs', 'store_bk', 'EGG-0625-NY', 58),
  ('lot_eggs_pdx', 'cat_organic_valley_eggs', 'store_pdx', 'EGG-0625-OR', 49),
  ('lot_walnuts_jer', 'cat_365_walnuts', 'store_jer', 'WAL-1125-NJ', 21),
  ('lot_walnuts_bos', 'cat_365_walnuts', 'store_bos', 'WAL-1125-MA', 26),
  ('lot_cantaloupe_phx', 'cat_dole_cantaloupe_chunks', 'store_phx', 'MELON-0825-AZ', 44),
  ('lot_cantaloupe_dal', 'cat_dole_cantaloupe_chunks', 'store_dal', 'MELON-0825-TX', 39),
  ('lot_peaches_la', 'cat_wawona_peach_slices', 'store_la', 'PEACH-0825-CA', 35),
  ('lot_peaches_pdx', 'cat_wawona_peach_slices', 'store_pdx', 'PEACH-0825-OR', 25),
  ('lot_rawfarm_sf', 'cat_raw_farm_cheddar', 'store_sf', 'RAW-0326-CA', 18),
  ('lot_rawfarm_la', 'cat_raw_farm_cheddar', 'store_la', 'RAW-0326-LA', 22),
  ('lot_spring_mulberry_bk', 'cat_spring_mulberry_bar', 'store_bk', 'SM-1225-NY', 36),
  ('lot_spring_mulberry_phl', 'cat_spring_mulberry_bar', 'store_phl', 'SM-1225-PA', 19),
  ('lot_diamond_shruumz_mia', 'cat_diamond_shruumz_bar', 'store_mia', 'DS-0725-FL', 14),
  ('lot_diamond_shruumz_dal', 'cat_diamond_shruumz_bar', 'store_dal', 'DS-0725-TX', 17),
  ('lot_ghirardelli_bar_den', 'cat_ghirardelli_chocolate_bar', 'store_den', 'GHI-BAR-1225-CO', 43),
  ('lot_ghirardelli_bar_bos', 'cat_ghirardelli_chocolate_bar', 'store_bos', 'GHI-BAR-1225-MA', 29)
on conflict (id) do update set
  catalog_item_id = excluded.catalog_item_id,
  store_id = excluded.store_id,
  lot_code = excluded.lot_code,
  quantity_on_hand = excluded.quantity_on_hand,
  last_seen_at = now();
