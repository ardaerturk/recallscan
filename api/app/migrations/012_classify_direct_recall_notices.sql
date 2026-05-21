update external_sources
set source_type = 'official_recall'
where canonical_url ilike '%fda.gov/safety/recalls-market-withdrawals-safety-alerts/%'
  and canonical_url not ilike '%/safety/recalls-market-withdrawals-safety-alerts'
  and canonical_url not ilike '%/safety/recalls-market-withdrawals-safety-alerts/major-product-recalls%';

update external_sources
set source_type = 'public_health_alert'
where canonical_url ilike '%fsis.usda.gov/recalls-alerts/%'
  and canonical_url not ilike '%/recalls-alerts';

update external_sources
set source_type = 'direct_recall_notice'
where source_type = 'external_signal'
  and title ~* '(^|[[:space:]])((issues?|announces?|initiates?|expands?)[[:space:]]+(a[[:space:]]+)?(voluntary[[:space:]]+)?recall|voluntarily[[:space:]]+recalls?|recalls?[[:space:]].*(because of|due to|for possible|potential|undeclared|allergy alert))'
  and title !~* '(what to check|how to check|list of|roundup|study|investigation|mmwr|linked to|tied to|brand-by-brand|fallout|cascade|sparks|recalled over|recalled after|fda warns|cdc)';

update exposure_matches
set
  tier = 'confirmed_match',
  match_type = 'brand_product',
  matched_fields_json = coalesce(matched_fields_json, '{}'::jsonb) || '{"direct_recall_notice": true}'::jsonb,
  missing_fields_json = '[]'::jsonb,
  explanation = 'Direct recall notice names the catalog product.',
  recommended_action = 'Pull matched SKU or lot from affected stores.'
from recall_signals
join external_sources on external_sources.id = recall_signals.source_id
where exposure_matches.recall_signal_id = recall_signals.id
  and exposure_matches.match_type = 'product_mention'
  and external_sources.source_type in ('official_recall', 'public_health_alert', 'direct_recall_notice');
