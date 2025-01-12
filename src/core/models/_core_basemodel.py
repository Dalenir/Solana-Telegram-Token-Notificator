from pydantic import BaseModel, ConfigDict


class CoreBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
