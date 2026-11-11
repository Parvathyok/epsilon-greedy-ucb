"""Export the report with an explicitly selected LibreOffice executable."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--office',required=True,help='Absolute path to the LibreOffice soffice executable')
args=parser.parse_args()
office=Path(args.office).expanduser().resolve()
if not office.is_file():parser.error('The selected LibreOffice executable does not exist.')
source=ROOT/'reports/Parvathy_OK_Epsilon_Greedy_and_UCB_Report.docx'
with tempfile.TemporaryDirectory(prefix='bandit-pdf-') as temporary:
    temp=Path(temporary);profile=temp/'profile';out=temp/'out';out.mkdir()
    result=subprocess.run([str(office),f'-env:UserInstallation={profile.as_uri()}',
        '--headless','--convert-to','pdf','--outdir',str(out),str(source)],capture_output=True,text=True,check=False)
    pdf=out/(source.stem+'.pdf')
    if result.returncode or not pdf.is_file():raise RuntimeError(result.stdout+'\n'+result.stderr)
    target=source.with_suffix('.pdf');shutil.copy2(pdf,target);print(target)
