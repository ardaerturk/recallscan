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
