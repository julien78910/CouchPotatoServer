from couchpotato.core.logger import CPLog
from couchpotato.core.media._base.providers.nzb.uptobox import Base
from couchpotato.core.media.movie.providers.base import MovieProvider

log = CPLog(__name__)

autoload = 'uptobox'


class uptobox(MovieProvider, Base):
    pass
