from pathlib import Path
R=Path('C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew')
p=R/'client/src/components/records/RecordView.tsx';t=p.read_text(encoding='utf-8')
if "from '../CharacterWorkflow'" not in t:
 t="import { CharacterWorkflow } from '../CharacterWorkflow'\n"+t
 needle='                    : <img className="record-image-field-preview" src={movieFileUrl(apiBase, `/api/movies/files/${record[c.field]}`)} alt="" />'
 replacement='                    : <><img className="record-image-field-preview" src={movieFileUrl(apiBase, `/api/movies/files/${record[c.field]}`)} alt="" />{tableName.toLowerCase().includes(\'character\') && <CharacterWorkflow apiBase={apiBase} fileId={Number(record[c.field])} name={String(record.name ?? `${tableName} ${recordId}`)} compact />}</>'
 assert needle in t;t=t.replace(needle,replacement);p.write_text(t,encoding='utf-8')
print('Added workflow beside character images in record details.')
