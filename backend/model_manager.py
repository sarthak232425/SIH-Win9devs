from sentence_transformers import SentenceTransformer

class ModelManager:
    _instance = None
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            print("🔄 Loading LaBSE model (shared instance)...")
            cls._model = SentenceTransformer('sentence-transformers/LaBSE')
            print("✅ Model loaded successfully")
        return cls._model