from fastapi import FastAPI

from .api.routes import router

app = FastAPI(title="IF3170 Truck Search")
app.include_router(router)
