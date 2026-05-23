update external_sources
set source_type = 'external_signal'
where source_type = 'direct_recall_notice'
  and canonical_url not ilike '%fda.gov/safety/recalls-market-withdrawals-safety-alerts/%'
  and canonical_url not ilike '%fsis.usda.gov/recalls-alerts/%';

update exposure_matches
set
  tier = 'watch_only',
  matched_fields_json = coalesce(matched_fields_json, '{}'::jsonb) || '{"direct_recall_notice_required": true}'::jsonb,
  missing_fields_json = '["direct recall notice", "supplier lot confirmation"]'::jsonb,
  explanation = 'A supplier connection appears in the source, but product or lot exposure is not confirmed.',
  recommended_action = 'Monitor for product, UPC, lot, or supplier confirmation.'
from recall_signals
join external_sources on external_sources.id = recall_signals.source_id
where exposure_matches.recall_signal_id = recall_signals.id
  and external_sources.source_type = 'external_signal'
  and exposure_matches.tier in ('confirmed_match', 'supplier_review')
  and external_sources.canonical_url not ilike '%fda.gov/safety/recalls-market-withdrawals-safety-alerts/%'
  and external_sources.canonical_url not ilike '%fsis.usda.gov/recalls-alerts/%';
