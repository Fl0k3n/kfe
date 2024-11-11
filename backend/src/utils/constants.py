from typing import Literal

PRELOAD_THUMBNAILS_ENV = 'PRELOAD_THUMBNAILS'
GENERATE_OPENAPI_SCHEMA_ON_STARTUP_ENV = 'GENERATE_OPENAPI_SCHEMA_ON_STARTUP'
LOG_SQL_ENV = 'LOG_SQL'
DEVICE_ENV = 'DEVICE'

DIRECTORY_NAME_HEADER = 'X-Directory'

Language = Literal['pl', 'en']
SUPPORTED_LANGUAGES: list[Language] = ['pl', 'en']
