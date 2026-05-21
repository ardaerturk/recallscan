delete from exposure_matches
where recall_signal_id in (
  select recall_signals.id
  from recall_signals
  join external_sources on external_sources.id = recall_signals.source_id
  where external_sources.canonical_url in (
    'https://fda.gov/safety/recalls-market-withdrawals-safety-alerts/major-product-recalls',
    'https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts/major-product-recalls'
  )
);

delete from recall_signals
using external_sources
where external_sources.id = recall_signals.source_id
  and external_sources.canonical_url in (
    'https://fda.gov/safety/recalls-market-withdrawals-safety-alerts/major-product-recalls',
    'https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts/major-product-recalls'
  );

delete from external_sources
where canonical_url in (
  'https://fda.gov/safety/recalls-market-withdrawals-safety-alerts/major-product-recalls',
  'https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts/major-product-recalls'
);
