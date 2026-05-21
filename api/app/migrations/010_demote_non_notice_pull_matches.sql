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
