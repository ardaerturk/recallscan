delete from exposure_matches
where recall_signal_id in (
  select recall_signals.id
  from recall_signals
  join external_sources on external_sources.id = recall_signals.source_id
  where external_sources.source_type = 'simulation'
     or external_sources.canonical_url like 'simulation://%'
);

delete from recall_signals
using external_sources
where external_sources.id = recall_signals.source_id
  and (
    external_sources.source_type = 'simulation'
    or external_sources.canonical_url like 'simulation://%'
  );

delete from external_sources
where source_type = 'simulation'
   or canonical_url like 'simulation://%';

alter table recall_signals drop column if exists is_simulated;

insert into catalog_items (
  id, sku, brand, product_name, upc, category, supplier_name, co_manufacturer_name,
  ingredients_json, allergens_json, supplier_aliases_json, metadata_json
)
values
  (
    'cat_ghirardelli_powdered_drinks', 'GHI-POWDERED-DRINK-MIXES', 'Ghirardelli',
    'Powdered Drink Mixes', null, 'powdered drink mixes',
    'Ghirardelli Chocolate Company', null,
    '["cocoa", "sugar", "dry milk", "powdered milk"]'::jsonb,
    '["milk"]'::jsonb,
    '["Ghirardelli", "Ghirardelli Chocolate", "California Dairies Inc.", "California Dairies"]'::jsonb,
    '{"channels":["grocery"],"store_states":["CA","WA","CO","AZ","FL","MA"],"catalog_source":"bootstrap"}'::jsonb
  ),
  (
    'cat_parents_choice_rice_cereal', 'PC-RICE-BABY-CEREAL', 'Parent''s Choice',
    'Rice Baby Cereal', null, 'baby food',
    'Walmart Private Brands', null,
    '["rice flour", "vitamins", "minerals"]'::jsonb,
    '[]'::jsonb,
    '["Parent''s Choice", "Parents Choice", "Walmart"]'::jsonb,
    '{"channels":["grocery"],"store_states":["CA","TX","IL","GA","OH"],"catalog_source":"bootstrap"}'::jsonb
  ),
  (
    'cat_black_sheep_eggs', 'BSE-BROWN-EGGS', 'Black Sheep Egg Company',
    'Eggs', null, 'eggs',
    'Black Sheep Egg Company', null,
    '["eggs"]'::jsonb,
    '["eggs"]'::jsonb,
    '["Black Sheep Egg Company"]'::jsonb,
    '{"channels":["grocery"],"store_states":["CA","OR","WA"],"catalog_source":"bootstrap"}'::jsonb
  ),
  (
    'cat_sun_hong_enoki', 'SUNHONG-ENOKI-MUSHROOMS', 'Sun Hong Foods',
    'Enoki Mushrooms', null, 'mushrooms',
    'Sun Hong Foods, Inc.', null,
    '["enoki mushrooms"]'::jsonb,
    '[]'::jsonb,
    '["Sun Hong Foods", "Sun Hong Foods Inc."]'::jsonb,
    '{"channels":["grocery"],"store_states":["CA","NY","NJ","PA"],"catalog_source":"bootstrap"}'::jsonb
  ),
  (
    'cat_fulvic_care_powder_tablets', 'FULVIC-CARE-POWDER-TABLETS', 'Fulvic Care',
    'Powder and Tablets', null, 'supplements',
    'Fulvic Care', null,
    '["fulvic mineral powder"]'::jsonb,
    '[]'::jsonb,
    '["Fulvic Care"]'::jsonb,
    '{"channels":["grocery","wellness"],"store_states":["CA","NY","FL","TX"],"catalog_source":"bootstrap"}'::jsonb
  ),
  (
    'cat_felix_smoked_seafood', 'FELIX-SMOKED-SEAFOOD', 'Felix Custom Smoking',
    'Seafood Products', null, 'seafood',
    'Felix Custom Smoking', null,
    '["smoked seafood"]'::jsonb,
    '["fish", "shellfish"]'::jsonb,
    '["Felix Custom Smoking", "Felix Custom Smoking Seafood"]'::jsonb,
    '{"channels":["grocery"],"store_states":["WA","OR","CA"],"catalog_source":"bootstrap"}'::jsonb
  ),
  (
    'cat_little_hatch_ready_to_eat', 'LITTLE-HATCH-RTE-FOODS', 'Little Hatch''s',
    'Ready To Eat Foods', null, 'ready-to-eat foods',
    'Little Hatch''s', null,
    '["prepared foods"]'::jsonb,
    '[]'::jsonb,
    '["Little Hatch''s", "Little Hatchs"]'::jsonb,
    '{"channels":["grocery"],"store_states":["TX","AZ","CO"],"catalog_source":"bootstrap"}'::jsonb
  ),
  (
    'cat_nutramigen_formula', 'NUTRAMIGEN-HYPO-FORMULA', 'Nutramigen',
    'Hypoallergenic Powdered Infant Formula Products', null, 'infant formula',
    'Reckitt Mead Johnson', 'Mead Johnson',
    '["powdered infant formula"]'::jsonb,
    '["milk"]'::jsonb,
    '["Nutramigen", "Mead Johnson", "Reckitt"]'::jsonb,
    '{"channels":["grocery"],"store_states":["CA","NY","TX","IL","FL"],"catalog_source":"bootstrap"}'::jsonb
  ),
  (
    'cat_diamond_shruumz_chocolate_bars', 'DIAMOND-SHRUUMZ-CHOCOLATE-BARS', 'Diamond Shruumz',
    'Chocolate Bars', null, 'mushroom chocolate',
    'Prophet Premium Blends', 'Prophet Premium Blends',
    '["chocolate", "mushroom blend"]'::jsonb,
    '[]'::jsonb,
    '["Diamond Shruumz", "Prophet Premium Blends"]'::jsonb,
    '{"channels":["grocery"],"store_states":["CA","NY","FL","TX","IL"],"catalog_source":"bootstrap"}'::jsonb
  ),
  (
    'cat_diamond_shruumz_gummies', 'DIAMOND-SHRUUMZ-GUMMIES', 'Diamond Shruumz',
    'Gummies', null, 'mushroom gummies',
    'Prophet Premium Blends', 'Prophet Premium Blends',
    '["gummies", "mushroom blend"]'::jsonb,
    '[]'::jsonb,
    '["Diamond Shruumz", "Prophet Premium Blends"]'::jsonb,
    '{"channels":["grocery"],"store_states":["CA","NY","FL","TX"],"catalog_source":"bootstrap"}'::jsonb
  ),
  (
    'cat_diamond_shruumz_cones', 'DIAMOND-SHRUUMZ-CONES', 'Diamond Shruumz',
    'Cones', null, 'mushroom cones',
    'Prophet Premium Blends', 'Prophet Premium Blends',
    '["cones", "mushroom blend"]'::jsonb,
    '[]'::jsonb,
    '["Diamond Shruumz", "Prophet Premium Blends"]'::jsonb,
    '{"channels":["grocery"],"store_states":["CA","NY","FL"],"catalog_source":"bootstrap"}'::jsonb
  ),
  (
    'cat_spring_mulberry_select_bars', 'SM-SELECT-CHOCOLATE-BARS', 'Spring & Mulberry',
    'Select Chocolate Bars', null, 'chocolate bars',
    'Spring & Mulberry', null,
    '["cocoa", "dates", "cocoa butter"]'::jsonb,
    '[]'::jsonb,
    '["Spring & Mulberry", "Spring and Mulberry"]'::jsonb,
    '{"channels":["grocery"],"store_states":["NY","NJ","MA","PA","CA"],"catalog_source":"bootstrap"}'::jsonb
  ),
  (
    'cat_sour_cream_onion_cheese_curds', 'CHEESE-CURDS-SOUR-CREAM-ONION', 'Westby Cooperative Creamery',
    'Sour Cream and Onion Cheese Curds', null, 'cheese curds',
    'Westby Cooperative Creamery', null,
    '["cheese", "milk", "sour cream and onion seasoning"]'::jsonb,
    '["milk"]'::jsonb,
    '["Westby Cooperative Creamery"]'::jsonb,
    '{"channels":["grocery"],"store_states":["WI","IL","MN"],"catalog_source":"bootstrap"}'::jsonb
  ),
  (
    'cat_white_cheddar_seasoning', 'GRIFFITH-WHITE-CHEDDAR-SEASONING', 'Griffith Foods',
    'White Cheddar Seasoning Products', null, 'seasoning',
    'Griffith Foods', 'Griffith Foods',
    '["white cheddar seasoning", "milk powder"]'::jsonb,
    '["milk"]'::jsonb,
    '["Griffith Foods"]'::jsonb,
    '{"channels":["grocery"],"store_states":["IL","OH","PA","NY"],"catalog_source":"bootstrap"}'::jsonb
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

insert into inventory_lots (id, catalog_item_id, store_id, lot_code, quantity_on_hand)
values
  ('lot_ghirardelli_drinks_la', 'cat_ghirardelli_powdered_drinks', 'store_la', 'GHI-DRINK-0526-CA', 26),
  ('lot_ghirardelli_drinks_sea', 'cat_ghirardelli_powdered_drinks', 'store_sea', 'GHI-DRINK-0526-WA', 18),
  ('lot_parents_choice_dal', 'cat_parents_choice_rice_cereal', 'store_dal', 'PC-RICE-0426-TX', 34),
  ('lot_parents_choice_chi', 'cat_parents_choice_rice_cereal', 'store_chi', 'PC-RICE-0426-IL', 27),
  ('lot_black_sheep_pdx', 'cat_black_sheep_eggs', 'store_pdx', 'BSE-0426-OR', 48),
  ('lot_black_sheep_sea', 'cat_black_sheep_eggs', 'store_sea', 'BSE-0426-WA', 42),
  ('lot_sun_hong_sf', 'cat_sun_hong_enoki', 'store_sf', 'ENOKI-0426-CA', 32),
  ('lot_sun_hong_bk', 'cat_sun_hong_enoki', 'store_bk', 'ENOKI-0426-NY', 24),
  ('lot_fulvic_mia', 'cat_fulvic_care_powder_tablets', 'store_mia', 'FULVIC-0426-FL', 15),
  ('lot_fulvic_bk', 'cat_fulvic_care_powder_tablets', 'store_bk', 'FULVIC-0426-NY', 11),
  ('lot_felix_sea', 'cat_felix_smoked_seafood', 'store_sea', 'FELIX-SEA-0426-WA', 19),
  ('lot_felix_pdx', 'cat_felix_smoked_seafood', 'store_pdx', 'FELIX-SEA-0426-OR', 16),
  ('lot_little_hatch_dal', 'cat_little_hatch_ready_to_eat', 'store_dal', 'LH-RTE-0426-TX', 29),
  ('lot_little_hatch_phx', 'cat_little_hatch_ready_to_eat', 'store_phx', 'LH-RTE-0426-AZ', 23),
  ('lot_nutramigen_chi', 'cat_nutramigen_formula', 'store_chi', 'NUTRA-0426-IL', 21),
  ('lot_nutramigen_mia', 'cat_nutramigen_formula', 'store_mia', 'NUTRA-0426-FL', 17),
  ('lot_diamond_bars_la', 'cat_diamond_shruumz_chocolate_bars', 'store_la', 'DS-BARS-0426-CA', 22),
  ('lot_diamond_bars_bk', 'cat_diamond_shruumz_chocolate_bars', 'store_bk', 'DS-BARS-0426-NY', 18),
  ('lot_diamond_gummies_mia', 'cat_diamond_shruumz_gummies', 'store_mia', 'DS-GUM-0426-FL', 20),
  ('lot_diamond_gummies_dal', 'cat_diamond_shruumz_gummies', 'store_dal', 'DS-GUM-0426-TX', 16),
  ('lot_diamond_cones_sf', 'cat_diamond_shruumz_cones', 'store_sf', 'DS-CONE-0426-CA', 14),
  ('lot_spring_select_bk', 'cat_spring_mulberry_select_bars', 'store_bk', 'SM-SEL-1225-NY', 24),
  ('lot_spring_select_phl', 'cat_spring_mulberry_select_bars', 'store_phl', 'SM-SEL-1225-PA', 21),
  ('lot_cheese_curds_chi', 'cat_sour_cream_onion_cheese_curds', 'store_chi', 'CURD-1225-IL', 28),
  ('lot_cheese_curds_msp', 'cat_sour_cream_onion_cheese_curds', 'store_msp', 'CURD-1225-MN', 24),
  ('lot_white_cheddar_col', 'cat_white_cheddar_seasoning', 'store_col', 'WCHED-1225-OH', 31),
  ('lot_white_cheddar_phl', 'cat_white_cheddar_seasoning', 'store_phl', 'WCHED-1225-PA', 26)
on conflict (id) do update set
  catalog_item_id = excluded.catalog_item_id,
  store_id = excluded.store_id,
  lot_code = excluded.lot_code,
  quantity_on_hand = excluded.quantity_on_hand,
  last_seen_at = now();
