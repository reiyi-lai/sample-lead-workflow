alter table public.events
add constraint events_normalized_event_url_key unique (normalized_event_url);
