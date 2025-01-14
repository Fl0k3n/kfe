import asyncio
from dataclasses import dataclass
from typing import Optional

from kfe.utils.constants import Language
from kfe.utils.model_manager import ModelManager, ModelType


@dataclass(frozen=False)
class ModelManagementTasks:
    loader_task: Optional[asyncio.Task] = None
    cleaner_task: Optional[asyncio.Task] = None

class ModelEagerLoader:
    def __init__(self, model_managers: dict[Language, ModelManager], model_types_to_eager_load: list[ModelType], release_delay_seconds=60*30):
        self.model_managers = model_managers
        self.model_types_to_eager_load = model_types_to_eager_load
        self.release_delay_seconds = release_delay_seconds
        self.tasks: dict[Language, ModelManagementTasks] = {lang: ModelManagementTasks() for lang in model_managers}
        self.release_locks: dict[Language, asyncio.Lock] = {lang: asyncio.Lock() for lang in model_managers}
        
    async def ensure_eager_models_loaded_in_background(self, used_languages: set[Language]):
        for language in used_languages:
            async with self.release_locks[language]:
                tasks = self.tasks[language]
                if tasks.loader_task is None:
                    tasks.loader_task = asyncio.create_task(self._require_models_in_background(language))
                elif tasks.cleaner_task is not None:
                    # reset timers
                    tasks.cleaner_task.cancel()
                    tasks.cleaner_task = asyncio.create_task(self._release_models_in_background(language))

    async def _require_models_in_background(self, language: Language):
        model_manager = self.model_managers[language]
        await asyncio.gather(*[model_manager.require_eager(model) for model in self.model_types_to_eager_load])
        self.tasks[language].cleaner_task = asyncio.create_task(self._release_models_in_background(language))

    async def _release_models_in_background(self, language: Language):
        await asyncio.sleep(self.release_delay_seconds)

        # make sure we don't get canceled in the middle
        async with self.release_locks[language]:
            model_manager = self.model_managers[language]
            for model in self.model_types_to_eager_load:
                await model_manager.release_eager(model)
            tasks = self.tasks[language]
            tasks.loader_task = tasks.cleaner_task = None
    
    async def teardown(self):
        for language_tasks in self.tasks.values():
            if language_tasks.loader_task is not None:
                language_tasks.loader_task.cancel()
            if language_tasks.cleaner_task is not None:
                language_tasks.cleaner_task.cancel()
