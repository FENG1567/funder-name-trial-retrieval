"""Recalculate the reported quantities and regenerate the manuscript figures."""
from __future__ import annotations
import argparse
import csv
from datetime import date
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent

def read_csv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))

def truth(value):
    token=str(value).strip().lower()
    if token in ('true','1','yes'):
        return True
    if token in ('false','0','no'):
        return False
    raise ValueError(f'Not an explicit boolean: {value!r}')

def percentage(n, d):
    if d < 0 or n < 0 or n > d:
        raise ValueError('Invalid fraction')
    return 100*n/d if d else None

def difference(n, d, rn, rd):
    current, reference=percentage(n,d),percentage(rn,rd)
    return None if current is None or reference is None else current-reference

def identifiers(value):
    return set(re.findall(r'NCT\d{8}|ISRCTN\d{8}', str(value)))

def family_union(links):
    return {r['family_id'] for r in links if truth(r['A_known_identifier_hit'])}

def historical_mrc_eligible(value):
    return date.fromisoformat(str(value)[:10]) <= date(2022,12,31)

def count_fraction(records, positive):
    return [sum(bool(positive(r)) for r in records),len(records)]

def write_json(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def write_csv(path, records):
    if not records:
        return
    with path.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

def fraction_text(pair, with_pct=True):
    n,d=pair
    if d==0:
        return 'NE'
    return f'{n}/{d} ({percentage(n,d):.1f})' if with_pct else f'{n}/{d}'

def export_tables(tables, label, output):
    # Presentation exports; not read by the calculations.
    for table in tables:
        with (output/f'{label}_table_{table["number"]}.csv').open('w',encoding='utf-8',newline='') as stream:
            writer=csv.writer(stream)
            writer.writerow(table['columns'])
            for row in table['rows']:
                writer.writerow([row['section']] if isinstance(row,dict) else row)

def run(output, figures=False):
    output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    curated=ROOT/'data/curated'
    aggregate=ROOT/'data/aggregate'
    expected=json.loads((ROOT/'expected/manuscript_tables.json').read_text(encoding='utf-8'))
    checks=[]
    def check(label, observed, target):
        checks.append({'check':label,'observed':observed,'expected':target,'passed':observed==target})

    # Current posting: aggregate comparison inputs.
    fig1=read_csv(aggregate/'figure1_source_data.csv')
    current=[]
    table2=[]
    for row in fig1:
        rn,rd=int(row['reference_posted']),int(row['reference_eligible'])
        n,d=(int(row['query_posted']),int(row['query_eligible'])) if row['posting_status']=='estimable' else (0,0)
        coverage=[int(row['coverage_num']),int(row['coverage_den'])]
        dp=difference(n,d,rn,rd)
        current.append({'source':row['source'],'strategy':row['strategy'],'coverage_n':coverage[0],'coverage_N':coverage[1],
            'coverage_pct':percentage(*coverage),'reference_posted':rn,'reference_eligible':rd,
            'subset_posted':n if d else None,'subset_eligible':d,'subset_posting_pct':percentage(n,d),
            'difference_pp':dp})
        table2.append([fraction_text(coverage,False),fraction_text([rn,rd]),fraction_text([n,d]),None if dp is None else round(dp,1)])
    target2=next(t for t in expected if t['number']==2)['rows']
    for i,(actual,target) in enumerate(zip(table2,target2)):
        desired=target[1:4]+[None if target[4]=='NE' else float(target[4].replace('−','-'))]
        check(f'Table2_row_{i+1}',actual,desired)
    check('Table2_row_count',len(table2),len(target2))
    write_csv(output/'table2_recalculated.csv',current)
    write_csv(output/'figure1_source_data.csv',fig1)

    # Historical SU2C: actual row-coded union, distinct from current ACTUAL eligibility.
    su=read_csv(curated/'Supplementary_Data_1_SU2C_historical_evidence.csv')
    hist=[r for r in su if truth(r['historical_eligible'])]
    hit=[r for r in hist if truth(r['core_and_expanded_name_query_hit'])]
    def registry(r):
        return truth(r['ctgov_results']) or truth(r['external_registry_results'])
    def reported(r):
        return registry(r) or truth(r['qualifying_journal_report'])
    for r in hist:
        check('SU2C_registry_union:'+r['NCT'],registry(r),truth(r['any_registry_results']))
        check('SU2C_reporting_union:'+r['NCT'],reported(r),truth(r['registry_or_journal_result']))
    su_summary={'reference':count_fraction(hist,reported),'name_subset':count_fraction(hit,reported),
        'conference_reference':count_fraction(hist,lambda r:reported(r) or truth(r['conference_sensitivity_addition'])),
        'conference_subset':count_fraction(hit,lambda r:reported(r) or truth(r['conference_sensitivity_addition'])),
        'current_ACTUAL_eligible_count':sum(truth(r['current_ACTUAL_enrollment_eligible']) for r in su),
        'registry_n':sum(registry(r) for r in hist),'journal_n':sum(truth(r['qualifying_journal_report']) for r in hist),
        'registry_journal_overlap':sum(registry(r) and truth(r['qualifying_journal_report']) for r in hist)}
    check('SU2C_current_eligibility_separate',su_summary['current_ACTUAL_eligible_count'],24)

    # MRC historical source rows; no expansion into multiple NCT observations.
    mr=read_csv(curated/'Supplementary_Data_6_MRC_historical_source_rows.csv')
    full_mrc=read_csv(curated/'mrc_row_classification.csv')
    eligible_full=[r for r in full_mrc if historical_mrc_eligible(r['trial_end_date_registry_raw'])]
    check('MRC_historical_source_row_identity',sorted(r['source_excel_row'] for r in mr),sorted(r['source_excel_row'] for r in eligible_full))
    nct_rows=[r for r in mr if identifiers(r['nct_identifiers_extracted'])]
    all_reported=lambda r:r['derived_reporting_class_within_eligible_cohort']=='reported'
    ref=count_fraction(mr,all_reported)
    nct=count_fraction(nct_rows,all_reported)
    any_registry=[r for r in mr if any(r[k].strip() for k in ('isctn_reference_raw','clinicaltrials_gov_reference_raw','eudract_euctr_reference_raw','other_who_primary_registry_raw'))]
    fig2=read_csv(aggregate/'figure2_source_data.csv')
    check('MRC_figure2_reference',[int(fig2[0]['reported_n']),int(fig2[0]['reported_denominator'])],ref)
    check('MRC_figure2_NCT',[int(fig2[1]['reported_n']),int(fig2[1]['reported_denominator'])],nct)
    branch=[[int(r['reported_n']),int(r['reported_denominator'])] for r in fig2[2:]]
    mrc_summary={'all_source_rows':len(full_mrc),'historical_rows':len(mr),'reference':ref,'any_registry':count_fraction(any_registry,all_reported),
        'NCT_bearing':nct,'historical_unique_NCTs':len(set().union(*(identifiers(r['nct_identifiers_extracted']) for r in nct_rows))),
        'core_query':branch[0],'expanded_query':branch[1]}
    table3=[]
    for label,base,subset in [
        ('SU2C historical',su_summary['reference'],su_summary['name_subset']),
        ('SU2C conference sensitivity',su_summary['conference_reference'],su_summary['conference_subset']),
        ('MRC any registry',ref,mrc_summary['any_registry']),
        ('MRC NCT-bearing',ref,nct),
        ('MRC core',nct,branch[0]),
        ('MRC expanded',nct,branch[1])]:
        table3.append({'comparison':label,'reference_n':base[0],'reference_N':base[1],'subset_n':subset[0],'subset_N':subset[1],
            'difference_pp':difference(*subset,*base)})
    target3=next(t for t in expected if t['number']==3)['rows']
    for i,(actual,target) in enumerate(zip(table3,target3)):
        observed=[fraction_text([actual['reference_n'],actual['reference_N']]),fraction_text([actual['subset_n'],actual['subset_N']]),round(actual['difference_pp'],1)]
        desired=target[1:3]+[float(target[3].replace('−','-'))]
        check(f'Table3_row_{i+1}',observed,desired)
    check('Table3_row_count',len(table3),len(target3))
    write_csv(output/'table3_recalculated.csv',table3)
    write_csv(output/'figure2_source_data.csv',fig2)

    # NIHR full-frame observed A hits.
    families=read_csv(curated/'Supplementary_Data_3_NIHR_full125_families.csv')
    links=read_csv(curated/'Supplementary_Data_4_NIHR_full125_links.csv')
    linked={r['family_id'] for r in links}
    unique={(r['platform'],r['registry_id']) for r in links}
    check('NIHR_link_uniqueness',len(unique),len(links))
    check('NIHR_family_id_uniqueness',len({r['family_id'] for r in families}),len(families))
    for fam in families:
        islinked=fam['family_id'] in linked
        check('NIHR_reference_status:'+fam['family_id'],fam['reference_status']=='linked',islinked)
        if islinked:
            check('NIHR_family_A_union:'+fam['family_id'],truth(fam['any_reference_ID_hit_by_A']),fam['family_id'] in family_union(links))
    nihr={'families':len(families),'linked_families':len(linked),'unresolved_families':len(families)-len(linked),
        'links':len(unique),'A_hit_families':len(family_union(links)),'platforms':{}}
    table4full=[]
    for platform_name in sorted({r['platform'] for r in links}):
        subset=[r for r in links if r['platform']==platform_name]
        pair=count_fraction(subset,lambda r:truth(r['A_known_identifier_hit']))
        nihr['platforms'][platform_name]=pair
        table4full.append({'platform':platform_name,'known_IDs':pair[1],'A_hit_IDs':pair[0],'A_coverage_pct':percentage(*pair),'B':'Not evaluated'})
    target4=next(t for t in expected if t['number']==4)['rows'][-2:]
    for target in target4:
        found=next((p for p in nihr['platforms'] if p.lower().replace('.','')==target[0].lower().replace('.','')),None)
        if found is None:
            raise ValueError(f'Unmatched NIHR platform {target[0]}')
        check('Table4_fullframe_'+target[0],fraction_text(nihr['platforms'][found],False),target[3])
    write_csv(output/'table4_fullframe_recalculated.csv',table4full)
    selected=json.loads((aggregate/'nihr_selected_samples.json').read_text(encoding='utf-8'))
    # Selected-sample results.
    write_json(output/'nihr_selected_samples.json',selected)
    for group,label in [('Pilot','pilot'),('Extension','extension')]:
        sample=[r for r in families if r['sample_group']==group]
        check('NIHR_'+label+'_membership_n',len(sample),selected[label]['families'])
    pilot=read_csv(curated/'nihr_pilot_12_family_reference_links.csv')
    pilotids=set().union(*(identifiers(r['reference_identifiers']) for r in pilot))
    check('NIHR_pilot_reference_ID_count',len(pilotids),selected['pilot']['identifiers'])

    # Supporting descriptive evidence.
    papers=read_csv(curated/'Supplementary_Data_2_MRC_paper_evidence.csv')
    source_links=read_csv(curated/'Supplementary_Data_5_SU2C_project_registration_links.csv')
    supporting={'MRC_confirmed_paper_rows':len(papers),
        'MRC_confirmed_rows_with_source_NCT':sum(bool(identifiers(p['source_NCTs'])) for p in papers),
        'MRC_confirmed_rows_without_source_NCT':sum(not bool(identifiers(p['source_NCTs'])) for p in papers),
        'SU2C_projects':len({p['project_id'] for p in source_links}),
        'SU2C_unique_NCTs':len({p['NCT'] for p in source_links}),
        'SU2C_project_link_rows':len(source_links)}
    check('MRC_confirmed_paper_row_uniqueness',len({p['source_excel_row'] for p in papers}),len(papers))
    check('MRC_confirmed_papers_n',len(papers),13)
    check('MRC_confirmed_paper_source_partition',
          [supporting['MRC_confirmed_rows_with_source_NCT'],supporting['MRC_confirmed_rows_without_source_NCT']],[6,7])
    table1=next(t for t in expected if t['number']==1)['rows']
    check('Table1_SU2C_inventory',[supporting['SU2C_projects'],supporting['SU2C_unique_NCTs']],
          [int(n) for n in re.findall(r'\d+',table1[0][1])])
    mrc_ids=set().union(*(identifiers(p['nct_identifiers_extracted']) for p in full_mrc))
    check('Table1_MRC_inventory',[len(full_mrc),sum(bool(identifiers(p['nct_identifiers_extracted'])) for p in full_mrc),len(mrc_ids)],
          [int(n) for n in re.findall(r'\d+',table1[1][1])])
    check('Table1_NIHR_inventory',[nihr['families'],nihr['linked_families'],nihr['unresolved_families']],
          [int(n) for n in re.findall(r'\d+',table1[3][1])])
    for t in expected:
        export_tables([t],'manuscript',output)
    supplement=json.loads((ROOT/'expected/supplement_tables.json').read_text(encoding='utf-8'))
    export_tables(supplement,'supplement',output)
    summaries={'SU2C_historical':su_summary,'MRC_historical':mrc_summary,'NIHR_full_frame':nihr,'supporting':supporting}
    write_json(output/'recalculated_summaries.json',summaries)
    result={'passed':all(r['passed'] for r in checks),'checks':checks}
    failed=[r for r in checks if not r['passed']]
    if failed:
        raise ValueError(json.dumps(failed,ensure_ascii=False))
    if figures:
        subprocess.run([sys.executable,str(ROOT/'plot_figures.py'),'--source-dir',str(output),'--output-dir',str(output/'figures')],check=True)
    print(f'{len(checks)} checks passed. Outputs: {output}')
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-figures',action='store_true',help='Standard-library calculations only')
    parser.add_argument('--output-dir',type=Path,default=ROOT/'results')
    args=parser.parse_args()
    run(args.output_dir,figures=not args.no_figures)
