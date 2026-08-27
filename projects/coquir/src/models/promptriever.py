from mteb.model_meta import ModelMeta
from mteb.models.promptriever_models import PromptrieverWrapper, _loader
import torch

local_promptriever_llama2 = ModelMeta(
    loader=_loader(
        PromptrieverWrapper,
        base_model_name_or_path="meta-llama/Llama-2-7b-hf",
        peft_model_name_or_path="example_path",
        device_map="auto",
        torch_dtype=torch.bfloat16,
    ),
    name="local-promptriever-llama2",
    languages=["eng_Latn"],
    open_source=True,
    revision=None,
    release_date="2024-09-15",
)

PROMPTRIEVER_DICT = {

}