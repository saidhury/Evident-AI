import os
import sys

root_dir = os.path.dirname(os.path.dirname(__file__))
src_dir = os.path.join(root_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from traceable_ai_compliance_agent.api import app
