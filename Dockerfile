FROM python:3.11-slim

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /home/user/app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
## -----
## vraiment essayer technical
## actions - partie ou on voit que ca se deploie aussi 
## --> in github to hugging face =-- think of it like ssh key for github 
## cd is cd when ci is OK 
## README - 
## voir si je trouve un fichier pour monter architecture 