#!/bin/sh
. /root/conda/etc/profile.d/conda.sh
conda activate climada_env
exec "$@"
