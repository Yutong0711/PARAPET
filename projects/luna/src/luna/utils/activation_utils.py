import torch
import torch.nn.functional as F
from baukit import Trace, TraceDict
import pickle

def get_llama_activations_bau(model, prompt, device): 

    HEADS = [f"model.layers.{i}.self_attn.head_out" for i in range(model.config.num_hidden_layers)]
    MLPS = [f"model.layers.{i}.mlp" for i in range(model.config.num_hidden_layers)]

    with torch.no_grad():
        prompt = prompt.to(device)
        with TraceDict(model, HEADS+MLPS) as ret:
            output = model(prompt, output_hidden_states = True)
        hidden_states = output.hidden_states
        hidden_states = hidden_states[1:]
        hidden_states = torch.stack(hidden_states, dim = 0).squeeze()
        hidden_states = hidden_states.detach().cpu().numpy()
        head_wise_hidden_states = [ret[head].output.squeeze().detach().cpu() for head in HEADS]
        head_wise_hidden_states = torch.stack(head_wise_hidden_states, dim = 0).squeeze().numpy()
        mlp_wise_hidden_states = [ret[mlp].output.squeeze().detach().cpu() for mlp in MLPS]
        mlp_wise_hidden_states = torch.stack(mlp_wise_hidden_states, dim = 0).squeeze().numpy()

    return hidden_states, head_wise_hidden_states, mlp_wise_hidden_states

def get_llama_probs(model, prompt, device):
    model.eval()
    with torch.no_grad(): 
        prompt = prompt.to(device)
        probs = F.softmax(model(prompt).logits, dim=-1)
        target_probabilities = probs.gather(-1, prompt.unsqueeze(-1)).squeeze(-1)
        target_probabilities = target_probabilities.detach().cpu()
        return target_probabilities.tolist()[-1]
    
def get_llama_loss(model, prompt, device, label): 
    model.eval()
    with torch.no_grad(): 
        prompt = prompt.to(device)
        target_loss = model(prompt, labels=label).loss
        target_loss = target_loss.detach().cpu()
        return target_loss.item()

def get_llama_logits(model, prompt, device): 

    model.eval()
    with torch.no_grad(): 
        prompt = prompt.to(device)
        logits = model(prompt).logits
        logits = logits.detach().cpu()
        return logits

def save_probes(probes, path): 
    """takes in a list of sklearn lr probes and saves them to path"""
    with open(path, 'wb') as f: 
        pickle.dump(probes, f)

def load_probes(path): 
    """loads a list of sklearn lr probes from path"""
    with open(path, 'rb') as f: 
        probes = pickle.load(f)
    return probes