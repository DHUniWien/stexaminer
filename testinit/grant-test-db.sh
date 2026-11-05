#!/bin/bash
# Run (or sourced) by the mysql image's entrypoint when the database is first
# created. Django's test runner makes its own test_<name> database, so the
# application's database user needs rights on those. Only the test override
# compose file mounts this script.
mysql --protocol=socket -uroot -p"${MYSQL_ROOT_PASSWORD}" <<SQL
GRANT ALL PRIVILEGES ON \`test\\_%\`.* TO '${MYSQL_USER}'@'%';
SQL
