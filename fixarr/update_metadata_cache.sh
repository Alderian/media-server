#!/bin/bash
# Simply delete the cache to force a refresh on next run
rm -f metadata_cache.json
echo "Metadata cache cleared. It will be rebuilt on the next run."
