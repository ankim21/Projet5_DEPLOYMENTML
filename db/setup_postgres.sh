#!/usr/bin/env bash
# Prépare PostgreSQL en local (Ubuntu / WSL) : installation, démarrage, utilisateur.
# L'utilisateur et le mot de passe sont lus dans DATABASE_URL (.env) : une seule source de vérité.
#
# Usage (depuis la racine du projet) : bash db/setup_postgres.sh
#
# Serveur deja genere ailleurs (Docker, autre port...) : fournir la commande psql admin, ex.
#   PSQL_ADMIN="psql -h localhost -p 5433 -U postgres" bash db/setup_postgres.sh
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ] && [ -z "${DATABASE_URL:-}" ]; then
    echo "Fichier .env absent : cp .env.example .env puis choisir un mot de passe" >&2
    exit 1
fi

# user / mot de passe extraits de DATABASE_URL (décodage %xx compris), quotés pour le shell
# (affectation séparée de eval : sinon set -e ne détecte pas un échec du python)
identifiants="$(venv/bin/python - <<'EOF'
import os, shlex
from dotenv import load_dotenv
from sqlalchemy.engine import make_url
load_dotenv(".env")  # chemin explicite : find_dotenv() échoue quand le code arrive par stdin
url = make_url(os.environ["DATABASE_URL"])
print(f"DB_USER={shlex.quote(url.username)}")
print(f"DB_PASSWORD={shlex.quote(url.password or '')}")
EOF
)"
eval "$identifiants"

if [ -z "$DB_PASSWORD" ] || [ "$DB_PASSWORD" = "changeme" ]; then
    echo "Choisir un vrai mot de passe dans DATABASE_URL (.env)" >&2
    exit 1
fi

if [ -z "${PSQL_ADMIN:-}" ]; then
    if ! command -v psql >/dev/null; then
        echo "==> Installation de PostgreSQL"
        sudo apt update
        sudo apt install -y postgresql
    fi
    # WSL ne démarre pas toujours les services : à relancer après un redémarrage
    echo "==> Démarrage du service"
    sudo service postgresql start
    PSQL_ADMIN="sudo -u postgres psql"
fi

echo "==> Utilisateur PostgreSQL '$DB_USER'"
# \gexec exécute la requête générée ; %I / %L quotent nom et mot de passe sans injection SQL
# shellcheck disable=SC2086
$PSQL_ADMIN -X -q -v ON_ERROR_STOP=1 -v user="$DB_USER" -v pw="$DB_PASSWORD" <<'SQL'
SELECT format('CREATE ROLE %I LOGIN CREATEDB PASSWORD %L', :'user', :'pw')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'user') \gexec
-- rôle déjà présent : on aligne son mot de passe sur .env
SELECT format('ALTER ROLE %I PASSWORD %L', :'user', :'pw') \gexec
SQL

echo "==> Prêt. Étapes suivantes :"
echo "    venv/bin/python -m db.create_db"
echo "    venv/bin/python -m db.import_csv"
echo "    psql \"\$(grep ^DATABASE_URL .env | cut -d= -f2- | sed 's/+psycopg//')\" -f db/verify.sql"
