import torch
from transformers import AutoModel, AutoTokenizer
import numpy as np


def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0] #First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)


class AutoModelRetriever:
    # the default setup is to use mean pooling and not to apply L2 normalization
    def __init__(self, model_name, pooling='mean', l2_norm=False, **kwargs):
        self.model = AutoModel.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.pooling = pooling
        self.l2_norm = l2_norm

        if torch.cuda.is_available():
            self.device = 'cuda'
        else:
            self.device = 'cpu'

        self.model.to(self.device)

    def encode_queries(self, queries, batch_size: int, **kwargs) -> np.ndarray:
        input_kwargs = {}
        input_kwargs['text'] = queries

        inputs = self.tokenizer(**input_kwargs, return_tensors='pt', padding=True, truncation=True)
        inputs.to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
        if self.pooling == 'cls':
            embeddings = outputs[0][:, 0, :].detach().cpu().numpy()
        elif self.pooling == 'mean':
            embeddings = mean_pooling(outputs, inputs['attention_mask']).detach().cpu().numpy()
        else:
            raise ValueError(f'Pooling {self.pooling} is not supported')
        
        inputs.detach().to('cpu')

        return embeddings

    def encode_corpus(self, corpus, batch_size: int, **kwargs) -> np.ndarray:
        input_texts = [f"{doc.get('title', '')} {doc['text']}" for doc in corpus]
        input_kwargs = {}
        input_kwargs['text'] = input_texts
       
        inputs = self.tokenizer(**input_kwargs, return_tensors='pt', padding=True, truncation=True)
        inputs.to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
        if self.pooling == 'cls':
            embeddings = outputs[0][:, 0, :].detach().cpu().numpy()
        elif self.pooling == 'mean':
            embeddings = mean_pooling(outputs, inputs['attention_mask']).detach().cpu().numpy()
        else:
            raise ValueError(f'Pooling {self.pooling} is not supported')

        inputs.detach().to('cpu')
        return embeddings