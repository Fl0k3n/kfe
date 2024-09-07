
from enum import Enum

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class FileType(str, Enum):
    IMAGE = 'image' # TODO: screenshot
    VIDEO = 'video'
    AUDIO = 'audio'
    OTHER = 'other'


class FileMetadata(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    added_at = Column(DateTime)
    description = Column(Text)
    

    # image | screenshot | video | audio
    ftype = Column(String) 

    # for audio or video files
    transcript = Column(Text, nullable=True)

    # for screenshot
    ocr_text = Column(Text, nullable=True)


    @property
    def file_type(self) -> FileType:
        return FileType(self.ftype)
