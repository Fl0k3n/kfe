from pydantic import BaseModel


class UpdateDescriptionRequest(BaseModel):
    file_id: int
    description: str

class UpdateTranscriptRequest(BaseModel):
    file_id: int
    transcript: str

class UpdateOCRTextRequest(BaseModel):
    file_id: int
    ocr_text: str

class OpenFileRequest(BaseModel):
    file_id: int

class SearchRequest(BaseModel):
    query: str

class FindSimilarItemsRequest(BaseModel):
    file_id: int

class GetOffsetOfFileInLoadResultsRequest(BaseModel):
    file_id: int

class FindSimilarImagesToUploadedImageRequest(BaseModel):
    image_data_base64: str

class RegisterDirectoryRequest(BaseModel):
    name: str
    path: str
    primary_language: str

class UnregisterDirectoryRequest(BaseModel):
    name: str

class UnregisterDirectoryRequest(BaseModel):
    name: str

class UpdateScreenshotTypeRequest(BaseModel):
    file_id: int
    is_screenshot: bool
