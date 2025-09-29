from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, devices, resources, reservations

app = FastAPI(
    title="IoT Management System",
    description="Sistema de Gestao de Recursos Compartilhados com IoT",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://frontend"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, tags=["authentication"])
app.include_router(devices.router, tags=["devices"])
app.include_router(resources.router, tags=["resources"])
app.include_router(reservations.router, tags=["reservations"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "IoT Management System API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "API is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
