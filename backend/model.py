

from sqlalchemy import Column, DateTime, Integer, String, Text

from db import Base


class File(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    added_at = Column(DateTime)
    description = Column(Text)
    

    # image | screenshot | video | audio
    file_type = Column(String) 

    # for audio or video files
    transcript = Column(Text, nullable=True)

    # for screenshot
    ocr_text = Column(Text, nullable=True)



