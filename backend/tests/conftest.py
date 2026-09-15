import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/voice_cloning_detection_test",
)
