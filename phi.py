from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig
from torch.utils.checkpoint import checkpoint


def prepare_phi(trainable=False):
    name = "microsoft/phi-4"
    revision = "187ef0342fff0eb3333be9f00389385e95ef0b61"
    phi = AutoModelForCausalLM.from_pretrained(name, trust_remote_code=True, revision=revision).bfloat16().to("cuda")
    phi.model.gradient_checkpointing = True
    phi.model._gradient_checkpointing_func = checkpoint
    tokenizer = AutoTokenizer.from_pretrained(name, trust_remote_code=True, revision=revision)

    for param in phi.parameters():
        param.requires_grad = trainable

    print("Listing all trainable parameters:")
    for name, param in phi.named_parameters():
        if param.requires_grad:
            print(f"> {name}, dtype={param.dtype}")
    return phi, tokenizer

def inference(model, tokenizer, prompt, max_tokens):
    inputs = tokenizer(text=prompt, return_tensors="pt").to("cuda")
    cfg = GenerationConfig(output_hidden_states=True, return_dict_in_generate=True)

    generation_args = {
        "max_new_tokens": max_tokens,
        "temperature": 0.0,
        "do_sample": False,
    }
    outputs = model.generate(**inputs, eos_token_id=tokenizer.eos_token_id, generation_config=cfg, **generation_args)
    ids = outputs.sequences[:, inputs['input_ids'].shape[1]:]
    return tokenizer.batch_decode(ids, skip_special_tokens=True)

