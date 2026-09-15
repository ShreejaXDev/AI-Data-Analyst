import uuid
import time
from typing import Dict, Optional, List
import pandas as pd


class DatasetSession:
    def __init__(self, dataset_id: str, filename: str, df: pd.DataFrame):
        self.dataset_id: str = dataset_id
        self.filename: str = filename
        self.original_df: pd.DataFrame = df.copy()
        self.active_df: pd.DataFrame = df.copy()
        self.conversation_history: List[Dict[str, str]] = []
        self.created_at: float = time.time()


class SessionStore:
    def __init__(self):
        self._sessions: Dict[str, DatasetSession] = {}

    def create_session(self, filename: str, df: pd.DataFrame) -> DatasetSession:
        dataset_id = str(uuid.uuid4())
        session = DatasetSession(dataset_id=dataset_id, filename=filename, df=df)
        self._sessions[dataset_id] = session
        return session

    def get_session(self, dataset_id: str) -> Optional[DatasetSession]:
        return self._sessions.get(dataset_id)

    def update_session(
        self,
        dataset_id: str,
        active_df: pd.DataFrame,
        conversation_history: List[Dict[str, str]]
    ) -> bool:
        session = self.get_session(dataset_id)
        if not session:
            return False
        session.active_df = active_df.copy()
        session.conversation_history = list(conversation_history)
        return True

    def clear_all(self):
        self._sessions.clear()


# Global singleton session store
session_store = SessionStore()
