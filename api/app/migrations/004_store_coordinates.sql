alter table stores add column if not exists latitude double precision;
alter table stores add column if not exists longitude double precision;

update stores set latitude = 37.7516, longitude = -122.4350 where id = 'store_sf';
update stores set latitude = 37.8044, longitude = -122.2712 where id = 'store_oak';
update stores set latitude = 40.7081, longitude = -73.9571 where id = 'store_bk';
update stores set latitude = 40.7178, longitude = -74.0431 where id = 'store_jer';
update stores set latitude = 33.7838, longitude = -84.3839 where id = 'store_atl';
update stores set latitude = 39.9788, longitude = -83.0030 where id = 'store_col';
update stores set latitude = 32.8218, longitude = -96.7877 where id = 'store_dal';
update stores set latitude = 41.9105, longitude = -87.6776 where id = 'store_chi';
