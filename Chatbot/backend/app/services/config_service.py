import json
import logging
from pathlib import Path

from app.config import Settings
from app.core.prompts import build_system_prompt
from app.models.schemas import PromptConfigOut, PromptConfigUpdate

logger = logging.getLogger(__name__)

CONFIG_FILE = "prompt_config.json"


class ConfigService:
    """Runtime prompt/branding overrides persisted to data/prompt_config.json."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._path = settings.data_path / CONFIG_FILE

    def _load_overrides(self) -> dict:
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.warning("Invalid prompt_config.json, ignoring")
            return {}

    def _save_overrides(self, data: dict) -> None:
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_effective(self) -> dict:
        overrides = self._load_overrides()
        return {
            "brand_name": overrides.get("brand_name", self.settings.brand_name),
            "company_description": overrides.get(
                "company_description", self.settings.company_description
            ),
            "system_prompt_tone": overrides.get(
                "system_prompt_tone", self.settings.system_prompt_tone
            ),
            "custom_system_prompt": overrides.get(
                "custom_system_prompt", self.settings.custom_system_prompt
            ),
        }

    def get_system_prompt(self) -> str:
        cfg = self.get_effective()
        return build_system_prompt(
            brand_name=cfg["brand_name"],
            company_description=cfg["company_description"],
            tone=cfg["system_prompt_tone"],
            custom_prompt=cfg["custom_system_prompt"],
        )

    def get_prompt_config(self) -> PromptConfigOut:
        cfg = self.get_effective()
        prompt = build_system_prompt(
            brand_name=cfg["brand_name"],
            company_description=cfg["company_description"],
            tone=cfg["system_prompt_tone"],
            custom_prompt=cfg["custom_system_prompt"],
        )
        preview = prompt[:500] + ("..." if len(prompt) > 500 else "")
        return PromptConfigOut(
            brand_name=cfg["brand_name"],
            company_description=cfg["company_description"],
            system_prompt_tone=cfg["system_prompt_tone"],
            custom_system_prompt=cfg["custom_system_prompt"],
            effective_prompt_preview=preview,
        )

    def update_prompt_config(self, update: PromptConfigUpdate) -> PromptConfigOut:
        current = self._load_overrides()
        data = update.model_dump(exclude_none=True)
        current.update(data)
        self._save_overrides(current)
        logger.info("Updated prompt config keys=%s", list(data.keys()))
        return self.get_prompt_config()
