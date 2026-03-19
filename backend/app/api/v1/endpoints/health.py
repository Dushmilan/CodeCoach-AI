from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.health import HealthResponse, DatabaseStatus

router = APIRouter()

@router.get("/", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Comprehensive health check endpoint."""
    
    # Check database connectivity
    db_status = DatabaseStatus.healthy
    try:
        await db.execute("SELECT 1")
    except Exception as e:
        db_status = DatabaseStatus.unhealthy
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        database=db_status,
    services={
        "supabase": "healthy" # TODO: Add Supabase health check
    }
    )