"""Prioritize explicit immediate hazards over ordinary troubleshooting."""
import re


def urgent_hazard(symptom, answers):
    findings=answers.get('findings',[])
    notes=[symptom]+([x for x in findings if isinstance(x,str)] if isinstance(findings,list) else [])
    for note in notes:
        text=note.lower()
        for phrase in ('gas leak','smell gas','smell of gas','fuel leak','carbon monoxide alarm','outlet sparking','sparking outlet','smoke from outlet','brakes failed','brake pedal goes to the floor','no brakes'):
            for match in re.finditer(re.escape(phrase),text):
                prefix=text[max(0,match.start()-18):match.start()]
                if phrase!='no brakes' and re.search(r'\b(no|not|without)\s+(?:a |any )?$',prefix):
                    continue
                return {
                    'title':'Immediate hazard — stop use and get qualified help',
                    'confidence':1.0,
                    'why':'Your description reports an immediate fuel, gas, electrical, or braking hazard. Ordinary repair steps should wait until it is made safe.',
                    'checks':['Stop operating the equipment or driving the vehicle. Keep other people away from the hazard.','For a suspected gas leak, leave the area without operating electrical switches or creating sparks. Contact the gas utility or emergency services from a safe location.','For active smoke, fire, a carbon monoxide alarm, or immediate danger, leave the area and contact emergency services.'],
                    'repair':['Have a qualified professional make the equipment safe and identify the fault before reuse. Do not test by driving, bypassing safety controls, or energizing damaged equipment.'],
                    'safety':'stop'
                }
    return None
