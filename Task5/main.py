import typer

from search_db import SearchDB
from pipeline import Pipeline

app = typer.Typer()


@app.command(name="create-index")
def create_index():
    search_db = SearchDB()
    search_db.init()


@app.command(name="search")
def search():
    pipeline = Pipeline()
    pipeline.search()


if __name__ == "__main__":
    app()