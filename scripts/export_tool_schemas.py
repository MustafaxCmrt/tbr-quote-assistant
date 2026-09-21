"""Generate real validation schemas without modifying descriptive company contracts."""
import json
from pathlib import Path
from app.services.executor import SCHEMAS

root = Path(__file__).resolve().parents[1]
source = json.loads((root/'data/source/tool_contracts.json').read_text())
assert set(SCHEMAS)=={tool['name'] for tool in source}
result={}
for tool in source:
    schema=SCHEMAS[tool['name']].model_json_schema()
    assert set(schema['properties'])==set(tool['input_schema']), tool['name']
    result[tool['name']]=schema
(root/'packages/contracts/tool_inputs.schema.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print('PASS six tool names and input field names match original contracts; JSON Schemas exported.')
