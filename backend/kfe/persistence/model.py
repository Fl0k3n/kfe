
from enum import Enum
from pathlib import Path

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class FileType(str, Enum):
    IMAGE = 'image'
    VIDEO = 'video'
    AUDIO = 'audio'
    OTHER = 'other'


class FileMetadata(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)
    added_at = Column(DateTime)
    description = Column(Text)

    # image | video | audio
    ftype = Column(String) 

    # for audio or video files
    is_transcript_analyzed = Column(Boolean, default=False)
    transcript = Column(Text, nullable=True)
    is_transcript_fixed = Column(Boolean, default=False)

    # for image
    is_ocr_analyzed = Column(Boolean, default=False)
    is_screenshot = Column(Boolean, default=False)
    ocr_text = Column(Text, nullable=True)

    embedding_generation_failed = Column(Boolean, default=False)

    lemmatized_description = Column(Text, nullable=True)
    lemmatized_ocr_text    = Column(Text, nullable=True)
    lemmatized_transcript  = Column(Text, nullable=True)

    @property
    def file_type(self) -> FileType:
        return FileType(self.ftype)


class RegisteredDirectory(Base):
    __tablename__ = 'directories'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    fs_path = Column(String, unique=True)
    primary_language = Column(String)

    @property
    def path(self) -> Path:
        return Path(self.fs_path)
