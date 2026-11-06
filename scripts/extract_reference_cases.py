"""Rebuild the seven supplied before/after crops from their original screenshots."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

IDS = [
    'de9f04a8-c024-408f-88dc-57b2858d53c7',
    '6086312f-da11-4175-8172-c15d01f3aafb',
    'a7a94b27-6d2e-44fa-8660-a7f6823b8f71',
    '1dc4faa5-1aa8-43d4-8235-aad8da5a4afa',
    'bbec94bb-1744-40c4-9832-59bca8e89981',
    'f3d319ea-d386-4b39-b35f-91041aaad73d',
    '0404946c-2248-41b3-a66b-88d4abbaf736',
]
# Coordinates measured on the 949 x 2048 display, not the original JPEG pixels.
REGIONS = [
    ((35,359,915,857),(29,958,920,1461)),
    ((35,359,915,857),(29,958,920,1461)),
    ((35,359,915,857),(29,958,920,1461)),
    ((41,359,903,842),(43,948,905,1426)),
    ((41,359,903,842),(43,948,905,1426)),
    ((52,370,898,845),(53,972,899,1450)),
    ((52,370,898,845),(53,972,899,1450)),
]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    records=[]
    for index,(identifier,regions) in enumerate(zip(IDS,REGIONS),1):
        source=args.source_dir/('codex-clipboard-'+identifier+'.jpg')
        with Image.open(source) as image:
            item={'case':index,'source_filename':source.name,'source_size':image.size,
                  'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'crops':{}}
            for label,region in zip(('before','after'),regions):
                bounds=tuple(round(value*image.size[axis%2]/(949 if axis%2==0 else 2048)) for axis,value in enumerate(region))
                crop=image.crop(bounds)
                name=f'case-{index:02d}-{label}.png'
                crop.save(args.output_dir/name)
                item['crops'][label]={'file':name,'bbox_original':bounds,'size':crop.size}
            records.append(item)
    sheet=Image.new('RGB',(1440,7*445),'#EDF1F4')
    draw=ImageDraw.Draw(sheet)
    for index,item in enumerate(records):
        y=index*445
        for col,label in enumerate(('before','after')):
            draw.text((col*720+18,y+10),f'CASE {index+1:02d} / {label.upper()}',fill='#173D59')
            with Image.open(args.output_dir/item['crops'][label]['file']) as image:
                image.thumbnail((696,408))
                sheet.paste(image,(col*720+12,y+33))
    sheet.save(args.output_dir/'reference-contact-sheet.jpg',quality=94)
    (args.output_dir/'source-manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Created {len(records)} reference pairs and contact sheet.')

if __name__=='__main__':
    main()
