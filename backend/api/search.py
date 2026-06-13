from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.db import get_db
from core.logging import logger
from services.search import SearchService

router = APIRouter()

@router.get("/search", tags=["Search"])
async def search(
    q: str = Query(..., description="Query string for semantic search"),
    modality: Optional[str] = Query(None, description="Optional modality filter: TEXT, AUDIO, VIDEO"),
    limit: int = Query(20, description="Max number of candidate chunks to retrieve initially"),
    threshold: float = Query(0.0, description="Minimum quality score threshold (0.0 to 1.0)"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Search endpoint performing semantic cross-modal similarity search.
    """
    logger.info(f"API search request received: q='{q}', modality={modality}, limit={limit}, threshold={threshold}")
    
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' cannot be empty or whitespace.")

    try:
        search_service = SearchService(db)
        results = await search_service.execute_search(
            query=q,
            limit=limit,
            modality=modality,
            quality_threshold=threshold
        )
        return results
    except Exception as e:
        logger.error(f"Error executing semantic search endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search service error: {str(e)}")
