# chatbot_module — FleetIQ Text-to-SQL AI Chatbot
# Modular structure:
#   prompts.py        → All LLM prompts (edit here to tune AI behavior)
#   llm_service.py    → Groq API calls (swap LLM provider here)
#   schema_service.py → JSON schema loading + keyword-based table selector
#   db_executor.py    → SQL Server (pyodbc) query execution + result serialization
#   pipeline.py       → End-to-end orchestration of all stages
#   routes.py         → FastAPI endpoints exposed to frontend
