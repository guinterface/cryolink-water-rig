"""Record source identity and environment without modifying the installed FSW."""
import hashlib
import json
import os
from pathlib import Path
import platform
import time

root=Path(__file__).resolve().parents[1]
fsw=Path('cryolink/fsw/src/cryolink_fsw/cryolink_fsw')
files=[p for d in ['esp32','rig_bridge','launch','tests','scripts'] for p in (root/d).rglob('*')
       if p.is_file() and p.suffix in ('.py','.h','.ino','.sh','.yaml')]
files += [root/n for n in ['README.md','setup.py','setup.cfg','package.xml']]
manifest={'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'python':platform.python_version(),
          'ros_distro':os.getenv('ROS_DISTRO'),'ros_domain_id':os.getenv('ROS_DOMAIN_ID'),
          'use_sim_time':False,'hardware_tested':False,
          'source_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
          'fsw_read_only_sources_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in fsw.glob('*.py')}}
(root/'logs/build_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
