"""Preserve explicit pauses; reject unsupported SSML instead of silently dropping it."""
import re
import xml.etree.ElementTree as ET

def parse_voice_script(text: str) -> list[dict]:
    try:root=ET.fromstring('<script>'+text+'</script>')
    except ET.ParseError as e:raise ValueError('Invalid script markup; escape literal < and &') from e
    result=[]
    if root.text and root.text.strip():result.append({'text':root.text.strip()})
    for node in root:
        if node.tag!='break' or set(node.attrib)!={'time'} or list(node) or node.text:
            raise ValueError('Only empty <break time="300ms"/> is supported')
        match=re.fullmatch(r'(\d+(?:\.\d+)?)(ms|s)',node.attrib['time'])
        if not match:raise ValueError('Invalid pause duration')
        ms=round(float(match[1])*(1000 if match[2]=='s' else 1))
        if ms>60000:raise ValueError('Pause exceeds 60 seconds')
        result.append({'silence_ms':ms})
        if node.tail and node.tail.strip():result.append({'text':node.tail.strip()})
    return result
