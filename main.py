from fastapi import FastAPI
from routers import lti, usage

app = FastAPI()

app.include_router(lti.router, prefix="/lti")
#app.include_router(usage.router, prefix="/admin")