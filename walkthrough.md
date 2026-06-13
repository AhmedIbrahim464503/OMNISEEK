# Phase 4 Walkthrough: AI Model Integration Layer & Embedding Generation Pipeline

This document outlines the AI model integrations, singleton manager, text/audio/video processing pipelines, database vector modifications, and testing instructions implemented in Phase 4.

---

## 1. Updated Folder Structure

The backend workspace is structured as follows:

```
OMNISEEK/
├── backend/
│   ├── api/
│   │   ├── router.py
│   │   └── upload.py         <-- [MODIFY] Connected ProcessingOrchestrator trigger
│   ├── core/
│   │   ├── celery.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── exceptions.py
│   │   ├── init_schema.py
│   │   └── logging.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── asset.py
│   │   ├── base.py
│   │   └── chunk.py
│   ├── repositories/
│   │   ├── asset.py
│   │   ├── base.py
│   │   └── chunk.py
│   ├── schemas/
│   │   └── base.py
│   ├── services/
│   │   ├── ai_model_manager.py <-- [NEW] Singleton model manager
│   │   ├── audio_embedding.py  <-- [NEW] Whisper + BGE-M3 audio pipeline
│   │   ├── base.py
│   │   ├── chunking.py
│   │   ├── database.py
│   │   ├── embedding.py        <-- [NEW] Core embedding logic
│   │   ├── ingestion.py
│   │   ├── media_processor.py
│   │   ├── processing_orchestrator.py <-- [NEW] Connects Phase 3 to Phase 4
│   │   ├── text_embedding.py   <-- [NEW] BGE-M3 text pipeline (512-dim slice)
│   │   ├── upload.py
│   │   └── video_embedding.py  <-- [NEW] CLIP frame + audio pipeline
│   ├── workers/
│   │   └── worker.py
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt     <-- [MODIFY] Added torch, transformers, and whisper
├── docs/
│   ├── api_reference.md
│   ├── architecture.md
│   ├── chunking_strategy.md
│   ├── database_schema.md
│   ├── deployment_guide.md
│   ├── future_ai_pipeline.md
│   ├── ingestion_pipeline.md
│   ├── media_processing.md
│   └── troubleshooting.md
├── frontend/
│   └── README.md
├── .env
├── .env.example
├── docker-compose.yml
├── development_history.md
├── agent_behavior_guidelines.md
├── implementation_plan.md
└── task.md
```

---

## 2. Implemented Code Files

### [ai_model_manager.py](file:///d:/projects/sps_project/backend/services/ai_model_manager.py)
Singleton manager ensuring AI models are cached once in memory.
```python
import threading
from typing import Any, Optional
from core.logging import logger

class AIModelManager:
    _instance: Optional["AIModelManager"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, *args, **kwargs) -> "AIModelManager":
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(AIModelManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, "_initialized"):
            self._clip_model: Any = None
            self._clip_processor: Any = None
            self._whisper_model: Any = None
            self._bge_m3_model: Any = None
            self._load_lock = threading.Lock()
            self._initialized = True

    def load_clip(self) -> None:
        if self._clip_model is not None: return
        with self._load_lock:
            if self._clip_model is not None: return
            from transformers import CLIPModel, CLIPProcessor
            self._clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self._clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    def load_whisper(self) -> None:
        if self._whisper_model is not None: return
        with self._load_lock:
            if self._whisper_model is not None: return
            from faster_whisper import WhisperModel
            self._whisper_model = WhisperModel("tiny", device="cpu", compute_type="float32")

    def load_bge_m3(self) -> None:
        if self._bge_m3_model is not None: return
        with self._load_lock:
            if self._bge_m3_model is not None: return
            from sentence_transformers import SentenceTransformer
            self._bge_m3_model = SentenceTransformer("BAAI/bge-m3", device="cpu")

    @property
    def clip_model(self) -> Any:
        self.load_clip()
        return self._clip_model

    @property
    def clip_processor(self) -> Any:
        self.load_clip()
        return self._clip_processor

    @property
    def whisper_model(self) -> Any:
        self.load_whisper()
        return self._whisper_model

    @property
    def bge_m3_model(self) -> Any:
        self.load_bge_m3()
        return self._bge_m3_model
```

### [text_embedding.py](file:///d:/projects/sps_project/backend/services/text_embedding.py)
Encodes text using BGE-M3, truncates to 512 dimensions, and L2 normalizes.
```python
import numpy as np
from typing import List
from services.ai_model_manager import AIModelManager

class TextEmbeddingService:
    @staticmethod
    def embed_text(text: str) -> List[float]:
        if not text: return [0.0] * 512
        model_manager = AIModelManager()
        model = model_manager.bge_m3_model
        embedding_1024 = model.encode(text, convert_to_numpy=True)
        embedding_512 = embedding_1024[:512]
        norm = np.linalg.norm(embedding_512)
        if norm > 0:
            embedding_512 = embedding_512 / norm
        return embedding_512.tolist()
```

### [audio_embedding.py](file:///d:/projects/sps_project/backend/services/audio_embedding.py)
Transcribes audio locally using Whisper and embeds segments using BGE-M3.
```python
import os
from typing import Any, Dict, List
from services.ai_model_manager import AIModelManager
from services.text_embedding import TextEmbeddingService
from core.exceptions import ValidationError

class AudioEmbeddingService:
    @staticmethod
    def process_audio(audio_path: str) -> List[Dict[str, Any]]:
        if not os.path.exists(audio_path):
            raise ValidationError(f"Audio file not found: {audio_path}")
        model_manager = AIModelManager()
        whisper = model_manager.whisper_model
        segments, info = whisper.transcribe(audio_path, beam_size=5)
        segment_list = list(segments)
        
        results = []
        for idx, segment in enumerate(segment_list):
            segment_text = segment.text.strip()
            if not segment_text: continue
            embedding = TextEmbeddingService.embed_text(segment_text)
            results.append({
                "chunk_index": idx,
                "content": segment_text,
                "start_time": float(segment.start),
                "end_time": float(segment.end),
                "embedding": embedding,
                "metadata": {"avg_logprob": float(segment.avg_logprob)}
            })
        return results
```

### [video_embedding.py](file:///d:/projects/sps_project/backend/services/video_embedding.py)
Embeds frames using CLIP and transcribes audio tracks.
```python
import os
import numpy as np
import torch
from PIL import Image
from typing import Any, Dict, List
from services.ai_model_manager import AIModelManager
from services.audio_embedding import AudioEmbeddingService

class VideoEmbeddingService:
    @staticmethod
    def embed_frame(image_path: str) -> List[float]:
        if not os.path.exists(image_path): return [0.0] * 512
        model_manager = AIModelManager()
        model = model_manager.clip_model
        processor = model_manager.clip_processor
        try:
            image = Image.open(image_path).convert("RGB")
            inputs = processor(images=image, return_tensors="pt")
            with torch.no_grad():
                features = model.get_image_features(**inputs)
            embedding_np = features[0].cpu().numpy()
            norm = np.linalg.norm(embedding_np)
            if norm > 0:
                embedding_np = embedding_np / norm
            return embedding_np.tolist()
        except Exception:
            return [0.0] * 512

    @staticmethod
    def process_video_audio(audio_path: str) -> List[Dict[str, Any]]:
        return AudioEmbeddingService.process_audio(audio_path)
```

### [processing_orchestrator.py](file:///d:/projects/sps_project/backend/services/processing_orchestrator.py)
Updates DB chunk records in batches of 50 using transaction boundary commits.
```python
import os
import uuid
from typing import Any, Dict, List
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.exceptions import DatabaseError
from models.asset import Asset, ModalityEnum
from models.chunk import AssetChunk
from services.audio_embedding import AudioEmbeddingService
from services.embedding import EmbeddingService

class ProcessingOrchestrator:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def process_asset_embeddings(self, asset_id: uuid.UUID) -> int:
        stmt = select(Asset).filter(Asset.id == asset_id)
        result = await self.db.execute(stmt)
        asset = result.scalars().first()
        if not asset: return 0
        
        chunks_stmt = select(AssetChunk).filter(AssetChunk.asset_id == asset_id, AssetChunk.embedding == None)
        chunks_result = await self.db.execute(chunks_stmt)
        raw_chunks = chunks_result.scalars().all()
        
        chunks_updated = 0
        try:
            if asset.modality == ModalityEnum.TEXT:
                batch = [{"id": chunk.id, "embedding": EmbeddingService.embed_text(chunk.content)} for chunk in raw_chunks]
                if batch:
                    await self._bulk_update_embeddings(batch)
                    chunks_updated += len(batch)
                    
            elif asset.modality == ModalityEnum.AUDIO:
                real_chunks = AudioEmbeddingService.process_audio(asset.file_path)
                await self.db.execute(delete(AssetChunk).filter(AssetChunk.asset_id == asset_id))
                for chunk in real_chunks: chunk["asset_id"] = asset_id
                from services.database import DatabaseService
                await DatabaseService(self.db).add_asset_chunks(real_chunks)
                chunks_updated += len(real_chunks)
                
            elif asset.modality == ModalityEnum.VIDEO:
                visual_batch = []
                for chunk in raw_chunks:
                    frames = chunk.metadata.get("frames", [])
                    if not frames: continue
                    vector = EmbeddingService.embed_image(frames[0]["frame_path"])
                    visual_batch.append({"id": chunk.id, "embedding": vector})
                if visual_batch:
                    await self._bulk_update_embeddings(visual_batch)
                    chunks_updated += len(visual_batch)
                    
                filename = os.path.basename(asset.file_path)
                base_name, _ = os.path.splitext(filename)
                audio_path = os.path.join(settings.STORAGE_DIR, "assets", str(asset_id), "audio", f"{base_name}_audio.mp3")
                if os.path.exists(audio_path):
                    audio_chunks = AudioEmbeddingService.process_audio(audio_path)
                    for idx, chunk in enumerate(audio_chunks):
                        chunk["asset_id"] = asset_id
                        chunk["chunk_index"] = len(raw_chunks) + idx
                    from services.database import DatabaseService
                    await DatabaseService(self.db).add_asset_chunks(audio_chunks)
                    chunks_updated += len(audio_chunks)
                    
            await self.db.commit()
            return chunks_updated
        except Exception as err:
            await self.db.rollback()
            raise DatabaseError(f"Embedding pipeline execution failed: {str(err)}")

    async def _bulk_update_embeddings(self, batch: List[Dict[str, Any]], batch_size: int = 50) -> None:
        for i in range(0, len(batch), batch_size):
            for record in batch[i:i+batch_size]:
                await self.db.execute(update(AssetChunk).filter(AssetChunk.id == record["id"]).values(embedding=record["embedding"]))
```

---

## 3. Setup & Model Downloads

To deploy the deep learning stack:
1. Re-build and run the container network:
   ```bash
   docker-compose up --build -d
   ```
2. The PyTorch, Transformers, and sentence-transformers libraries will be installed automatically from `requirements.txt`. Models (`BAAI/bge-m3`, `openai/clip-vit-base-patch32`, and Whisper `tiny`) are downloaded programmatically on CPU upon their first invocation and cached in the local cache directories of the runner container.

---

## 4. Ingestion & Embedding Testing

1. Test the complete flow (Phase 3 upload + Phase 4 embedding generation) using a curl document upload:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/upload" -F "file=@sample.txt"
   ```
2. Verify that the response returns the count of processed text chunks.
3. Access the PostgreSQL container and check that the vector embeddings length matches 512 dimensions exactly:
   ```sql
   SELECT id, chunk_index, array_length(embedding, 1) FROM asset_chunks WHERE embedding IS NOT NULL;
   ```
