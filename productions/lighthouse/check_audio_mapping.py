"""Cross-correlate decoded source speech against mapped master segments.
This measures audio placement, not mouth motion or subjective voice quality.
"""
import json,subprocess
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];P=R/'videos/lighthouse';W=P/'work'
def decode(path):
    r=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-vn','-ac','1','-ar','16000','-f','f32le','-'],capture_output=True,check=True)
    return np.frombuffer(r.stdout,dtype='<f4').astype(np.float64)
def main():
    m=json.loads((W/'render-manifest.json').read_text());master=decode(m['master']);rows=[]
    for s in m['segments']:
        original=decode(s['source']);a=round(s['source_in_sample']/3);b=round(s['output_in_sample']/3);n=min(round((s['output_out_sample']-s['output_in_sample'])/3),len(original)-a,len(master)-b)
        x=original[a:a+n];y=master[b:b+n];x=x-x.mean();y=y-y.mean();size=1<<(2*n-1).bit_length()
        cc=np.fft.irfft(np.fft.rfft(y,size)*np.conj(np.fft.rfft(x,size)),size);limit=1600
        scores=np.concatenate([cc[-limit:],cc[:limit+1]]);lag=int(np.argmax(scores))-limit
        similarity=float(np.dot(x,y)/(np.linalg.norm(x)*np.linalg.norm(y)))
        rows.append({'clip':s['clip_id'],'best_lag_samples_16k':lag,'best_lag_ms':lag/16,'zero_lag_correlation':similarity})
        assert abs(lag)<=16,(s['clip_id'],lag)
        assert similarity>.95,(s['clip_id'],similarity)
    report={'measurement':'Decoded source/master audio alignment, within +/-100 ms search; <=1 ms lag and >0.95 correlation required. Not physical lip sync or listening acceptance.','segments':rows}
    (W/'audio-mapping-check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
