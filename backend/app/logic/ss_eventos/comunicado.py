from dataclasses import dataclass
from uuid import UUID,uuid4
from datetime import datetime

from utils.utils import utc_now_datetime

@dataclass
class Comunicado:
    id: UUID = uuid4()
    titulo : str = ""
    data : datetime = utc_now_datetime()
    corpo : str = ""