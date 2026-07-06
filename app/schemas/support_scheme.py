from pydantic import BaseModel, Field

class SupportRequest(BaseModel):
    message_type: str = Field(..., example="Suggestion / Feature Idea")
    description: str = Field(..., example="Explain the details here...")
    username: str = Field("Anonymous", example="azamat_thunder")