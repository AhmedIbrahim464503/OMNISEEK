import threading
from typing import Any, Optional
from core.logging import logger

class AIModelManager:
    """Thread-safe singleton model loader ensuring AI models are cached once in memory."""

    _instance: Optional["AIModelManager"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, *args, **kwargs) -> "AIModelManager":
        """Verify and fetch singleton instance with locking block."""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(AIModelManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        """Initialize private model slots and loading locks."""
        if not hasattr(self, "_initialized"):
            self._clip_model: Any = None
            self._clip_processor: Any = None
            self._whisper_model: Any = None
            self._bge_m3_model: Any = None
            self._reranker_model: Any = None
            self._load_lock = threading.Lock()
            self._initialized = True

    def load_clip(self) -> None:
        """Load CLIP ViT-B/32 model and preprocessors for frame embedding extraction."""
        if self._clip_model is not None:
            return
            
        with self._load_lock:
            if self._clip_model is not None:
                return
            try:
                from transformers import CLIPModel, CLIPProcessor
                logger.info("Loading CLIP base patch32 model and processor...")
                self._clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
                self._clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
                logger.info("CLIP model loaded successfully.")
            except Exception as err:
                logger.error(f"CLIP model initialization failed: {str(err)}")
                raise

    def load_whisper(self) -> None:
        """Load Faster-Whisper audio transcriber on CPU memory."""
        if self._whisper_model is not None:
            return
            
        with self._load_lock:
            if self._whisper_model is not None:
                return
            try:
                from faster_whisper import WhisperModel
                logger.info("Loading Faster-Whisper tiny model on CPU...")
                # Utilizing tiny for lightweight CPU verification runs
                self._whisper_model = WhisperModel("tiny", device="cpu", compute_type="float32")
                logger.info("Faster-Whisper loaded successfully.")
            except Exception as err:
                logger.error(f"Whisper initialization failed: {str(err)}")
                raise

    def load_bge_m3(self) -> None:
        """Load BAAI/bge-m3 sentence transformer model on CPU memory."""
        if self._bge_m3_model is not None:
            return
            
        with self._load_lock:
            if self._bge_m3_model is not None:
                return
            try:
                from sentence_transformers import SentenceTransformer
                logger.info("Loading BAAI/bge-m3 sentence transformer...")
                self._bge_m3_model = SentenceTransformer("BAAI/bge-m3", device="cpu")
                logger.info("BGE-M3 loaded successfully.")
            except Exception as err:
                logger.error(f"BGE-M3 initialization failed: {str(err)}")
                raise

    @property
    def clip_model(self) -> Any:
        """Fetch CLIP model instance, loading it on demand if absent."""
        self.load_clip()
        return self._clip_model

    @property
    def clip_processor(self) -> Any:
        """Fetch CLIP processor instance, loading it on demand if absent."""
        self.load_clip()
        return self._clip_processor

    @property
    def whisper_model(self) -> Any:
        """Fetch Whisper transcriber instance, loading it on demand if absent."""
        self.load_whisper()
        return self._whisper_model

    @property
    def bge_m3_model(self) -> Any:
        """Fetch BGE-M3 sentence transformer instance, loading it on demand if absent."""
        self.load_bge_m3()
        return self._bge_m3_model

    def load_reranker(self) -> None:
        """Load BAAI/bge-reranker-base cross-encoder for semantic score refinement."""
        if self._reranker_model is not None:
            return
            
        with self._load_lock:
            if self._reranker_model is not None:
                return
            try:
                from sentence_transformers import CrossEncoder
                logger.info("Loading BAAI/bge-reranker-base cross-encoder...")
                self._reranker_model = CrossEncoder("BAAI/bge-reranker-base", device="cpu")
                logger.info("Reranker model loaded successfully.")
            except Exception as err:
                logger.error(f"Reranker model initialization failed: {str(err)}")
                raise

    @property
    def reranker_model(self) -> Any:
        """Fetch Cross-Encoder reranker instance, loading it on demand if absent."""
        self.load_reranker()
        return self._reranker_model
