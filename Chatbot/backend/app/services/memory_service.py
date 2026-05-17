from app.config import Settings
from app.repositories.session_repo import SessionRepository


class MemoryService:
    def __init__(self, repo: SessionRepository, settings: Settings):
        self.repo = repo
        self.settings = settings

    async def load_history(self, session_id: str) -> list[dict[str, str]]:
        messages = await self.repo.get_recent_messages(
            session_id, self.settings.memory_max_turns
        )
        return [{"role": m.role, "content": m.content} for m in messages]

    async def save_turn(
        self, session_id: str, user_message: str, assistant_reply: str
    ) -> None:
        await self.repo.add_message(session_id, "user", user_message)
        await self.repo.add_message(session_id, "assistant", assistant_reply)
