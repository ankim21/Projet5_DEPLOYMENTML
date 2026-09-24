# the address of the cabinet and the key to open it. It only knows where the database is and how to reach it, nothing about tables.

#Session: one "unit of work".  add or change rows, then either commit() to save everything or rollback() to cancel everything.

# If DATABASE_URL is missing, it stops straight away with a clear message

## HOW TO CONNECT

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# lit le fichier .env (jamais commit) pour ne pas mettre le mot de passe dans le code
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL manquante : copier .env.example vers .env et la renseigner"
    )

# Engine: the link to PostgreSQL. opens a connection when something actually uses it.
# format : postgresql+psycopg://<utilisateur>:<mot_de_passe>@<hôte>:<port>/<nom_de_la_base>
# the first part is what we calll dialect, so here POSTGRESQL 
# also indicated what DBAPI we are using - third party driver that SQLAlchemy uses to interact with particular database, here psycopg
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


# the thing that talks to DV : factory for Session objects, which is what actually checks out a connection from engine's pool and
# lets run querties
# layer quen otre fastapi utilise/routes via Depdends ? 
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
