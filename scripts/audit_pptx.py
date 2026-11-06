"""Inspect editable PPTX objects for slide-review clues; does not render or grade design."""
import argparse
import json
import posixpath
import re
import sys
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

P='http://schemas.openxmlformats.org/presentationml/2006/main'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
M='http://schemas.openxmlformats.org/officeDocument/2006/math'
A14='http://schemas.microsoft.com/office/drawing/2010/main'
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
MC='http://schemas.openxmlformats.org/markup-compatibility/2006'
NS={'p':P,'a':A,'m':M,'a14':A14,'mc':MC}

def equation_details(item,name,bounds):
    equations=item.findall('.//m:oMath',NS)
    if not equations:
        return None
    kinds={'fractions':'f','subscripts':'sSub','superscripts':'sSup',
           'sub_superscripts':'sSubSup','matrices':'m','radicals':'rad',
           'delimiters':'d','nary_operators':'nary','equation_arrays':'eqArr'}
    return {'object':name,'office_math_count':len(equations),
            'drawing_math_container_count':len(item.findall('.//a14:m',NS)),
            'text':[''.join(t.text or '' for t in equation.findall('.//m:t',NS)) for equation in equations],
            'structures':{label:sum(len(eq.findall('.//m:'+tag,NS)) for eq in equations) for label,tag in kinds.items()},
            'frame_inches':[round(value/914400,3) for value in bounds] if bounds else None,
            'wordprocessing_elements_review':sum(1 for element in item.iter() if element.tag.startswith('{'+W+'}'))}

def style_colors(item):
    """Explicit editable fill/text/line RGB values; excludes raster image pixels."""
    colors={}
    for color in item.findall('.//a:srgbClr',NS):
        value=color.get('val','').upper()
        if re.fullmatch('[0-9A-F]{6}',value):
            colors[value]=colors.get(value,0)+1
    return colors

def union_area(rectangles):
    """Area of clipped axis-aligned picture frames without overlap double-counting."""
    xs=sorted({edge for x1,y1,x2,y2 in rectangles for edge in (x1,x2)})
    total=0
    for left,right in zip(xs,xs[1:]):
        intervals=sorted((y1,y2) for x1,y1,x2,y2 in rectangles if x1<right and x2>left)
        if not intervals:
            continue
        start,end=intervals[0]
        height=0
        for low,high in intervals[1:]:
            if low>end:
                height+=end-start
                start,end=low,high
            else:
                end=max(end,high)
        total+=(right-left)*(height+end-start)
    return total

def frame(transform,parent):
    if transform is None:
        return None
    offset=transform.find('a:off',NS)
    extent=transform.find('a:ext',NS)
    if offset is None or extent is None:
        return None
    sx,sy,tx,ty=parent
    return (int(offset.get('x'))*sx+tx,int(offset.get('y'))*sy+ty,
            int(extent.get('cx'))*sx,int(extent.get('cy'))*sy)

def objects(container,parent=(1,1,0,0)):
    for item in container:
        local=item.tag.rsplit('}',1)[-1]
        if local=='AlternateContent':
            # PowerPoint saves native equations in Choice plus a bitmap fallback.
            # Inspect a supported shape branch once to avoid duplicate objects.
            choices=item.findall('mc:Choice',NS)+item.findall('mc:Fallback',NS)
            for choice in choices:
                if any(child.tag in {'{'+P+'}'+kind for kind in ('sp','pic','graphicFrame','cxnSp','grpSp')} for child in choice):
                    yield from objects(choice,parent)
                    break
        elif local=='grpSp':
            transform=item.find('p:grpSpPr/a:xfrm',NS)
            bounds=frame(transform,parent)
            if bounds is None:
                yield from objects(item,parent)
                continue
            offset=transform.find('a:chOff',NS)
            extent=transform.find('a:chExt',NS)
            if offset is None or extent is None:
                yield from objects(item,parent)
                continue
            sx=bounds[2]/max(1,int(extent.get('cx')))
            sy=bounds[3]/max(1,int(extent.get('cy')))
            nested=(sx,sy,bounds[0]-int(offset.get('x'))*sx,bounds[1]-int(offset.get('y'))*sy)
            yield from objects(item,nested)
        elif local in ('sp','pic','graphicFrame','cxnSp'):
            transform=item.find('p:spPr/a:xfrm',NS)
            if transform is None:
                transform=item.find('p:xfrm',NS)
            yield local,item,frame(transform,parent),transform

def table_alignment(item,name):
    table=item.find('.//a:tbl',NS)
    if table is None:
        return None
    rows=table.findall('a:tr',NS)
    columns=table.findall('a:tblGrid/a:gridCol',NS)
    result={'object':name,'rows':len(rows),'columns':len(columns),
            'text_cell_count':0,'explicitly_centered_cells':0,
            'horizontal_alignment_inherited':0,'alignment_review_cells':[]}
    for row_number,row in enumerate(rows,1):
        for column_number,cell in enumerate(row.findall('a:tc',NS),1):
            paragraphs=cell.findall('a:txBody/a:p',NS)
            text=''.join(value.text or '' for paragraph in paragraphs for value in paragraph.findall('.//a:t',NS))
            if not text.strip():
                continue
            result['text_cell_count']+=1
            alignments=[]
            for paragraph in paragraphs:
                if not ''.join(value.text or '' for value in paragraph.findall('.//a:t',NS)).strip():
                    continue
                props=paragraph.find('a:pPr',NS)
                alignments.append(props.get('algn') if props is not None else None)
            cell_props=cell.find('a:tcPr',NS)
            vertical=cell_props.get('anchor','t') if cell_props is not None else 't'
            inherited=any(value is None for value in alignments)
            if inherited:
                result['horizontal_alignment_inherited']+=1
            centered=bool(alignments) and all(value=='ctr' for value in alignments) and vertical=='ctr'
            if centered:
                result['explicitly_centered_cells']+=1
            else:
                result['alignment_review_cells'].append({'row':row_number,'column':column_number,
                    'text':text[:60],'horizontal':alignments,'vertical':vertical})
    return result

def audit(path,selected):
    with zipfile.ZipFile(path) as package:
        error=package.testzip()
        if error:
            raise ValueError('Invalid ZIP member '+error)
        presentation=ET.fromstring(package.read('ppt/presentation.xml'))
        size=presentation.find('p:sldSz',NS)
        width,height=int(size.get('cx')),int(size.get('cy'))
        links={x.get('Id'):x.get('Target') for x in ET.fromstring(package.read('ppt/_rels/presentation.xml.rels'))}
        slides=list(presentation.find('p:sldIdLst',NS))
        if any(number<1 or number>len(slides) for number in selected):
            raise ValueError('Requested slide numbers are outside the presentation.')
        result={'file':str(path.resolve()),'slide_count':len(slides),
                'slide_size_inches':[round(width/914400,3),round(height/914400,3)],
                'limits':['No rendering or OCR; inherited text geometry/fonts may be unavailable.',
                          'Picture-frame share differs from semantic graphic share.',
                          'Rotation, clipping masks and text glyph width are not evaluated.',
                          'Effect and alignment counts inspect explicit XML; theme inheritance can require visual review.'],
                'slides':[]}
        for index,slide in enumerate(slides,1):
            if selected and index not in selected:
                continue
            target=links[slide.get('{'+R+'}id')]
            part=target.lstrip('/') if target.startswith('/') else posixpath.normpath('ppt/'+target)
            tree=ET.fromstring(package.read(part)).find('p:cSld/p:spTree',NS)
            page={'number':index,'picture_count':0,'text_object_count':0,'native_object_count':0,
                  'small_text_candidates':[],'off_canvas_candidates':[],'single_character_candidates':[],
                  'multiline_text_objects':[],'rotated_objects':0,
                  'gradient_object_count':0,'transparent_object_count':0,'shadow_object_count':0,
                  'dashed_object_count':0,'tables':[],'equations':[],
                  'explicit_style_colors':{},'deprecated_theme_color_candidates':[]}
            pictures=[]
            for kind,item,bounds,transform in objects(tree):
                page['native_object_count']+=1
                identifier=item.find('.//p:cNvPr',NS)
                name=identifier.get('name','') if identifier is not None else kind
                colors=style_colors(item)
                for color,count in colors.items():
                    page['explicit_style_colors'][color]=page['explicit_style_colors'].get(color,0)+count
                deprecated=sorted(set(colors)&{'124F78','086CA8','123F75'})
                if deprecated:
                    page['deprecated_theme_color_candidates'].append({'object':name,'colors':deprecated})
                equation=equation_details(item,name,bounds)
                if equation is not None:
                    page['equations'].append(equation)
                if item.find('.//a:gradFill',NS) is not None:
                    page['gradient_object_count']+=1
                if any(int(alpha.get('val','100000'))<100000 for alpha in item.findall('.//a:alpha',NS)):
                    page['transparent_object_count']+=1
                if item.find('.//a:outerShdw',NS) is not None or item.find('.//a:innerShdw',NS) is not None:
                    page['shadow_object_count']+=1
                if any(dash.get('val')!='solid' for dash in item.findall('.//a:prstDash',NS)):
                    page['dashed_object_count']+=1
                alignment=table_alignment(item,name)
                if alignment is not None:
                    page['tables'].append(alignment)
                if transform is not None and transform.get('rot','0')!='0':
                    page['rotated_objects']+=1
                if bounds:
                    x,y,w,h=bounds
                    if x<-width*.002 or y<-height*.002 or x+w>width*1.002 or y+h>height*1.002:
                        page['off_canvas_candidates'].append(name)
                    if kind=='pic':
                        page['picture_count']+=1
                        if min(width,x+w)>max(0,x) and min(height,y+h)>max(0,y):
                            pictures.append((max(0,x),max(0,y),min(width,x+w),min(height,y+h)))
                body=item.find('p:txBody',NS)
                if body is None:
                    continue
                paragraphs=[''.join(t.text or '' for t in p.findall('.//a:t',NS)) for p in body.findall('a:p',NS)]
                value='\n'.join(paragraphs).strip()
                if not value:
                    continue
                page['text_object_count']+=1
                if len(value)==1 and re.fullmatch('[\u4e00-\u9fff]',value):
                    page['single_character_candidates'].append({'object':name,'text':value})
                if sum(bool(p.strip()) for p in paragraphs)>1 or body.find('.//a:br',NS) is not None:
                    page['multiline_text_objects'].append({'object':name,'text':value[:100]})
                sizes=[int(run.get('sz'))/100 for run in body.findall('.//a:rPr',NS) if run.get('sz')]
                if sizes and min(sizes)<16:
                    page['small_text_candidates'].append({'object':name,'text':value[:80],'minimum_pt':min(sizes)})
            page['picture_frame_share_percent']=round(union_area(pictures)/(width*height)*100,1)
            result['slides'].append(page)
        return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pptx',type=Path)
    parser.add_argument('--slides',type=int,nargs='+',help='One-based slide numbers; all by default.')
    parser.add_argument('--output',type=Path,help='Optional UTF-8 JSON report.')
    args=parser.parse_args()
    result=audit(args.pptx,set(args.slides or []))
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(str(args.output.resolve()))
    else:
        print(json.dumps(result,ensure_ascii=True,indent=2))

if __name__=='__main__':
    main()
