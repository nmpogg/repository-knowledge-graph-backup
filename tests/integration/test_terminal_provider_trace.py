"""Real API/coordinator/adapters emit console detail only in explicit debug mode."""

import json
import os
import subprocess
import sys

import pytest

PROGRAM = """
import json,sys,os
from pathlib import Path
from fastapi.testclient import TestClient
from rkg.api import create_app
from rkg.ingestion import LocalSourcePolicy
from rkg.storage import Storage
from rkg.conversations import create_conversation
from rkg.llm import OpenAIProvider,OpenRouterProvider
from rkg.terminal_logging import configure_terminal_logging
from tests.integration.graph_helpers import seed_cycle_graph
root=Path(sys.argv[1]);level=sys.argv[2];name=sys.argv[3]
configure_terminal_logging(level)
with Storage(root/'trace.kuzu') as store:
    repo,sid,batch=seed_cycle_graph(store)
    conv=create_conversation(store,repository_id=repo,snapshot_id=sid)
    subject=next(e for e in batch.entities if e.qualified_name=='app.cycle.a')
    calls=[]
    def transport(payload,headers,timeout):
        calls.append(payload)
        content=json.dumps({'status':'answered','root_id':subject.id,
            'sections':[{'relation':'calls','direction':'outgoing',
            'paths':[{'anchor_id':subject.id,'edge_ids':['private-foreign-edge']}]}]})
        return {'choices':[{'finish_reason':'stop','message':{'content':content}}],
            'test_note':'synthetic-server-key'}
    cls=OpenAIProvider if name=='openai' else OpenRouterProvider
    app=create_app(store,LocalSourcePolicy((root,)),
        session_token=os.environ['RKG_SESSION_TOKEN'],provider=cls(transport))
    with TestClient(app,base_url='http://127.0.0.1') as client:
        body={'question':'What does app.cycle.a call?', 'root_id':subject.id,
            'client_request_id':'trace-test','expected_revision':1}
        route=f'/api/v1/conversations/{conv.id}/turns'
        answer=client.post(route,headers={'X-RKG-Session':os.environ['RKG_SESSION_TOKEN']},json=body)
        replay=client.post(route,headers={'X-RKG-Session':os.environ['RKG_SESSION_TOKEN']},json=body)
        print(json.dumps({'status':answer.status_code,'error':answer.json()['error']['code'],
            'replay_matches':answer.json()==replay.json(),'calls':len(calls),
            'state_preserved':store.get_conversation(conv.id).state==conv.state}))
"""


@pytest.mark.parametrize("name", ["openai", "openrouter"])
@pytest.mark.parametrize("level", ["info", "debug"])
def test_actual_adapter_terminal_levels_and_verbatim_debug(tmp_path, name, level):
    env = dict(
        os.environ,
        OPENAI_API_KEY="synthetic-server-key",
        OPENROUTER_API_KEY="synthetic-server-key",
        RKG_SESSION_TOKEN="synthetic-session-key",
    )
    result = subprocess.run(
        [sys.executable, "-c", PROGRAM, str(tmp_path), level, name],
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    summary = json.loads(result.stdout)
    assert summary == {
        "status": 502,
        "error": "llm_malformed_response",
        "replay_matches": True,
        "calls": 1,
        "state_preserved": True,
    }
    log = result.stderr
    for event in [
        "http_request",
        "turn_started",
        "stage_started",
        "stage_finished",
        "turn_finished",
    ]:
        assert "event=" + event in log
    assert "request_id=" in log and "turn_id=" in log
    assert ("synthetic-server-key" in log) == (level == "debug")
    assert ("private-foreign-edge" in log) == (level == "debug")
    assert ("What does app.cycle.a call?" in log) == (level == "debug")
    if level == "debug":
        for event in [
            "model_profile",
            "provider_request",
            "provider_response",
            "schema_validation_failed",
        ]:
            assert "event=" + event in log
        assert "invalid_schema" in log
        assert "[masked]" not in log
