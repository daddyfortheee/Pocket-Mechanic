"""Evidence-driven next checks. A user report is evidence, never a certainty score."""
from hashlib import sha256

CHOICES = {
    'dsc_lights': [('off_only','DSC OFF only, steady'),('both','DSC OFF and traction / ABS warning'),('flashing','DSC OFF flashes'),('brake','Red brake warning or abnormal braking'),('unsure','I cannot identify the lights')],
    'dsc_scan': [('codes','ABS / DSC codes retrieved'),('none','ABS / DSC scan completed; no codes'),('engine_only','Only engine codes were checked'),('help','I need a scanner or qualified help')],
    'start_behavior': [('no_crank','Clicks or does not turn over'),('slow_crank','Turns over slowly'),('cranks','Turns over normally but will not run'),('stalls','Starts, then stalls'),('unsure','I cannot tell')],
    'battery_test': [('passed','Charged and passed a load / conductance test'),('failed','Failed testing after charging'),('untested','Not tested yet'),('unsafe','Damaged, leaking, hot, or unsafe')],
    'connection_test': [('passed','Cable / ground tests passed'),('fault','A cable or ground fault was measured'),('help','I cannot perform this test safely')],
    'starter_test': [('control_fault','A relay / start-command fault was confirmed'),('starter_fault','Correct power, ground and command; starter fault confirmed'),('inconclusive','Tests did not isolate the fault'),('help','I need qualified help')],
    'repair_retest': [('resolved','Repair completed; original symptom is gone'),('persists','Repair completed; original symptom remains'),('not_done','Repair has not been completed'),('unsafe','Unsafe to test')],
    'project_verify': [('resolved','Project meets the goal and safety checks'),('persists','Something still needs correction'),('not_done','Not finished yet')],
}


def evidence(answers):
    records=answers.get('guided_answers',[])
    if not isinstance(records,list): return []
    result=[]
    for record in records[-40:]:
        if not isinstance(record,dict): continue
        q,a,d=record.get('question_id'),record.get('answer'),record.get('detail','')
        if not isinstance(q,str) or not isinstance(a,str) or not isinstance(d,str): continue
        allowed=dict(CHOICES.get(q,[]))
        if q.startswith('check_') and q.endswith('_confirm'): allowed={'confirmed':'Confirmed by diagnostic testing','inconclusive':'Not confirmed','help':'Need help'}
        elif q.startswith('check_'): allowed={'observed':'Observed a problem','clear':'Check completed; no fault observed','help':'Cannot test safely'}
        if q.startswith('project_') and q!='project_verify': allowed={'clear':'Completed','observed':'Blocked','help':'Need help'}
        if a not in allowed: continue
        result.append({'question_id':q[:80],'answer':a,'detail':d.strip()[:1000]})
    return result


def with_evidence(answers):
    result=dict(answers)
    records=evidence(answers)
    result['guided_answers']=records
    latest={x['question_id']:x for x in records}
    behavior=latest.get('start_behavior',{}).get('answer')
    if behavior in {'no_crank','slow_crank','cranks','stalls'}: result['starting_behavior']=behavior
    findings=result.get('findings',[])
    findings=[x for x in findings if isinstance(x,str)] if isinstance(findings,list) else []
    battery=latest.get('battery_test',{}).get('answer')
    if battery=='passed': findings.append('Battery passed a load test after charging.')
    if battery=='failed': findings.append('Battery failed a load test after charging.')
    for row in records:
        if row['detail']: findings.append(row['detail'])
    result['findings']=findings[-40:]
    return result


def step(question_id,title,instruction,why,choices=None,state='investigating',requires_detail=False):
    return {'question_id':question_id,'title':title,'instruction':instruction,'why':why,
            'choices':[{'value':v,'label':label} for v,label in (choices if choices is not None else CHOICES.get(question_id,[]))],
            'state':state,'requires_detail':requires_detail}


def build_guided_step(category,symptom,answers,causes):
    records=evidence(answers)
    latest={x['question_id']:x for x in records}
    answer=lambda q: latest.get(q,{}).get('answer')
    if any(c.safety=='stop' for c in causes) or any(r['answer']=='unsafe' for r in records) or latest.get('dsc_lights',{}).get('answer')=='brake':
        return step('stop','Make it safe first','Stop use and follow the safety warning. Do not perform further live tests. Get qualified help.','Safety takes priority over narrowing the fault.',[],state='stop')
    verification='project_verify' if category=='diy' else 'repair_retest'
    if answer(verification)=='resolved':
        return step('complete','Outcome verified by you','You report that the original issue is resolved. Keep your checks and repair notes; reopen this work if the symptom returns.','A successful retest is different from a suspected cause.',[],state='resolved')
    if answer(verification)=='persists':
        return step(verification,'The original problem remains','Do not repeat part replacement. Review the saved evidence with a qualified technician; the current checks have not established a successful repair.','A failed retest means the original diagnosis or repair needs reassessment.',CHOICES[verification],state='needs_help')
    if answer(verification)=='not_done':
        return step(verification,'Retest when the work is complete','Complete only the repair supported by testing, then check the original symptom safely. If the work is beyond your tools or skills, get qualified help.','The case stays open until you report the result.')
    text=symptom.lower().replace('’',"'")
    if category=='automotive' and any(x in text for x in ('traction control','dsc','stability control')):
        lights=answer('dsc_lights')
        if lights=='brake':
            return step('stop','Check the braking hazard first','Stop driving if braking is abnormal. Arrange qualified inspection of the brake warning before further tests.','A red brake warning requires assessment before ordinary DSC troubleshooting.',[],state='stop')
        if not lights or lights=='unsure':
            return step('dsc_lights','Identify the DSC and brake indicators','While safely parked, identify which indicators stay on after startup: DSC OFF, the skidding-car / TCS warning, ABS, or the red brake warning. Record whether DSC OFF is steady or flashing and whether pressing its button changes it.','A disabled setting, initialization issue, and a system fault require different checks.')
        scanned=answer('dsc_scan')
        item=answers.get('item',{})
        rx8=isinstance(item,dict) and str(item.get('year'))=='2004' and str(item.get('make','')).lower()=='mazda' and str(item.get('model','')).lower().replace('-','').replace(' ','')=='rx8'
        note=''
        if rx8 and lights=='flashing':
            note=' For a 2004 Mazda RX-8, the owner manual (5-22) describes DSC initialization after battery disconnection when DSC OFF flashes and TCS/DSC illuminates. Check whether that exact condition applies with a qualified person; a steady light is not proof of that condition.'
        if not scanned or scanned in {'engine_only','help'}:
            return step('dsc_scan','Check the ABS / DSC system, not just engine codes','Use a scanner that explicitly supports this vehicle’s ABS / DSC module. Save the exact codes before clearing anything. If the button cannot clear a steady DSC OFF light, request system diagnosis; do not assume a transmission fault or a failed switch.'+note,'Driving normally does not establish that stability control is working. Burnouts are not a diagnostic test.',state='needs_help' if scanned else 'investigating')
        if answer('check_dsc_fault_confirm')=='confirmed':
            return step('repair_retest','Verify the DSC repair','After the confirmed fault is corrected, have the warning lights and normal DSC operation checked according to the manufacturer procedure. Do not use a burnout as a retest.','The recorded repair still needs an outcome check.')
        return step('check_dsc_fault_confirm','Use the warning and scan evidence to isolate the fault','Record the exact ABS / DSC codes, which lights stay on, and button response. Have the relevant manufacturer diagnostic procedure used to confirm the cause before replacing a sensor, switch, or module. A scan with no codes does not prove DSC operation.','The scan narrows the next test; it does not by itself prove a failed part.',[('confirmed','Diagnostic tests confirmed the fault'),('inconclusive','The cause is still uncertain'),('help','I need qualified help')],requires_detail=True)
    starting=category in {'automotive','motorcycle','equipment'} and any(x in text for x in ('start','crank','turn over','turns over'))
    if starting:
        behavior=answer('start_behavior')
        if not behavior:
            return step('start_behavior','First, separate the starting problem','When trying to start, does the engine turn over? Use what you already observed; do not repeat start attempts on unsafe equipment.','No-crank and crank-no-start require different tests.')
        if behavior=='unsure':
            return step('start_behavior','Identify the starting behavior safely','Ask a technician to distinguish no-crank from crank-no-start. Take your symptom description and item details; do not bypass an interlock or expose moving parts.','The next test depends on an observation we do not yet have.',CHOICES['start_behavior'],state='needs_help')
        if behavior in {'no_crank','slow_crank'}:
            battery=answer('battery_test')
            if not battery:
                return step('battery_test','Establish battery starting capacity','Have the battery charged and load- or conductance-tested using the correct battery specifications. A resting-voltage reading alone is not a passed starting-capacity test.','Battery capacity must be established before condemning the starter.')
            if battery=='untested':
                return step('battery_test','Get the missing battery test','Request a battery capacity test before buying a battery or starter. Save the measured result here when available.','The current evidence cannot distinguish a weak battery from a power-delivery fault.',CHOICES['battery_test'],state='needs_help')
            if battery=='failed':
                return step('repair_retest','A failed battery test is reported','Have the confirmed battery fault corrected using the correct battery specification. Check the charging system and cause of discharge, then retest the original starting complaint.','Replacement is supported by the reported test failure, not by clicking alone.')
            connection=answer('connection_test')
            if not connection:
                return step('connection_test','Battery passed: test power delivery next','Have a qualified person measure positive-cable and ground-path voltage drop during a safe start attempt against the manufacturer’s specifications. Do not bridge terminals or bypass safety switches.','A good battery can still be prevented from delivering power by a cable or ground fault.')
            if connection=='fault':
                return step('repair_retest','A connection fault is reported','Correct the cable or ground fault demonstrated by the test, then repeat the original starting test safely.','The reported measurement gives a targeted repair path.')
            if connection=='help':
                return step('connection_test','Get a starting-circuit test','Take the passed battery test and original complaint to a qualified technician. Request cable/ground voltage-drop tests before starter replacement.','Your evidence narrows what needs testing; it does not yet prove a failed starter.',CHOICES['connection_test'],state='needs_help')
            starter=answer('starter_test')
            if not starter:
                return step('starter_test','Power delivery passed: isolate the command or starter','A qualified technician should test the start command, relay, starter power and ground, and mechanical resistance using the exact service procedure.','Passed battery/cable tests narrow the fault but do not prove starter failure.')
            if starter in {'control_fault','starter_fault'}:
                return step('repair_retest','A starting-circuit fault is reported','Correct the specific fault confirmed by the technician’s tests, then retest the original starting complaint safely.','Repair follows the reported fault isolation rather than a parts guess.')
            return step('starter_test','Further fault isolation is needed','Take the saved checks to a qualified technician. Do not replace the starter without isolating the fault.','The current results are inconclusive.',CHOICES['starter_test'],state='needs_help')
    # For other symptoms, move through the current checks with recorded observations.
    for check in causes[0].checks:
        q=('project_' if category=='diy' else 'check_')+sha256(check.encode()).hexdigest()[:12]
        selected=answer(q)
        if selected=='help':
            return step(q,'Get help with the next check',check+' Share your original description and completed checks with a qualified person.','The missing test prevents a defensible conclusion.',[('observed','I observed a problem'),('clear','Check completed; no fault observed'),('help','I cannot test this safely')],state='needs_help',requires_detail=True)
        if selected=='observed':
            if category=='diy':
                return step(q,'Resolve the blocked project step','Review the recorded obstacle with the relevant building instructions or a qualified person before proceeding.','A blocked step should be resolved before dependent work continues.',[('clear','Completed'),('observed','Blocked / needs correction'),('help','I need help')],state='needs_help',requires_detail=True)
            confirmation=q+'_confirm'
            if answer(confirmation)=='confirmed':
                return step('repair_retest','A fault-confirmation test is reported','Correct only the component or circuit confirmed by your tests, following the exact manufacturer’s repair procedure. Then retest the original complaint safely.','The reported test supports a targeted repair; a retest still needs to establish the outcome.')
            if answer(confirmation) in {'help','inconclusive'}:
                return step(confirmation,'The finding has not established the cause','Take the original complaint and recorded observations to a qualified technician for model-specific fault isolation before replacing parts.','An abnormal observation alone does not identify the root cause.',[('confirmed','Diagnostic tests confirmed the fault'),('inconclusive','The cause is still uncertain'),('help','I need qualified help')],state='needs_help',requires_detail=True)
            return step(confirmation,'Confirm what the finding means','Use the manufacturer’s diagnostic procedure or a qualified technician to establish whether your recorded finding caused the original symptom. Record the confirming test and result.','Finding something abnormal is useful evidence; it does not by itself prove the fault.',[('confirmed','Diagnostic tests confirmed the fault'),('inconclusive','The cause is still uncertain'),('help','I need qualified help')],requires_detail=True)
        if selected=='clear': continue
        choices=[('clear','Completed'),('observed','Blocked / needs correction'),('help','I need help')] if category=='diy' else [('observed','I observed a problem'),('clear','Check completed; no fault observed'),('help','I cannot test this safely')]
        return step(q,'Your next project step' if category=='diy' else 'Your next check',check,causes[0].why,choices,requires_detail=True)
    if category=='diy':
        return step('project_verify','Verify the finished project','Check the original goal and safety requirements before use. Is the project complete and safe?','Completing steps and achieving the intended outcome are separate.')
    return step('handoff','The current checks did not isolate the fault','Take the recorded checks and observations to a qualified technician. Ask for model-specific fault isolation before buying parts.','No fault observed during a check is not proof that every component works.',[],state='needs_help')
