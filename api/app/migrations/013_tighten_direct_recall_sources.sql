update external_sources
set source_type = 'external_signal'
where source_type = 'direct_recall_notice'
  and (
    title ~* '(what to check|how to check|what to know|what you should know|here''?s what|list of|roundup|study|investigation|mmwr|linked to|tied to|brand-by-brand|fallout|cascade|sparks|recalled over|recalled after|fda warns|fda recalls|cdc|recall alert|popular|sold locally)'
    or title ~* '^company[[:space:]]+issues?'
    or title !~* '((issues?|announces?|initiates?|expands?)[[:space:]]+(a[[:space:]]+)?(voluntary[[:space:]]+)?recall|voluntarily[[:space:]]+recalls?|recalls?[[:space:]].*(because of possible health risk|due to possible health risk|because of possible|due to possible|undeclared|allergy alert))'
  );

update exposure_matches
set
  tier = 'watch_only',
  match_type = 'product_mention',
  matched_fields_json = matched_fields_json || '{"direct_recall_notice_required": true}'::jsonb,
  missing_fields_json = '["direct recall notice"]'::jsonb,
  explanation = 'The product is mentioned, but the source is not a direct recall notice or safety alert.',
  recommended_action = 'Monitor. Do not pull product until product, UPC, lot, or supplier exposure is confirmed.'
from recall_signals
join external_sources on external_sources.id = recall_signals.source_id
where exposure_matches.recall_signal_id = recall_signals.id
  and exposure_matches.tier = 'confirmed_match'
  and external_sources.source_type not in ('official_recall', 'public_health_alert', 'direct_recall_notice');
