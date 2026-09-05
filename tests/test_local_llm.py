import pytest


def test_empty_answer_is_not_replaced_by_reasoning():
    from tools.providers.local_llm import answer_json
    with pytest.raises(ValueError, match='answer'):
        answer_json({'choices':[{'message':{'content':'','reasoning_content':'{"shots":[]}'}}]}, {'type':'object'})


def test_answer_json_validates_schema():
    from tools.providers.local_llm import answer_json
    schema={'type':'object','properties':{'shots':{'type':'array','minItems':1}},'required':['shots']}
    assert answer_json({'choices':[{'message':{'content':'```json\n{"shots":["opening"]}\n```'}}]},schema)=={'shots':['opening']}
    with pytest.raises(ValueError):answer_json({'choices':[{'message':{'content':'{"shots":[]}'}}]},schema)


def test_request_budget_rejects_unbounded_input_and_output():
    from tools.providers.local_llm import bounded_request
    with pytest.raises(ValueError):bounded_request('qwen3.5-4b','a'*2049,512)
    with pytest.raises(ValueError):bounded_request('qwen3.5-4b','hello',4096)


def test_admission_does_not_autoload_or_accept_parallel_model():
    from tools.providers.local_llm import require_loaded
    with pytest.raises(RuntimeError):require_loaded({'models':[]},'qwen3.5-4b')
    with pytest.raises(RuntimeError):require_loaded({'models':[{'key':'qwen3.5-4b','loaded_instances':[{'id':'qwen3.5-4b','config':{'parallel':4}}]}]},'qwen3.5-4b')
    require_loaded({'models':[{'key':'qwen3.5-4b','loaded_instances':[{'id':'qwen3.5-4b','config':{'parallel':1}}]}]},'qwen3.5-4b')
