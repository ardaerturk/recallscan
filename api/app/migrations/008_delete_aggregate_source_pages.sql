delete from exposure_matches
where recall_signal_id in (
  select recall_signals.id
  from recall_signals
  join external_sources on external_sources.id = recall_signals.source_id
  where external_sources.canonical_url in (
    'https://fda.gov/food/recalls-outbreaks-emergencies/alerts-advisories-safety-information',
    'https://fda.gov/food/recalls-outbreaks-emergencies/recalls-foods-dietary-supplements',
    'https://fda.gov/safety/recalls-market-withdrawals-safety-alerts',
    'https://www.fda.gov/food/recalls-outbreaks-emergencies/alerts-advisories-safety-information',
    'https://www.fda.gov/food/recalls-outbreaks-emergencies/recalls-foods-dietary-supplements',
    'https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts',
    'https://foodsafety.gov/recalls-and-outbreaks',
    'https://www.foodsafety.gov/recalls-and-outbreaks',
    'https://fsis.usda.gov/recalls-alerts',
    'https://www.fsis.usda.gov/recalls-alerts'
  )
);

delete from recall_signals
using external_sources
where external_sources.id = recall_signals.source_id
  and external_sources.canonical_url in (
    'https://fda.gov/food/recalls-outbreaks-emergencies/alerts-advisories-safety-information',
    'https://fda.gov/food/recalls-outbreaks-emergencies/recalls-foods-dietary-supplements',
    'https://fda.gov/safety/recalls-market-withdrawals-safety-alerts',
    'https://www.fda.gov/food/recalls-outbreaks-emergencies/alerts-advisories-safety-information',
    'https://www.fda.gov/food/recalls-outbreaks-emergencies/recalls-foods-dietary-supplements',
    'https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts',
    'https://foodsafety.gov/recalls-and-outbreaks',
    'https://www.foodsafety.gov/recalls-and-outbreaks',
    'https://fsis.usda.gov/recalls-alerts',
    'https://www.fsis.usda.gov/recalls-alerts'
  );

delete from external_sources
where canonical_url in (
  'https://fda.gov/food/recalls-outbreaks-emergencies/alerts-advisories-safety-information',
  'https://fda.gov/food/recalls-outbreaks-emergencies/recalls-foods-dietary-supplements',
  'https://fda.gov/safety/recalls-market-withdrawals-safety-alerts',
  'https://www.fda.gov/food/recalls-outbreaks-emergencies/alerts-advisories-safety-information',
  'https://www.fda.gov/food/recalls-outbreaks-emergencies/recalls-foods-dietary-supplements',
  'https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts',
  'https://foodsafety.gov/recalls-and-outbreaks',
  'https://www.foodsafety.gov/recalls-and-outbreaks',
  'https://fsis.usda.gov/recalls-alerts',
  'https://www.fsis.usda.gov/recalls-alerts'
);
