import os
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-key-for-testing")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("CORS_ORIGINS", '["http://localhost:3000"]')