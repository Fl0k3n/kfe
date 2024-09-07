from pydantic import BaseModel


class UpdateDescriptionRequest(BaseModel):
    file_id: int
    description: str

class OpenFileRequest(BaseModel):
    file_name: str
