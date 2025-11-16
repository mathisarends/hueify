from pydantic import BaseModel, create_model


def make_partial(model: type[BaseModel]) -> type[BaseModel]:
    fields = {
        name: (field.annotation | None, None)
        for name, field in model.model_fields.items()
    }
    return create_model(f"Partial{model.__name__}", **fields)
