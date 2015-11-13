from sqlalchemy import Column, Integer, Boolean, \
    DateTime, Table, ForeignKey, String
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()


# creating many-to-many mapping
commit_to_file = Table(
    'commit_to_file', Base.metadata,
    Column('commit_id', Integer, ForeignKey('commits.id')),
    Column('file_id', Integer, ForeignKey('files.id'))
    )


class Commit(Base):
    __tablename__ = 'commits'

    id = Column(Integer, primary_key=True)
    pushed_time = Column(DateTime)
    is_fix = Column(Boolean)
    filse = relationship(
        "File",
        secondary=commit_to_file,
        backref='commits'
        )


class File(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    path = Column(String, unique=True)


class DB():
    def __init__(self, eng):
        self.engine = create_engine(eng)

    def setup(self):
        Base.metadata.create_all(self.engine)
        DBSession = sessionmaker(bind=self.engine)
        self.session = DBSession()
        return self.session

    def teardown(self):
        self.session.close()
        Base.metadata.drop_all(self.engine)
