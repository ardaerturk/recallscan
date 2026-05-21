update external_sources
set source_type = 'outbreak_update'
where canonical_url ilike '%fda.gov/food/outbreaks-foodborne-illness/%';

update external_sources
set source_type = 'external_signal'
where source_domain ilike '%fsis.usda.gov'
  and canonical_url not ilike '%fsis.usda.gov/recalls-alerts/%';

update external_sources
set source_type = 'external_signal'
where source_domain ilike '%fda.gov'
  and canonical_url not ilike '%fda.gov/safety/recalls-market-withdrawals-safety-alerts/%'
  and canonical_url not ilike '%fda.gov/food/outbreaks-foodborne-illness/%';

update exposure_matches
set
  tier = 'watch_only',
  match_type = 'product_mention',
  matched_fields_json = matched_fields_json || '{"direct_recall_notice_required": true}'::jsonb,
  missing_fields_json = '["direct recall notice"]'::jsonb,
  explanation = 'The product is mentioned, but the source is not a direct recall notice or safety alert.',
  recommended_action = 'Monitor for product, UPC, lot, or supplier confirmation.'
from recall_signals
join external_sources on external_sources.id = recall_signals.source_id
where exposure_matches.recall_signal_id = recall_signals.id
  and exposure_matches.tier = 'confirmed_match'
  and external_sources.source_type not in ('official_recall', 'public_health_alert');
