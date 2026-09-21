"""Export backend-owned public shapes; invoke with PYTHONPATH=apps/api."""
import json
from pathlib import Path
from app.schemas.stream import stream_adapter
from app.schemas.tools import QuoteDTO

root=Path(__file__).resolve().parents[1]/'packages/contracts'
for name,schema in [('sse_events.schema.json',stream_adapter.json_schema()),('quote_dto.schema.json',QuoteDTO.model_json_schema())]:
    schema['$schema']='https://json-schema.org/draft/2020-12/schema'
    (root/name).write_text(json.dumps(schema,ensure_ascii=False,indent=2)+'\n')
    print('Exported',name)
