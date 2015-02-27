#!/bin/bash

echo $PWD
PGPASSWORD=datadog embedded/pg_REL9_4_0/bin/psql -h localhost -p 15433 -U datadog -w -c "SELECT * FROM persons" datadog_test
