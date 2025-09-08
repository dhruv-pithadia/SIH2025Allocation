from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.health import router as health_router
from app.routers.students import router as students_router
from app.routers.runs import router as runs_router
from app.routers.downloads import router as downloads_router
from app.routers.internships import router as internships_router


app = FastAPI(title="PM Internship Allocation API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(students_router)
app.include_router(runs_router)
app.include_router(downloads_router)
app.include_router(internships_router)