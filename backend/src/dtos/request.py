from pydantic import BaseModel


class UpdateDescriptionRequest(BaseModel):
    file_id: int
    description: str

class UpdateTranscriptRequest(BaseModel):
    file_id: int
    transcript: str

class OpenFileRequest(BaseModel):
    file_id: int

class SearchRequest(BaseModel):
    query: str

class FindSimilarItemsRequest(BaseModel):
    file_id: int

class GetIdxOfFileReqeust(BaseModel):
    file_id: int

class FindSimilarImagesToUploadedImageRequest(BaseModel):
    image_data_base64: str

class RegisterDirectoryRequest(BaseModel):
    name: str
    path: str
    languages: list[str]

class UnregisterDirectoryRequest(BaseModel):
    name: str
