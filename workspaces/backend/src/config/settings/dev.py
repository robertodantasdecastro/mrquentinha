from .base import *  # noqa: F403
from .base import env

DEBUG = env.bool("DEBUG", default=True)
