import sqlalchemy as sa
from data.db_session import SqlAlchemyBase


class Favorite(SqlAlchemyBase):
    __tablename__ = 'Favorite'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    user = sa.Column(sa.String, unique=True)
    videos = sa.Column(sa.String, nullable=True)
