from pydantic import BaseModel


class UpdateDescriptionRequest(BaseModel):
    file_id: int
    description: str

class OpenFileRequest(BaseModel):
    file_name: str

class SearchRequest(BaseModel):
    query: str

class FindSimilarItemsRequest(BaseModel):
    file_id: int

class GetIdxOfFileReqeust(BaseModel):
    file_id: int
