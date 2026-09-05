"""Original deterministic score, procedural cue catalog, ducked mix and stems."""
import array,json,math,subprocess,sys,wave,os
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from tools.providers.sfx_procedural import synthesize
from tools.mix_music import mix_one
from tools.make_stems import build_sfx,build_music
from tools import make_stems
P=R/'videos/lighthouse';A=R/'media/projects/lighthouse';O=P/'output';W=P/'work'
def run(args):subprocess.run([str(x) for x in args],cwd=R,check=True)
def main():
    make_stems.SCRATCH=str(W/'stems')
    cue=json.loads((W/'story-cues.json').read_text());dur=cue['output_duration_s'];sr=48000
    # A quiet four-chord miniature. Original notes/voicing; no inherited music clip.
    chords=[[146.832,174.614,220],[130.813,174.614,220],[130.813,164.814,195.998],[130.813,164.814,261.626]]
    samples=array.array('h')
    for i in range(round((dur+2)*sr)):
        t=i/sr;index=min(3,int(t/(dur/4)));notes=chords[index]
        # Adjacent chords fade through silence to avoid discontinuous oscillators.
        local=t-index*dur/4;env=min(1,max(0,local)/1.2,max(0,(dur/4-local))/1.2)
        pad=sum(math.sin(2*math.pi*n*t) for n in notes)/3
        bell=math.sin(2*math.pi*notes[int(t/1.5)%3]*2*t)*math.exp(-(t%1.5)*3)
        val=round(32767*(.07*pad*env+.035*bell)*min(1,t/1.5,max(0,dur-t)/2))
        samples.extend([val,val])
    score=A/'original-score.wav'
    with wave.open(str(score),'wb') as f:f.setparams((2,2,sr,0,'NONE',''));f.writeframes(samples.tobytes())
    clips=[]
    for kind,length in [('click',.12),('pop',.2),('tone',.35)]:
        out=synthesize(kind,A/(kind+'.wav'),length,seed=7);clips.append({'id':kind,'file':str(out),'source':'procedural original','duration_s':length})
    cat=W/'sfx-catalog.json';cat.write_text(json.dumps({'clips':clips},indent=2))
    events=[{'sfx_id':'click','at_s':cue['inspect_connection'],'gain_db':-17,'cue':'Inspect connection'},
            {'sfx_id':'pop','at_s':cue['repair']+cue['repair_click_local'],'gain_db':-13,'cue':'Cable connection closes'},
            {'sfx_id':'tone','at_s':cue['home']+.15,'gain_db':-22,'cue':'Beacon returns'}]
    plan={'time_basis':'final output seconds including insert','catalog':str(cat),'render':{'preview':str(O/'composited.mp4'),'out':str(O/'with-sfx.mp4'),'end_s':dur,'duck':True},'stem':{'out':str(O/'sfx-track.wav'),'duration_s':dur,'sample_rate':sr,'channels':2},'events':events}
    (W/'sfx-plan.json').write_text(json.dumps(plan,indent=2))
    run([R/'.venv/bin/python',R/'tools/mix_sfx.py',W/'sfx-plan.json'])
    mix_one(str(O/'with-sfx.mp4'),str(score),str(O/'mixed.mp4'),-5,9,1.5,dur)
    # Two-pass measured loudness normalization, preserving the finished picture.
    cmd=['ffmpeg','-hide_banner','-i',str(O/'mixed.mp4'),'-af','loudnorm=I=-18:TP=-1.5:LRA=9:print_format=json','-f','null','-']
    scan=subprocess.run(cmd,capture_output=True,text=True,check=True);report=json.JSONDecoder().raw_decode(scan.stderr[scan.stderr.rfind('{'):])[0];(W/'loudness-input.json').write_text(json.dumps(report,indent=2))
    filt=f"loudnorm=I=-18:TP=-1.5:LRA=9:measured_I={report['input_i']}:measured_TP={report['input_tp']}:measured_LRA={report['input_lra']}:measured_thresh={report['input_thresh']}:offset={report['target_offset']}:linear=true:print_format=json"
    run(['ffmpeg','-y','-v','error','-i',O/'mixed.mp4','-map','0:v','-map','0:a','-c:v','copy','-af',filt,'-ar','48000','-c:a','aac','-b:a','256k','-movflags','+faststart',O/'delivery-staged.mp4'])
    check=json.loads(subprocess.run(['ffprobe','-v','error','-show_format','-of','json',str(O/'delivery-staged.mp4')],capture_output=True,text=True,check=True).stdout)
    assert abs(float(check['format']['duration'])-dur)<.05
    os.replace(O/'delivery-staged.mp4',O/'The Little Lighthouse.mp4')
    build_sfx(str(W/'sfx-plan.json'))
    # Extract from baked master: its silence includes the insert, unlike pre-insert master.
    run(['ffmpeg','-y','-v','error','-i',O/'composited.mp4','-vn','-af',f'aresample=48000,apad,atrim=end_sample={round(dur*48000)}','-ar','48000','-ac','2','-c:a','pcm_s24le',O/'voice-track.wav'])
    mcat=W/'music-catalog.json';mcat.write_text(json.dumps({'clips':[{'id':'lighthouse-original','file':str(score),'source':'original deterministic composition','license':'Original project recipe; no external recording used'}]},indent=2))
    # Match exactly to source RMS, then apply the mix bed gain; preserve the unducked stem.
    rms=math.sqrt(sum((x/32768)**2 for x in samples)/len(samples));db=20*math.log10(rms)
    mplan={'catalog':str(mcat),'out':str(O/'music-track.wav'),'duration_s':dur,'sample_rate':sr,'channels':2,'crossfade_s':.2,'loop_crossfade_s':.2,'reference_rms_db':db,'fade_in_s':1.5,'fade_out_s':1.5,'beds':{'lighthouse-original':{'body_in':0,'body_out':dur+1,'body_rms_db':db}},'sections':[{'n':1,'bed':'lighthouse-original','start':0,'end':dur,'gain_db':-5}]}
    (W/'music-plan.json').write_text(json.dumps(mplan,indent=2));build_music(str(W/'music-plan.json'))
if __name__=='__main__':main()
