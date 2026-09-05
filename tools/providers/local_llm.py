"""Optional bounded text helper through the local PAIR proxy. No automatic model loads."""
import argparse
import json
import re
from pathlib import Path
import requests
from jsonschema import validate, ValidationError
from ..run_state import atomic_json, file_lock

ENDPOINT = 'http://127.0.0.1:1234/v1'


def bounded_request(model: str, prompt: str, max_tokens: int = 512) -> dict:
    # A conservative byte budget, not a claim that LM Studio honors context_length.
    # No caller-defined system messages, histories, tools or image payloads bypass it.
    if not prompt.strip() or len(prompt.encode('utf-8')) > 2048:
        raise ValueError('Prompt must contain 1–2048 UTF-8 bytes; split the task into bounded requests')
    if type(max_tokens) is not int or not 1 <= max_tokens <= 1024:
        raise ValueError('Output budget must be 1–1024 tokens')
    if model not in {'qwen3.5-4b', 'qwen3.5-9b'}:
        raise ValueError('Model is not in the qualified local shortlist')
    return {'model':model, 'messages':[{'role':'user','content':prompt}],
            'temperature':0, 'max_tokens':max_tokens, 'stream':False}


def answer_json(response: dict, schema: dict) -> dict:
    choice = response.get('choices', [{}])[0]
    if choice.get('finish_reason') == 'length':
        raise ValueError('Truncated model answer; reduce the task')
    content = choice.get('message', {}).get('content')
    if not isinstance(content, str) or not content.strip():
        raise ValueError('Model returned no answer; reasoning is not an answer artifact')
    content = content.strip()
    if content.startswith('```'):
        match = re.fullmatch(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.S)
        if not match:raise ValueError('Malformed JSON answer fence')
        content = match.group(1)
    try:
        value=json.loads(content);validate(value,schema)
    except (json.JSONDecodeError, ValidationError) as error:
        raise ValueError('Model answer failed JSON/schema validation') from error
    return value


def require_loaded(inventory: dict, model: str):
    instances=[i for m in inventory.get('models',[]) for i in m.get('loaded_instances',[])]
    matching=[i for i in instances if i['id']==model and i.get('config',{}).get('parallel')==1]
    if len(instances)!=1 or len(matching)!=1:
        raise RuntimeError('Explicitly load only the selected local model with parallel=1 before inference')


def generate_json(model: str, prompt: str, schema: dict, output: Path, max_tokens: int = 512):
    payload=bounded_request(model,prompt,max_tokens)
    root=Path(__file__).resolve().parents[2]
    with file_lock(root/'work/local-inference.lock'):
        loaded=requests.get('http://127.0.0.1:1235/api/v1/models',timeout=5)
        loaded.raise_for_status();require_loaded(loaded.json(),model)
        available=requests.get(ENDPOINT+'/models',timeout=5)
        available.raise_for_status()
        if model not in {m['id'] for m in available.json()['data']}:
            raise RuntimeError('Model not advertised by PAIR; explicit local setup required')
        response=requests.post(ENDPOINT+'/chat/completions',json=payload,timeout=(5,90))
        response.raise_for_status()
        data=response.json();result=answer_json(data,schema)
        atomic_json(output,{'result':result,'model':model,'endpoint':ENDPOINT,'usage':data.get('usage'),
                            'input_bytes':len(prompt.encode()),'max_output_tokens':max_tokens})
        return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model',choices=['qwen3.5-4b','qwen3.5-9b'],default='qwen3.5-4b')
    p.add_argument('--prompt',type=Path,required=True);p.add_argument('--schema',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--max-tokens',type=int,default=512)
    a=p.parse_args();print(json.dumps(generate_json(a.model,a.prompt.read_text(),json.loads(a.schema.read_text()),a.out,a.max_tokens)))
