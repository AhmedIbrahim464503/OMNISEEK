import asyncio
from core.db import AsyncSessionLocal
from core.logging import setup_logging, logger
from models.asset import ModalityEnum
from services.database import DatabaseService

async def test_flow() -> None:
    """Execute mock insertion and similarity query verification checks."""
    setup_logging()
    logger.info("Initializing Phase 2 DB verification check...")
    
    async with AsyncSessionLocal() as session:
        db_service = DatabaseService(session)
        
        # 1. Create a sample Asset
        logger.info("Inserting mock media asset...")
        asset = await db_service.create_asset(
            filename="sample_presentation.mp4",
            file_path="/uploads/sample_presentation.mp4",
            modality=ModalityEnum.VIDEO
        )
        logger.info(f"Asset created successfully: ID={asset.id}")
        
        # 2. Prepare mock 512-dimension vector embeddings
        emb1 = [0.1] * 512
        emb2 = [0.9] * 512
        
        # Assemble chunk records
        logger.info("Bulk inserting mock asset chunks...")
        chunks_data = [
            {
                "asset_id": asset.id,
                "chunk_index": 0,
                "content": "Welcome to the OMNISEEK introduction. Today we discuss AI vectors.",
                "start_time": 0.0,
                "end_time": 12.5,
                "metadata": {"speaker": "Alice"},
                "embedding": emb1
            },
            {
                "asset_id": asset.id,
                "chunk_index": 1,
                "content": "Temporal indexing is highly critical for video timestamps search.",
                "start_time": 12.5,
                "end_time": 25.0,
                "metadata": {"speaker": "Bob"},
                "embedding": emb2
            }
        ]
        
        inserted_chunks = await db_service.add_asset_chunks(chunks_data)
        logger.info(f"Successfully inserted {len(inserted_chunks)} chunks.")
        
        # 3. Execute similarity search close to the first embedding
        query_vector = [0.12] * 512
        logger.info("Running cosine similarity nearest-neighbor search...")
        search_results = await db_service.search_similar_chunks(query_vector, limit=2)
        
        logger.info("Similarity Search Results:")
        for idx, result in enumerate(search_results):
            logger.info(
                f"[{idx+1}] Score: {result['similarity_score']:.6f} | "
                f"Asset: {result['asset_name']} | "
                f"Time: {result['start_time']}s - {result['end_time']}s | "
                f"Content: {result['chunk_content']}"
            )
            
        assert len(search_results) > 0, "Zero query records retrieved!"
        assert search_results[0]["asset_name"] == "sample_presentation.mp4", "Asset relationship join broken!"
        assert "OMNISEEK" in search_results[0]["chunk_content"], "Unexpected first-match chunk contents!"
        logger.info("Phase 2 schema and vector search verification checks passed!")

if __name__ == "__main__":
    asyncio.run(test_flow())
