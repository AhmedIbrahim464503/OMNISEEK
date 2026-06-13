from pydantic import BaseModel, ConfigDict

class BaseSchema(BaseModel):
    """Base Pydantic schema model setting generic configuration defaults."""
    
    model_config = ConfigDict(from_attributes=True)
